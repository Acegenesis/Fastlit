"""Foundation for all st.* calls: node emission and stable ID generation."""

from __future__ import annotations

import inspect
from typing import Any

from fastlit.runtime.context import get_current_session
from fastlit.runtime.tree import UINode


def _emit_node(
    node_type: str,
    props: dict[str, Any],
    *,
    key: str | None = None,
    is_widget: bool = False,
) -> UINode:
    """Create a UINode and append it to the current tree.

    Args:
        node_type: The type string (e.g. "title", "button", "slider").
        props: The node properties.
        key: Optional explicit key for ID stability.
        is_widget: If True, this node represents an interactive widget.

    Returns:
        The created UINode.
    """
    session = get_current_session()
    node_id = _make_id(node_type, key)
    node = UINode(type=node_type, id=node_id, props=props)
    session.current_tree.append(node)
    return node


def _make_id(node_type: str, key: str | None = None) -> str:
    """Generate a stable ID for a node.

    Strategy:
    - If an explicit key is given, use it: "k:{key}"
    - Otherwise, use the caller's file + line + a per-run counter:
      "w:{filename}:{line}:{counter}"

    The counter ensures uniqueness when the same line is hit
    multiple times (e.g. in a loop).
    """
    if key is not None:
        return f"k:{key}"

    session = get_current_session()
    counter = session.next_id()

    # Walk up the call stack to find the user's code (outside fastlit package)
    frame = _get_user_frame()
    if frame is not None:
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        return f"w:{filename}:{lineno}:{counter}"

    # Fallback: use type + counter
    return f"w:{node_type}:{counter}"


def _get_user_frame() -> Any:
    """Walk the call stack to find the first frame outside the fastlit package."""
    import os

    fastlit_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stack = inspect.stack()
    for frame_info in stack:
        filepath = os.path.abspath(frame_info.filename)
        if not filepath.startswith(fastlit_dir):
            return frame_info.frame
    return None
