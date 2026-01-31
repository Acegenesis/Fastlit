"""Interactive widgets: st.button (Phase 1), more in Phase 2."""

from __future__ import annotations

from typing import Any

from fastlit.runtime.context import get_current_session
from fastlit.ui.base import _emit_node


def button(label: str, *, key: str | None = None) -> bool:
    """Display a button. Returns True if it was clicked on the previous run."""
    node = _emit_node("button", {"label": label}, key=key, is_widget=True)
    session = get_current_session()
    # Button is a "trigger" widget: the value is True for one run after click,
    # then resets. We pop it so it's only True once.
    clicked = session.widget_store.pop(node.id, False)
    return bool(clicked)
