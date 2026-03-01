"""Session runtime: holds per-connection state, executes scripts, produces patches."""

from __future__ import annotations

import logging
import threading
import uuid
from typing import Any

from fastlit.runtime.context import clear_current_session, set_current_session
from fastlit.runtime.diff import diff_trees
from fastlit.runtime.navigation_slug import slugify_page_token
from fastlit.runtime.protocol import PatchOp, RenderFull, RenderPatch
from fastlit.runtime.script_runner import run_script
from fastlit.runtime.tree import UINode, UITree

logger = logging.getLogger("fastlit.session")


class SessionState(dict):
    """Dict-like object with attribute access, compatible with st.session_state."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
                f"st.session_state has no attribute '{name}'. "
                f"Did you forget to initialize it?"
            )

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)


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
        self.current_tree: UITree | None = None
        self._previous_tree: UITree | None = None
        self._previous_tree_index: dict[str, UINode] | None = None
        self.rev: int = 0
        # Per-run, per-location counter for generating stable IDs when
        # the same line is hit multiple times (e.g. in a loop).
        self._id_counters: dict[str, int] = {}
        # Fragment support.
        self._fragment_registry: dict[str, tuple] = {}
        self._fragment_subtrees: dict[str, UINode] = {}
        self._widget_to_fragment: dict[str, str] = {}
        self._current_fragment_id: str | None = None
        # Deferred streaming: write_stream() registers (node_id, iterator) here;
        # the WS handler consumes them after sending each patch.
        self._deferred_streams: list[tuple[str, Any]] = []
        # Per-fragment auto-refresh intervals (seconds).  NOT cleared each run
        # so the WS handler can sync asyncio timers across full runs.
        self._fragment_run_every: dict[str, float] = {}
        # Runtime events emitted from script thread (e.g. spinner enter/exit).
        self._runtime_events: list[dict[str, Any]] = []
        self._runtime_events_lock = threading.Lock()
        # Multi-page metadata registered by st.navigation([...]).
        self._page_nav_id: str | None = None
        self._page_labels: list[str] = []
        self._page_url_paths: list[str] = []
        self._page_scripts: dict[int, str] = {}
        self._page_default_index: int = 0
        self._inline_page_rendered: bool = False
        self._inline_page_script_path: str | None = None
        # OIDC claims attached by the WS handler from the session cookie.
        self.user_claims: dict = {}
        # Widgets that should force a full tree render after an event.
        # Used for cases where incremental patching can be inconsistent with
        # highly interactive client-side views.
        self._force_full_render_widget_ids: set[str] = set()

    def register_navigation_pages(
        self,
        *,
        nav_id: str,
        labels: list[str],
        url_paths: list[str],
        page_scripts: dict[int, str],
        default_index: int = 0,
    ) -> None:
        """Persist navigation metadata for switch_page and page-script routing."""
        self._page_nav_id = nav_id
        self._page_labels = list(labels)
        self._page_url_paths = list(url_paths)
        self._page_scripts = dict(page_scripts)
        self._page_default_index = int(default_index)

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

    def run_inline_page_script(self, script_path: str) -> None:
        """Render a page script inline inside the current entry-script layout."""
        previous_inline_script = self._inline_page_script_path
        self._inline_page_rendered = True
        self._inline_page_script_path = script_path
        try:
            run_script(script_path, self)
        finally:
            self._inline_page_script_path = previous_inline_script

    def run(self) -> RenderFull | RenderPatch:
        """Execute the script and return either a full render or a patch."""
        new_tree: UITree | None = None
        for _attempt in range(max(1, self._MAX_RERUNS)):
            self._sync_script_path_from_navigation()
            self._deferred_streams.clear()
            self.clear_runtime_events()
            self._id_counters = {}
            self._fragment_registry.clear()
            self._widget_to_fragment.clear()
            self._current_fragment_id = None
            self._inline_page_rendered = False
            self._inline_page_script_path = None

            new_tree = UITree()
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
                self._handle_switch_page(spe.page_name)
                continue
            except _RequireLoginException:
                clear_current_session()
                self._handle_switch_page("/auth/login")
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
            self.rev += 1
            if self._previous_tree is None:
                self._previous_tree = new_tree
                self._previous_tree_index = new_tree.build_index()
                if script_error:
                    self._deferred_streams.clear()
                    raise script_error
                return RenderFull(rev=self.rev, tree=new_tree.to_dict())

            # Reuse unchanged node objects across runs to reduce retained allocations.
            self._adopt_shared_subtrees(self._previous_tree.root, new_tree.root)
            ops = diff_trees(self._previous_tree.root, new_tree.root)
            self._previous_tree = new_tree
            self._previous_tree_index = new_tree.build_index()
            if script_error:
                self._deferred_streams.clear()
                raise script_error
            return RenderPatch(rev=self.rev, ops=ops or [])

        # Exhausted reruns.
        if new_tree is None:
            new_tree = UITree()
        self.rev += 1
        if self._previous_tree is None:
            self._previous_tree = new_tree
            self._previous_tree_index = new_tree.build_index()
            return RenderFull(rev=self.rev, tree=new_tree.to_dict())
        self._adopt_shared_subtrees(self._previous_tree.root, new_tree.root)
        ops = diff_trees(self._previous_tree.root, new_tree.root)
        self._previous_tree = new_tree
        self._previous_tree_index = new_tree.build_index()
        return RenderPatch(rev=self.rev, ops=ops or [])

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
            return self.run()

        self.rev += 1
        return RenderPatch(rev=self.rev, ops=result)

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
            all_ops.extend(result)

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
            node.children = new_container.children
            node.invalidate_caches()
            self._previous_tree.invalidate_caches()
            self._previous_tree_index = self._previous_tree.build_index()

    def _handle_switch_page(self, page_name: str) -> None:
        """Update widget store so the navigation widget selects the given page."""
        target = self._normalize_page_token(page_name)

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
                    return

        # Fallback: infer from previous tree props.
        if self._previous_tree is None:
            return
        if self._previous_tree_index is None:
            self._previous_tree_index = self._previous_tree.build_index()

        nav_node = self._find_nav_node_in_index(self._previous_tree_index)
        if nav_node is None:
            return

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
                return

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
            new.children = new_children
            new.invalidate_caches()
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
