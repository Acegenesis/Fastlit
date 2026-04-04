"""Session runtime: holds per-connection state, executes scripts, produces patches."""

from __future__ import annotations

import copy
import json
import logging
import os
import threading
import time
import uuid
from typing import Any, cast

from fastlit.runtime.context import clear_current_session, set_current_session
from fastlit.runtime.diff import diff_trees
from fastlit.runtime.navigation_slug import slugify_page_token
from fastlit.runtime.page_discovery import DiscoveredPage, normalize_request_path, resolve_page, visible_pages
from fastlit.runtime.protocol import PatchOp, RenderFull, RenderPatch
from fastlit.runtime.script_runner import run_script
from fastlit.runtime.tree import UINode, UITree

logger = logging.getLogger("fastlit.session")


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


_PROGRESSIVE_RENDER_ENABLED = _env_flag("FASTLIT_PROGRESSIVE_RENDER", True)
_PROGRESSIVE_FIRST_SNAPSHOT_NODES = max(
    2, int(os.environ.get("FASTLIT_PROGRESSIVE_FIRST_SNAPSHOT_NODES", "3"))
)
_PROGRESSIVE_MIN_NODE_DELTA = max(
    1, int(os.environ.get("FASTLIT_PROGRESSIVE_MIN_NODE_DELTA", "6"))
)
_PROGRESSIVE_MIN_INTERVAL_SECONDS = max(
    0.0, float(os.environ.get("FASTLIT_PROGRESSIVE_MIN_INTERVAL_MS", "40")) / 1000.0
)
_PROGRESSIVE_MAX_EVENTS_PER_RUN = max(
    1, int(os.environ.get("FASTLIT_PROGRESSIVE_MAX_EVENTS_PER_RUN", "12"))
)


class SessionState(dict):
    """Dict-like object with attribute access, compatible with st.session_state.

    Thread-safety model: the script runner is the sole writer during execution.
    Only write operations acquire the lock; reads are lock-free during a run.
    This removes the per-operation RLock overhead from every dict access.
    """

    __slots__ = ("_write_lock",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._write_lock = threading.Lock()
        super().__init__()
        if args or kwargs:
            self.update(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
                f"st.session_state has no attribute '{name}'. "
                f"Did you forget to initialize it?"
            )

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        self[name] = value

    def __delattr__(self, name: str) -> None:
        if name.startswith("_"):
            object.__delattr__(self, name)
            return
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)

    # --- write ops: acquire coarse lock ---

    def __setitem__(self, key: Any, value: Any) -> None:
        with self._write_lock:
            super().__setitem__(key, value)

    def __delitem__(self, key: Any) -> None:
        with self._write_lock:
            super().__delitem__(key)

    def clear(self) -> None:
        with self._write_lock:
            super().clear()

    def pop(self, key: Any, *args: Any) -> Any:
        with self._write_lock:
            return super().pop(key, *args)

    def update(self, *args: Any, **kwargs: Any) -> None:
        with self._write_lock:
            super().update(*args, **kwargs)

    def setdefault(self, key: Any, default: Any = None) -> Any:
        with self._write_lock:
            return super().setdefault(key, default)

    # --- read ops: lock-free ---

    def copy(self) -> dict[str, Any]:
        return dict(super().items())

    def __deepcopy__(self, memo: dict[int, Any]) -> "SessionState":
        return SessionState(copy.deepcopy(dict(super().items()), memo))

    def __reduce__(self):
        return (SessionState, (dict(super().items()),))

    def __repr__(self) -> str:
        return f"SessionState({dict(super().items())!r})"


class Session:
    """A single user session, tied to one WebSocket connection."""

    _MAX_RERUNS = 5  # safety limit to prevent infinite rerun loops
    _FULL_RERUN_SENTINEL = object()

    def __init__(self, script_path: str) -> None:
        self.session_id: str = uuid.uuid4().hex
        self.script_path: str = script_path
        self.entry_script_path: str = script_path
        self.widget_store: dict[str, Any] = {}
        self.session_state: SessionState = SessionState()
        self.query_params: dict[str, str] = {}
        self.current_path: str = ""
        self.route_path: str = ""
        self.route_params: dict[str, Any] = {}
        self.route_guard_failure: str | None = None
        self.layout_stack: list[str] = []
        self._pending_browser_redirect: str | None = None
        self.current_tree: UITree | None = None
        self._previous_tree: UITree | None = None
        self._previous_tree_index: dict[str, UINode] | None = None
        self._committed_tree_bytes: int = 0
        self.rev: int = 0
        # Per-run, per-location counter for generating stable IDs when
        # the same line is hit multiple times (e.g. in a loop).
        self._id_counters: dict[str, int] = {}
        # Fragment support.
        self._fragment_registry: dict[str, tuple] = {}
        self._fragment_subtrees: dict[str, UINode] = {}
        self._widget_to_fragment: dict[str, str] = {}
        self._current_fragment_id: str | None = None
        self._deferred_fragment_ids: list[str] = []
        self._deferred_fragment_epoch: int = 0
        # Deferred streaming: write_stream() registers (node_id, iterator) here;
        # the WS handler consumes them after sending each patch.
        self._deferred_streams: list[tuple[str, Any]] = []
        # Per-fragment auto-refresh intervals (seconds).  NOT cleared each run
        # so the WS handler can sync asyncio timers across full runs.
        self._fragment_run_every: dict[str, float] = {}
        # Runtime events emitted from script thread (e.g. spinner enter/exit).
        self._runtime_events: list[dict[str, Any]] = []
        self._runtime_events_lock = threading.Lock()
        self._progressive_render_enabled = False
        self._progressive_run_token = 0
        self._progressive_last_emit_at = 0.0
        self._progressive_last_emit_nodes = 0
        self._progressive_events_emitted = 0
        self._current_tree_node_count = 0
        # Multi-page metadata registered by st.navigation([...]).
        self._page_nav_id: str | None = None
        self._page_labels: list[str] = []
        self._page_url_paths: list[str] = []
        self._page_scripts: dict[int, str] = {}
        self._all_discovered_pages: list[DiscoveredPage] = []
        self._page_default_index: int = 0
        self._inline_page_rendered: bool = False
        self._inline_page_script_path: str | None = None
        self._inline_rendered_scripts: set[str] = set()
        self._route_chain: tuple[str, ...] = ()
        self._route_cursor: int = -1
        self._route_outlet_stack: list[bool] = []
        # OIDC claims attached by the WS handler from the session cookie.
        self.user_claims: dict = {}
        # Widgets that should force a full tree render after an event.
        # Used for cases where incremental patching can be inconsistent with
        # highly interactive client-side views.
        self._force_full_render_widget_ids: set[str] = set()

    @staticmethod
    def _estimate_json_bytes(value: Any) -> int:
        try:
            return len(
                json.dumps(
                    value,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    default=str,
                ).encode("utf-8")
            )
        except Exception:
            return 0

    @classmethod
    def _estimate_tree_bytes(cls, tree: UITree | None) -> int:
        if tree is None:
            return 0
        return cls._estimate_json_bytes(tree.to_dict())

    def committed_tree_bytes(self) -> int:
        """Return the last known serialized size of the committed tree."""
        return self._committed_tree_bytes

    def _refresh_committed_tree_bytes(self) -> None:
        self._committed_tree_bytes = self._estimate_tree_bytes(self._previous_tree)

    def snapshot_state(self) -> dict[str, Any]:
        """Capture a rollback-safe snapshot of the committed session state.

        Uses shallow copies where values are effectively immutable during a run
        (widget values, OIDC claims, route params, discovered pages).
        Deep-copies only structures the script can mutate in-place.
        """
        return {
            "script_path": self.script_path,
            "entry_script_path": self.entry_script_path,
            # widget_store values are Python scalars/lists set by widgets —
            # shallow-copy the dict; individual values are replaced, not mutated.
            "widget_store": dict(self.widget_store),
            # session_state values may be mutable objects; copy one level deep.
            "session_state": {k: copy.copy(v) for k, v in self.session_state.items()},
            "query_params": dict(self.query_params),
            "current_path": self.current_path,
            "route_path": self.route_path,
            # route_params is a simple str→str/int dict from URL parsing.
            "route_params": dict(self.route_params),
            "route_guard_failure": self.route_guard_failure,
            "layout_stack": list(self.layout_stack),
            "previous_tree": self._previous_tree.snapshot_dict()
            if self._previous_tree is not None
            else None,
            "fragment_subtrees": {
                fragment_id: node.snapshot_dict()
                for fragment_id, node in self._fragment_subtrees.items()
            },
            "widget_to_fragment": dict(self._widget_to_fragment),
            "fragment_run_every": dict(self._fragment_run_every),
            "deferred_fragment_ids": list(self._deferred_fragment_ids),
            "deferred_fragment_epoch": self._deferred_fragment_epoch,
            "page_nav_id": self._page_nav_id,
            "page_labels": list(self._page_labels),
            "page_url_paths": list(self._page_url_paths),
            "page_scripts": dict(self._page_scripts),
            # _all_discovered_pages are frozen DiscoveredPage dataclasses — list copy suffices.
            "all_discovered_pages": list(self._all_discovered_pages),
            "page_default_index": self._page_default_index,
            # user_claims come from a JWT and are immutable for the session lifetime.
            "user_claims": dict(self.user_claims),
            "rev": self.rev,
            "force_full_render_widget_ids": set(self._force_full_render_widget_ids),
            "current_tree": self.current_tree.snapshot_dict()
            if self.current_tree is not None
            else None,
        }

    def restore_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Restore a previously captured snapshot."""
        self.script_path = snapshot["script_path"]
        self.entry_script_path = snapshot["entry_script_path"]
        self.widget_store = copy.deepcopy(snapshot["widget_store"])
        self.session_state = SessionState(snapshot["session_state"])
        self.query_params = dict(snapshot["query_params"])
        self.current_path = snapshot["current_path"]
        self.route_path = snapshot["route_path"]
        self.route_params = copy.deepcopy(snapshot["route_params"])
        self.route_guard_failure = snapshot["route_guard_failure"]
        self.layout_stack = list(snapshot["layout_stack"])
        previous_tree = snapshot.get("previous_tree")
        self._previous_tree = UITree.from_dict(previous_tree) if previous_tree else None
        self._previous_tree_index = (
            self._previous_tree.build_index() if self._previous_tree is not None else None
        )
        self._fragment_subtrees = {
            fragment_id: UINode.from_dict(node_dict)
            for fragment_id, node_dict in snapshot.get("fragment_subtrees", {}).items()
        }
        self._widget_to_fragment = dict(snapshot.get("widget_to_fragment", {}))
        self._fragment_run_every = dict(snapshot.get("fragment_run_every", {}))
        self._deferred_fragment_ids = list(snapshot.get("deferred_fragment_ids", []))
        self._deferred_fragment_epoch = int(snapshot.get("deferred_fragment_epoch", 0))
        self._page_nav_id = snapshot.get("page_nav_id")
        self._page_labels = list(snapshot.get("page_labels", []))
        self._page_url_paths = list(snapshot.get("page_url_paths", []))
        self._page_scripts = dict(snapshot.get("page_scripts", {}))
        self._all_discovered_pages = copy.deepcopy(snapshot.get("all_discovered_pages", []))
        self._page_default_index = int(snapshot.get("page_default_index", 0))
        self.user_claims = copy.deepcopy(snapshot.get("user_claims", {}))
        self.rev = int(snapshot.get("rev", 0))
        self._force_full_render_widget_ids = set(
            snapshot.get("force_full_render_widget_ids", set())
        )
        current_tree = snapshot.get("current_tree")
        self.current_tree = UITree.from_dict(current_tree) if current_tree else None
        self._refresh_committed_tree_bytes()

    def _commit_render_tree(self, tree: UITree) -> None:
        """Atomically publish a successful run as the new committed tree."""
        self._previous_tree = tree
        self._previous_tree_index = tree.build_index()
        self._refresh_committed_tree_bytes()

    def _commit_render_result(
        self,
        tree: UITree,
        *,
        force_full_render: bool,
    ) -> RenderFull | RenderPatch:
        next_rev = self.rev + 1
        if self._previous_tree is None or force_full_render:
            self.rev = next_rev
            self._commit_render_tree(tree)
            return RenderFull(rev=self.rev, tree=tree.to_dict())

        self._adopt_shared_subtrees(self._previous_tree.root, tree.root)
        ops = diff_trees(self._previous_tree.root, tree.root)
        self.rev = next_rev
        self._commit_render_tree(tree)
        return RenderPatch(rev=self.rev, ops=ops or [])

    def register_navigation_pages(
        self,
        *,
        nav_id: str,
        labels: list[str],
        url_paths: list[str],
        page_scripts: dict[int, str],
        default_index: int = 0,
        discovered_pages: list[DiscoveredPage] | None = None,
    ) -> None:
        """Persist navigation metadata for switch_page and page-script routing."""
        self._page_nav_id = nav_id
        self._page_labels = list(labels)
        self._page_url_paths = list(url_paths)
        self._page_scripts = dict(page_scripts)
        self._page_default_index = int(default_index)
        self._all_discovered_pages = list(discovered_pages or [])

    @staticmethod
    def _normalize_page_token(value: str) -> str:
        return slugify_page_token(value)

    def _selected_page_index(self) -> int:
        """Return the current navigation index, falling back to the default page."""
        nav_id = self._page_nav_id
        if nav_id is None:
            return self._page_default_index
        selected = self.widget_store.get(nav_id)
        if isinstance(selected, int) and selected >= 0:
            return selected
        return self._page_default_index

    def _selected_page_script(self) -> str | None:
        """Return the currently selected page script path, if any."""
        return self._page_scripts.get(self._selected_page_index())

    def _set_route_context(
        self,
        *,
        route_path: str,
        params: dict[str, Any] | None = None,
        guard_failure: str | None = None,
        layout_stack: list[str] | None = None,
    ) -> None:
        """Persist resolved route context for st.context."""
        self.route_path = route_path
        self.route_params = dict(params or {})
        self.route_guard_failure = guard_failure
        self.layout_stack = list(layout_stack or [])

    def set_current_path(self, pathname: str | None) -> None:
        """Persist the browser pathname for route resolution."""
        self.current_path = normalize_request_path(pathname)

    def consume_pending_browser_redirect(self) -> str | None:
        """Return and clear a pending browser redirect, if any."""
        target = self._pending_browser_redirect
        self._pending_browser_redirect = None
        return target

    def _switch_to_page_index(
        self, idx: int, nav_id: str | None, *, switch_script: bool = True
    ) -> None:
        """Apply selected page index and switch script when required."""
        if nav_id:
            self.widget_store[nav_id] = idx

        if not switch_script:
            return

        new_script = self._page_scripts.get(idx)
        if not new_script or new_script == self.script_path:
            return

        self.script_path = new_script
        # Reset UI tree/widget snapshots when changing script file.
        self._previous_tree = None
        self._previous_tree_index = None
        self._committed_tree_bytes = 0
        self._fragment_subtrees.clear()
        self._fragment_registry.clear()
        self._widget_to_fragment.clear()

        nav_value = idx if nav_id else None
        self.widget_store.clear()
        if nav_id is not None and nav_value is not None:
            self.widget_store[nav_id] = nav_value

    def _sync_script_path_from_navigation(self) -> None:
        """Before running a script, route to the selected Page script if needed."""
        if self.script_path == self.entry_script_path:
            return
        nav_id = self._page_nav_id
        if not nav_id or not self._page_scripts:
            return
        self._switch_to_page_index(self._selected_page_index(), nav_id)

    def run_inline_page_script(self, script_path: str, *, root_level: bool = False) -> None:
        """Render a page script inline inside the current entry-script layout."""
        previous_inline_script = self._inline_page_script_path
        previous_stack: list[UINode] | None = None
        self._inline_page_rendered = True
        self._inline_page_script_path = script_path
        self._inline_rendered_scripts.add(script_path)
        if root_level and self.current_tree is not None:
            previous_stack = list(self.current_tree._container_stack)
            self.current_tree._container_stack = [self.current_tree.root]
        try:
            run_script(script_path, self)
        finally:
            if previous_stack is not None and self.current_tree is not None:
                self.current_tree._container_stack = previous_stack
            self._inline_page_script_path = previous_inline_script

    def run_route_chain(self, script_paths: list[str], *, root_level: bool = False) -> None:
        """Render a layout/page chain, supporting explicit or implicit outlets."""
        if not script_paths:
            return

        previous_chain = self._route_chain
        previous_cursor = self._route_cursor
        previous_stack = list(self._route_outlet_stack)
        previous_container_stack: list[UINode] | None = None

        self._route_chain = tuple(script_paths)
        self._route_cursor = -1
        self._route_outlet_stack = []

        if root_level and self.current_tree is not None:
            previous_container_stack = list(self.current_tree._container_stack)
            self.current_tree._container_stack = [self.current_tree.root]

        try:
            self._run_route_chain_step(0)
        finally:
            if previous_container_stack is not None and self.current_tree is not None:
                self.current_tree._container_stack = previous_container_stack
            self._route_chain = previous_chain
            self._route_cursor = previous_cursor
            self._route_outlet_stack = previous_stack

    def _run_route_chain_step(self, index: int) -> None:
        """Render one script in the current route chain."""
        if index < 0 or index >= len(self._route_chain):
            return

        previous_cursor = self._route_cursor
        self._route_cursor = index
        self._route_outlet_stack.append(False)
        try:
            self.run_inline_page_script(self._route_chain[index])
            if not self._route_outlet_stack[-1] and index + 1 < len(self._route_chain):
                self._run_route_chain_step(index + 1)
        finally:
            self._route_outlet_stack.pop()
            self._route_cursor = previous_cursor

    def run_page_outlet(self) -> None:
        """Render the next pending layout/page in the current route chain."""
        if not self._route_chain or not self._route_outlet_stack:
            return
        if self._route_outlet_stack[-1]:
            return
        self._route_outlet_stack[-1] = True
        next_index = self._route_cursor + 1
        if next_index < len(self._route_chain):
            self._run_route_chain_step(next_index)

    def run(
        self,
        *,
        force_full_render: bool = False,
        progressive: bool = False,
    ) -> RenderFull | RenderPatch:
        """Execute the script and return either a full render or a patch."""
        new_tree: UITree | None = None
        for _attempt in range(max(1, self._MAX_RERUNS)):
            self._pending_browser_redirect = None
            self._sync_script_path_from_navigation()
            self._deferred_streams.clear()
            self._deferred_fragment_ids = []
            self._deferred_fragment_epoch += 1
            self.clear_runtime_events()
            self._id_counters = {}
            self._fragment_registry.clear()
            self._widget_to_fragment.clear()
            self._current_fragment_id = None
            self._progressive_render_enabled = bool(
                progressive and _PROGRESSIVE_RENDER_ENABLED
            )
            self._progressive_run_token += 1
            self._progressive_last_emit_at = time.monotonic()
            self._progressive_last_emit_nodes = 0
            self._progressive_events_emitted = 0
            self._current_tree_node_count = 0
            self._inline_page_rendered = False
            self._inline_page_script_path = None
            self._inline_rendered_scripts.clear()
            self._route_chain = ()
            self._route_cursor = -1
            self._route_outlet_stack = []
            self._set_route_context(route_path="", params={}, guard_failure=None, layout_stack=[])

            new_tree = UITree(
                on_append=self._on_tree_node_appended
                if self._progressive_render_enabled
                else None
            )
            self.current_tree = new_tree
            script_error: Exception | None = None

            set_current_session(self)
            try:
                run_script(self.script_path, self)
            except RerunException:
                clear_current_session()
                continue
            except SwitchPageException as spe:
                clear_current_session()
                if self._handle_switch_page(spe.page_name):
                    new_tree = UITree()
                    self.current_tree = new_tree
                    break
                continue
            except _RequireLoginException:
                clear_current_session()
                if self._handle_switch_page("/auth/login"):
                    new_tree = UITree()
                    self.current_tree = new_tree
                    break
                continue
            except _StopException:
                pass
            except Exception as exc:  # noqa: BLE001
                script_error = exc
            finally:
                clear_current_session()

            if self.script_path == self.entry_script_path and not self._inline_page_rendered:
                selected_idx = self._selected_page_index()
                selected_script = self._selected_page_script()
                if (
                    selected_script is not None
                    and selected_script != self.script_path
                    and self._page_nav_id is not None
                ):
                    self._switch_to_page_index(selected_idx, self._page_nav_id)
                    continue

            self._prune_fragment_state()
            if self._progressive_render_enabled:
                # Progressive snapshots serialize the tree mid-run, which can leave
                # cached node dicts stale for the final render/diff.
                new_tree.invalidate_caches()
            if script_error:
                self._deferred_streams.clear()
                raise script_error
            return self._commit_render_result(
                new_tree,
                force_full_render=force_full_render,
            )

        # Exhausted reruns.
        if new_tree is None:
            new_tree = UITree()
        if self._progressive_render_enabled:
            new_tree.invalidate_caches()
        return self._commit_render_result(
            new_tree,
            force_full_render=force_full_render,
        )

    def register_deferred_fragment(self, fragment_id: str) -> None:
        """Queue a fragment for background hydration after the current full render."""
        self._deferred_fragment_ids.append(fragment_id)

    def get_deferred_fragment_snapshot(self) -> tuple[int, list[str]]:
        """Return the current deferred-fragment epoch and pending ids."""
        return self._deferred_fragment_epoch, list(self._deferred_fragment_ids)

    def _prune_fragment_state(self) -> None:
        """Drop fragment state for fragments not registered in the latest full run."""
        active_fragment_ids = set(self._fragment_registry)
        if not active_fragment_ids:
            self._fragment_subtrees.clear()
            self._fragment_run_every.clear()
            return

        for fragment_id in list(self._fragment_subtrees):
            if fragment_id not in active_fragment_ids:
                del self._fragment_subtrees[fragment_id]

        for fragment_id in list(self._fragment_run_every):
            if fragment_id not in active_fragment_ids:
                del self._fragment_run_every[fragment_id]

    def emit_runtime_event(self, event: dict[str, Any]) -> None:
        """Emit a runtime event from script execution (thread-safe)."""
        with self._runtime_events_lock:
            self._runtime_events.append(event)

    def drain_runtime_events(self) -> list[dict[str, Any]]:
        """Drain pending runtime events (thread-safe)."""
        with self._runtime_events_lock:
            if not self._runtime_events:
                return []
            events = self._runtime_events[:]
            self._runtime_events.clear()
            return events

    def clear_runtime_events(self) -> None:
        """Clear runtime event queue (thread-safe)."""
        with self._runtime_events_lock:
            self._runtime_events.clear()

    def _on_tree_node_appended(self, _node: UINode) -> None:
        """Track tree growth and emit throttled progressive snapshots."""
        self._current_tree_node_count += 1
        self._maybe_emit_progressive_snapshot()

    def _has_progressive_main_content(self) -> bool:
        """Return True once the root tree contains visible main-area content."""
        if self.current_tree is None:
            return False
        for child in self.current_tree.root.children:
            if child.type not in {"sidebar", "page_config", "sidebar_state"}:
                return True
        return False

    def _maybe_emit_progressive_snapshot(self) -> None:
        if not self._progressive_render_enabled or self.current_tree is None:
            return
        if self._progressive_events_emitted >= _PROGRESSIVE_MAX_EVENTS_PER_RUN:
            return
        if self._current_tree_node_count < _PROGRESSIVE_FIRST_SNAPSHOT_NODES:
            return
        if not self._has_progressive_main_content():
            return

        now = time.monotonic()
        node_delta = self._current_tree_node_count - self._progressive_last_emit_nodes
        if self._progressive_events_emitted > 0:
            if node_delta < _PROGRESSIVE_MIN_NODE_DELTA:
                return
            if (now - self._progressive_last_emit_at) < _PROGRESSIVE_MIN_INTERVAL_SECONDS:
                return

        snapshot = self.current_tree.snapshot_dict()
        self.emit_runtime_event(
            {
                "kind": "render_progress",
                "runToken": self._progressive_run_token,
                "path": f"/{self.current_path.lstrip('/')}" if self.current_path else "/",
                "tree": snapshot,
            }
        )
        self._progressive_last_emit_at = now
        self._progressive_last_emit_nodes = self._current_tree_node_count
        self._progressive_events_emitted += 1

    def coerce_widget_event_result(
        self,
        result: RenderFull | RenderPatch,
        event_ids: list[str] | tuple[str, ...],
    ) -> RenderFull | RenderPatch:
        """Promote patch results to full renders for force-full widgets."""
        if not any(
            event_id in self._force_full_render_widget_ids for event_id in event_ids
        ):
            return result
        if isinstance(result, RenderFull):
            return result
        if self._previous_tree is not None:
            return RenderFull(rev=result.rev, tree=self._previous_tree.to_dict())
        return result

    def handle_widget_event(self, widget_id: str, value: Any) -> RenderFull | RenderPatch:
        """Process a widget event and return the resulting render message."""
        self.widget_store[widget_id] = value
        return self.coerce_widget_event_result(self.run(), [widget_id])

    def run_fragment(self, fragment_id: str) -> RenderPatch | None:
        """Re-execute a single fragment and return a targeted patch."""
        result = self._run_fragment_internal(fragment_id)
        if result is None:
            return None
        if result is self._FULL_RERUN_SENTINEL:
            full_result = self.run()
            if isinstance(full_result, RenderPatch):
                return full_result
            return None

        self.rev += 1
        return RenderPatch(rev=self.rev, ops=cast(list[PatchOp], result))

    def run_fragments(
        self, fragment_ids: list[str]
    ) -> RenderFull | RenderPatch | None:
        """Re-execute multiple fragments and return one patch message."""
        unique_ids: list[str] = []
        seen: set[str] = set()
        for fragment_id in fragment_ids:
            if fragment_id in seen:
                continue
            seen.add(fragment_id)
            unique_ids.append(fragment_id)

        all_ops: list[PatchOp] = []
        for fragment_id in unique_ids:
            result = self._run_fragment_internal(fragment_id)
            if result is None:
                return None
            if result is self._FULL_RERUN_SENTINEL:
                return self.run()
            all_ops.extend(cast(list[PatchOp], result))

        self.rev += 1
        return RenderPatch(rev=self.rev, ops=all_ops)

    def _run_fragment_internal(
        self, fragment_id: str
    ) -> list[PatchOp] | object | None:
        if fragment_id not in self._fragment_registry:
            return None

        fn, args, kwargs = self._fragment_registry[fragment_id]
        old_subtree = self._fragment_subtrees.get(fragment_id)
        if old_subtree is None:
            return None

        container = UINode(type="fragment", id=fragment_id, props={})
        temp_tree = UITree()
        temp_tree.append(container)
        temp_tree.push_container(container)

        saved_tree = self.current_tree
        saved_frag_id = self._current_fragment_id
        saved_counters = self._id_counters

        self.current_tree = temp_tree
        self._current_fragment_id = fragment_id
        self._id_counters = {}
        set_current_session(self)

        do_full_rerun = False
        try:
            for _frag_attempt in range(max(1, self._MAX_RERUNS)):
                try:
                    fn(*args, **kwargs)
                    break
                except RerunException as rerun_exc:
                    if rerun_exc.scope == "fragment":
                        container.children.clear()
                        self._id_counters = {}
                        continue
                    do_full_rerun = True
                    break
            else:
                # Too many fragment-local reruns: degrade to full rerun.
                do_full_rerun = True
        except _StopException:
            pass
        except Exception:  # noqa: BLE001
            logger.exception("Unhandled exception while running fragment '%s'", fragment_id)
            raise
        finally:
            self.current_tree = saved_tree
            self._current_fragment_id = saved_frag_id
            self._id_counters = saved_counters
            clear_current_session()
            temp_tree.pop_container()

        if do_full_rerun:
            return self._FULL_RERUN_SENTINEL

        ops = diff_trees(old_subtree, container)
        self._fragment_subtrees[fragment_id] = container
        self._sync_fragment_in_tree(fragment_id, container)
        return ops

    def _sync_fragment_in_tree(self, fragment_id: str, new_container: UINode) -> None:
        """Sync previous tree so future diffs reflect this partial rerun."""
        if self._previous_tree is None:
            return

        if self._previous_tree_index is None:
            self._previous_tree_index = self._previous_tree.build_index()

        node = self._previous_tree_index.get(fragment_id)
        if node is not None:
            node.replace_props(dict(new_container.props))
            node.replace_children(list(new_container.children))
            self._previous_tree_index = self._previous_tree.build_index()
            self._refresh_committed_tree_bytes()

    def _handle_switch_page(self, page_name: str) -> bool:
        """Update navigation state or request a browser redirect."""
        target_path = normalize_request_path(page_name)
        target = self._normalize_page_token(page_name)
        raw_target = str(page_name).strip()

        # System endpoints such as auth/login are HTTP routes, not Fastlit pages.
        if raw_target.startswith("/") and target_path.startswith("auth/"):
            self._pending_browser_redirect = raw_target
            return True

        if self._all_discovered_pages:
            self.set_current_path(target_path)
            resolved = resolve_page(
                self._all_discovered_pages,
                target_path,
                user_claims=self.user_claims,
            )
            visible = visible_pages(self._all_discovered_pages)
            if resolved is not None and self._page_nav_id is not None:
                resolved_script = str(resolved.page.path.resolve())
                visible_idx = next(
                    (
                        idx
                        for idx, page in enumerate(visible)
                        if str(page.path.resolve()) == resolved_script
                    ),
                    -1,
                )
                self.widget_store[self._page_nav_id] = visible_idx
                self._set_route_context(
                    route_path=resolved.requested_path or resolved.page.url_path,
                    params=resolved.params,
                    guard_failure=resolved.guard_failure,
                    layout_stack=[str(path) for path in resolved.page.layout_paths],
                )
                return False

        # Preferred source: explicit metadata registered by st.navigation([...]).
        if self._page_labels:
            switch_script = (
                self.script_path != self.entry_script_path
                and self._inline_page_script_path is None
            )
            for idx, label in enumerate(self._page_labels):
                candidates = {self._normalize_page_token(label)}
                if idx < len(self._page_url_paths):
                    candidates.add(self._normalize_page_token(self._page_url_paths[idx]))
                if target in candidates:
                    self._switch_to_page_index(
                        idx,
                        self._page_nav_id,
                        switch_script=switch_script,
                    )
                    return False

        # Fallback: infer from previous tree props.
        if self._previous_tree is None:
            return False
        if self._previous_tree_index is None:
            self._previous_tree_index = self._previous_tree.build_index()

        nav_node = self._find_nav_node_in_index(self._previous_tree_index)
        if nav_node is None:
            return False

        pages = nav_node.props.get("pages", nav_node.props.get("options", []))
        url_paths = nav_node.props.get("urlPaths", [])
        for idx, page in enumerate(pages):
            candidates = {self._normalize_page_token(page)}
            if isinstance(url_paths, list) and idx < len(url_paths):
                candidates.add(self._normalize_page_token(url_paths[idx]))
            if target in candidates:
                self._switch_to_page_index(
                    idx,
                    nav_node.id,
                    switch_script=self.script_path != self.entry_script_path,
                )
                return False

        return False

    @staticmethod
    def _find_nav_node_in_index(index: dict[str, UINode]) -> UINode | None:
        """Find the navigation widget from an id->node index."""
        for node in index.values():
            if node.type in ("navigation", "radio"):
                if "pages" in node.props or "options" in node.props:
                    return node
        return None

    def next_id_for_location(self, location: str) -> int:
        """Return and increment the per-location counter for file:line key."""
        val = self._id_counters.get(location, 0)
        self._id_counters[location] = val + 1
        return val

    def _adopt_shared_subtrees(self, old: UINode, new: UINode) -> UINode:
        """Mutate `new` tree to reuse unchanged node objects from `old` tree."""
        if (
            old.id == new.id
            and old.type == new.type
            and old.subtree_hash() == new.subtree_hash()
        ):
            return old

        if not old.children or not new.children:
            return new

        old_by_id = {child.id: child for child in old.children}
        replaced_any = False
        new_children: list[UINode] = []
        for child in new.children:
            old_child = old_by_id.get(child.id)
            if old_child is None:
                new_children.append(child)
                continue
            adopted = self._adopt_shared_subtrees(old_child, child)
            if adopted is not child:
                replaced_any = True
            new_children.append(adopted)

        if replaced_any:
            new.replace_children(new_children)
        return new


class RerunException(Exception):
    """Raised by st.rerun() to interrupt script execution."""

    def __init__(self, scope: str = "full"):
        self.scope = scope
        super().__init__()


class StopException(Exception):
    """Raised by st.stop() to halt script execution."""


class SwitchPageException(Exception):
    """Raised by st.switch_page() to navigate to another page programmatically."""

    def __init__(self, page_name: str) -> None:
        self.page_name = page_name
        super().__init__(f"Switch to page: {page_name}")


class _RequireLoginException(Exception):
    """Raised by st.require_login() when the user is not authenticated.

    The session run loop catches this and redirects to ``/auth/login``.
    """


# Private alias used internally to avoid name clashes with `fastlit.__init__`
_StopException = StopException
