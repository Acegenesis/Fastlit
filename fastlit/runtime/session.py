"""Session runtime: holds per-connection state, executes scripts, produces patches."""

from __future__ import annotations

import uuid
from typing import Any

from fastlit.runtime.context import set_current_session, clear_current_session
from fastlit.runtime.diff import diff_trees
from fastlit.runtime.protocol import PatchOp, RenderFull, RenderPatch
from fastlit.runtime.script_runner import run_script
from fastlit.runtime.tree import UITree


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

    def __init__(self, script_path: str) -> None:
        self.session_id: str = uuid.uuid4().hex
        self.script_path: str = script_path
        self.widget_store: dict[str, Any] = {}
        self.session_state: SessionState = SessionState()
        self.query_params: dict[str, str] = {}
        self.current_tree: UITree | None = None
        self._previous_tree: UITree | None = None
        self.rev: int = 0
        # Per-run, per-location counter for generating stable IDs when
        # the same line is hit multiple times (e.g. in a loop).
        # Key = "filename:lineno", value = count of hits so far.
        self._id_counters: dict[str, int] = {}

    _MAX_RERUNS = 5  # safety limit to prevent infinite rerun loops

    def run(self) -> RenderFull | RenderPatch:
        """Execute the script and return either a full render or a patch."""
        for attempt in range(self._MAX_RERUNS):
            self._id_counters = {}
            new_tree = UITree()
            self.current_tree = new_tree

            script_error: Exception | None = None
            set_current_session(self)
            try:
                run_script(self.script_path, self)
            except RerunException:
                # Script requested a rerun — discard partial tree and restart
                clear_current_session()
                continue
            except SwitchPageException as spe:
                # st.switch_page() — find the nav widget, update index, rerun
                clear_current_session()
                self._handle_switch_page(spe.page_name)
                continue
            except _StopException:
                # st.stop() — keep the tree built so far
                pass
            except Exception as exc:
                # Script error — sync _previous_tree with partial tree so
                # the next rerun diffs against a consistent state, then re-raise.
                script_error = exc
            finally:
                clear_current_session()

            # Produce result (even on error, sync tree state first)
            self.rev += 1

            if self._previous_tree is None:
                self._previous_tree = new_tree
                if script_error:
                    raise script_error
                return RenderFull(rev=self.rev, tree=new_tree.to_dict())
            else:
                ops = diff_trees(self._previous_tree.root, new_tree.root)
                self._previous_tree = new_tree
                if script_error:
                    raise script_error
                if ops:
                    return RenderPatch(rev=self.rev, ops=ops)
                else:
                    return RenderPatch(rev=self.rev, ops=[])

        # Exhausted reruns — return whatever we have
        self.rev += 1
        if self._previous_tree is None:
            self._previous_tree = new_tree
            return RenderFull(rev=self.rev, tree=new_tree.to_dict())
        ops = diff_trees(self._previous_tree.root, new_tree.root)
        self._previous_tree = new_tree
        return RenderPatch(rev=self.rev, ops=ops or [])

    def handle_widget_event(self, widget_id: str, value: Any) -> RenderFull | RenderPatch:
        """Process a widget event and return the resulting render message."""
        self.widget_store[widget_id] = value
        return self.run()

    def _handle_switch_page(self, page_name: str) -> None:
        """Update widget store so the navigation widget selects the given page."""
        # Search the previous tree for a navigation widget
        if self._previous_tree is None:
            return
        nav_node = self._find_nav_node(self._previous_tree.root)
        if nav_node is None:
            return

        # Match page_name to the pages list (case-insensitive slug match)
        pages = nav_node.props.get("pages", nav_node.props.get("options", []))
        target_slug = page_name.lower().replace(" ", "-").strip("/")

        for idx, page in enumerate(pages):
            slug = page.lower().replace(" ", "-").replace("/", "").strip()
            if slug == target_slug or page.lower() == page_name.lower():
                self.widget_store[nav_node.id] = idx
                return

    @staticmethod
    def _find_nav_node(node: "UINode") -> "UINode | None":
        """Find the navigation widget in the tree."""
        from fastlit.runtime.tree import UINode
        stack = [node]
        while stack:
            n = stack.pop()
            if n.type in ("navigation", "radio"):
                if "pages" in n.props or "options" in n.props:
                    return n
            for child in n.children:
                stack.append(child)
        return None

    def next_id_for_location(self, location: str) -> int:
        """Return and increment the per-location counter for the given file:line key."""
        val = self._id_counters.get(location, 0)
        self._id_counters[location] = val + 1
        return val


class RerunException(Exception):
    """Raised by st.rerun() to interrupt script execution."""
    pass


class StopException(Exception):
    """Raised by st.stop() to halt script execution."""
    pass


class SwitchPageException(Exception):
    """Raised by st.switch_page() to navigate to another page programmatically."""

    def __init__(self, page_name: str) -> None:
        self.page_name = page_name
        super().__init__(f"Switch to page: {page_name}")


# Private alias used internally to avoid name clashes with `fastlit.__init__`
_StopException = StopException
