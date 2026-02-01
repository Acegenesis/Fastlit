"""Fastlit — Streamlit-compatible, blazing fast, Python-first.

Usage:
    import fastlit as st
    st.title("Hello")
"""

from __future__ import annotations

from fastlit.ui.text import title, header, subheader, markdown, write, text
from fastlit.ui.widgets import (
    button,
    slider,
    text_input,
    text_area,
    checkbox,
    selectbox,
    radio,
    number_input,
)
from fastlit.ui.layout import sidebar, columns, tabs, expander
from fastlit.ui.state import _get_session_state
from fastlit.runtime.session import RerunException
from fastlit.runtime.context import get_current_session


# --- session_state as a module-level property ---
# We use a trick: a class instance whose attribute access delegates to
# the active session's state dict.


class _SessionStateProxy:
    """Proxy that forwards attribute access to the active session's state."""

    def __getattr__(self, name: str):
        return getattr(_get_session_state(), name)

    def __setattr__(self, name: str, value):
        setattr(_get_session_state(), name, value)

    def __delattr__(self, name: str):
        delattr(_get_session_state(), name)

    def __contains__(self, key):
        return key in _get_session_state()

    def __getitem__(self, key):
        return _get_session_state()[key]

    def __setitem__(self, key, value):
        _get_session_state()[key] = value

    def __delitem__(self, key):
        del _get_session_state()[key]

    def clear(self):
        _get_session_state().clear()

    def get(self, key, default=None):
        return _get_session_state().get(key, default)

    def __repr__(self):
        try:
            return repr(_get_session_state())
        except RuntimeError:
            return "SessionState(<no active session>)"


session_state = _SessionStateProxy()


def rerun() -> None:
    """Stop the current script run and trigger a rerun."""
    raise RerunException()


__all__ = [
    "title",
    "header",
    "subheader",
    "markdown",
    "write",
    "text",
    "button",
    "slider",
    "text_input",
    "text_area",
    "checkbox",
    "selectbox",
    "radio",
    "number_input",
    "sidebar",
    "columns",
    "tabs",
    "expander",
    "session_state",
    "rerun",
]
