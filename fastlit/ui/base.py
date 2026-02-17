"""Foundation for all st.* calls: node emission and stable ID generation."""

from __future__ import annotations

import inspect
import os as _os
from typing import Any

from fastlit.runtime.context import get_current_session
from fastlit.runtime.tree import UINode

# Cache at module level (computed once, never changes)
_fastlit_dir: str = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))


def _emit_node(
    node_type: str,
    props: dict[str, Any],
    *,
    key: str | None = None,
    is_widget: bool = False,
    no_rerun: bool = False,
) -> UINode:
    """Create a UINode and append it to the current tree.

    Args:
        node_type: The type string (e.g. "title", "button", "slider").
        props: The node properties.
        key: Optional explicit key for ID stability.
        is_widget: If True, this node represents an interactive widget.
        no_rerun: If True, widget events won't trigger a script rerun.

    Returns:
        The created UINode.
    """
    session = get_current_session()
    node_id = _make_id(node_type, key)

    # Add noRerun flag to props for value widgets (React-first architecture)
    if no_rerun:
        props["noRerun"] = True

    node = UINode(type=node_type, id=node_id, props=props)
    session.current_tree.append(node)
    return node


def _make_id(node_type: str, key: str | None = None) -> str:
    """Generate a stable ID for a node.

    Strategy:
    - If an explicit key is given, use it: "k:{key}"
    - Otherwise, use the caller's file + line + a per-location counter:
      "w:{filename}:{line}:{counter}"

    The counter is scoped per file:line so that conditional rendering
    on other lines does not shift IDs for unrelated nodes.
    """
    if key is not None:
        return f"k:{key}"

    session = get_current_session()

    # Walk up the call stack to find the user's code (outside fastlit package)
    frame = _get_user_frame()
    if frame is not None:
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        location = f"{filename}:{lineno}"
        counter = session.next_id_for_location(location)
        return f"w:{filename}:{lineno}:{counter}"

    # Fallback: use type + global fallback counter
    fallback_loc = f"_:{node_type}"
    counter = session.next_id_for_location(fallback_loc)
    return f"w:{node_type}:{counter}"


def _get_user_frame() -> Any:
    """Walk frames manually to find the first frame outside the fastlit package.

    Uses inspect.currentframe() + f_back traversal instead of inspect.stack(),
    which is ~100x faster (avoids reading source files from disk).
    """
    frame = inspect.currentframe()
    while frame is not None:
        filepath = _os.path.abspath(frame.f_code.co_filename)
        if not filepath.startswith(_fastlit_dir):
            return frame
        frame = frame.f_back
    return None
