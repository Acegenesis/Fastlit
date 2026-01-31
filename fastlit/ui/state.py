"""Session state access: st.session_state."""

from __future__ import annotations

from fastlit.runtime.context import get_current_session
from fastlit.runtime.session import SessionState


def _get_session_state() -> SessionState:
    """Return the session_state for the active session."""
    return get_current_session().session_state
