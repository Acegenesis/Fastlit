"""Context management for the active Fastlit session.

Uses contextvars so that st.* calls route to the correct session,
even under async concurrency.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastlit.runtime.session import Session

_current_session: ContextVar[Session | None] = ContextVar(
    "_current_session", default=None
)


def get_current_session() -> Session:
    """Return the active session or raise."""
    session = _current_session.get()
    if session is None:
        raise RuntimeError(
            "No active Fastlit session. "
            "st.* calls can only be used inside a Fastlit app script."
        )
    return session


def set_current_session(session: Session) -> None:
    """Set the active session for the current context."""
    _current_session.set(session)


def clear_current_session() -> None:
    """Clear the active session."""
    _current_session.set(None)
