"""Context management for the active Fastlit session.

Uses contextvars so that st.* calls route to the correct session,
even under async concurrency.
"""

from __future__ import annotations

import contextvars
import threading
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Callable

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
            "st.* calls can only be used inside a Fastlit app script. "
            "If calling from a background thread, use st.run_in_thread()."
        )
    return session


def set_current_session(session: Session) -> None:
    """Set the active session for the current context."""
    _current_session.set(session)


def clear_current_session() -> None:
    """Clear the active session."""
    _current_session.set(None)


def run_with_session_context(fn: Callable, *args: Any, **kwargs: Any) -> Any:
    """Run *fn* inside a copy of the current context so st.* works in threads.

    ContextVar values (including the active session) are inherited by the copy.

    Example::

        def my_worker():
            st.write("Hello from thread!")

        t = threading.Thread(target=lambda: st.run_with_session_context(my_worker))
        t.start()
    """
    ctx = contextvars.copy_context()
    return ctx.run(fn, *args, **kwargs)


def run_in_thread(fn: Callable, *args: Any, **kwargs: Any) -> threading.Thread:
    """Create a Thread that inherits the current session context.

    The returned thread is NOT started — call ``.start()`` yourself.

    Example::

        t = st.run_in_thread(my_heavy_fn, df)
        t.start()
        t.join()
    """
    ctx = contextvars.copy_context()

    def _target():
        ctx.run(fn, *args, **kwargs)

    return threading.Thread(target=_target)
