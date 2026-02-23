"""Status elements for Fastlit.

Provides Streamlit-compatible status functions:
- st.success, st.info, st.warning, st.error, st.exception
- st.progress, st.spinner, st.status
- st.toast, st.balloons, st.snow
"""

from __future__ import annotations

import traceback
import uuid
from contextlib import contextmanager
from typing import Any, Generator

from fastlit.ui.base import _emit_node
from fastlit.runtime.context import get_current_session


def success(body: str, *, icon: str | None = None) -> None:
    """Display a success message.

    Args:
        body: The message to display.
        icon: Optional icon (emoji or icon name).
    """
    _emit_node(
        "alert",
        {
            "type": "success",
            "body": str(body),
            "icon": icon or "✓",
        },
    )


def info(body: str, *, icon: str | None = None) -> None:
    """Display an info message.

    Args:
        body: The message to display.
        icon: Optional icon.
    """
    _emit_node(
        "alert",
        {
            "type": "info",
            "body": str(body),
            "icon": icon or "ℹ",
        },
    )


def warning(body: str, *, icon: str | None = None) -> None:
    """Display a warning message.

    Args:
        body: The message to display.
        icon: Optional icon.
    """
    _emit_node(
        "alert",
        {
            "type": "warning",
            "body": str(body),
            "icon": icon or "⚠",
        },
    )


def error(body: str, *, icon: str | None = None) -> None:
    """Display an error message.

    Args:
        body: The message to display.
        icon: Optional icon.
    """
    _emit_node(
        "alert",
        {
            "type": "error",
            "body": str(body),
            "icon": icon or "✕",
        },
    )


def exception(exception: BaseException | None = None) -> None:
    """Display an exception with traceback.

    Args:
        exception: The exception to display. If None, uses current exception.
    """
    if exception is None:
        # Get current exception from sys.exc_info()
        import sys
        exc_info = sys.exc_info()
        if exc_info[1] is not None:
            exception = exc_info[1]
            tb = "".join(traceback.format_exception(*exc_info))
        else:
            _emit_node(
                "alert",
                {
                    "type": "error",
                    "body": "No exception to display",
                    "icon": "✕",
                },
            )
            return
    else:
        tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))

    _emit_node(
        "exception",
        {
            "type": type(exception).__name__,
            "message": str(exception),
            "traceback": tb,
        },
    )


def progress(
    value: float | int,
    text: str | None = None,
    *,
    key: str | None = None,
) -> None:
    """Display a progress bar.

    Args:
        value: Progress value between 0 and 100 (or 0.0 and 1.0).
        text: Optional text to display above the progress bar.
        key: Optional key.
    """
    # Normalize value to 0-100
    if isinstance(value, float) and 0 <= value <= 1:
        normalized = int(value * 100)
    else:
        normalized = int(value)
    normalized = max(0, min(100, normalized))

    _emit_node(
        "progress",
        {
            "value": normalized,
            "text": text,
        },
        key=key,
    )


@contextmanager
def spinner(text: str = "Loading...") -> Generator[None, None, None]:
    """Display a spinner while executing code.

    Usage:
        with st.spinner("Loading data..."):
            data = load_data()

    Args:
        text: Text to display next to the spinner.
    """
    session = get_current_session()
    spinner_id = f"spin:{uuid.uuid4().hex}"
    session.emit_runtime_event(
        {
            "kind": "spinner",
            "id": spinner_id,
            "text": text,
            "active": True,
        }
    )
    try:
        yield
    finally:
        session.emit_runtime_event(
            {
                "kind": "spinner",
                "id": spinner_id,
                "text": text,
                "active": False,
            }
        )


@contextmanager
def status(
    label: str,
    *,
    expanded: bool = True,
    state: str = "running",
) -> Generator["StatusContainer", None, None]:
    """Display a status container that can be updated.

    Usage:
        with st.status("Downloading data...") as status:
            # ... do work ...
            status.update(label="Done!", state="complete")

    Args:
        label: The status label.
        expanded: Whether to expand the container.
        state: Initial state ("running", "complete", "error").
    """
    container = StatusContainer(label, expanded, state)
    try:
        yield container
    finally:
        container._finalize()


class StatusContainer:
    """Container for status updates."""

    def __init__(self, label: str, expanded: bool, state: str):
        self._label = label
        self._expanded = expanded
        self._state = state
        self._node = _emit_node(
            "status",
            {
                "label": label,
                "expanded": expanded,
                "state": state,
            },
        )

    def update(
        self,
        *,
        label: str | None = None,
        expanded: bool | None = None,
        state: str | None = None,
    ) -> None:
        """Update the status container."""
        if label is not None:
            self._label = label
        if expanded is not None:
            self._expanded = expanded
        if state is not None:
            self._state = state

        # Update node props
        self._node.props["label"] = self._label
        self._node.props["expanded"] = self._expanded
        self._node.props["state"] = self._state

    def _finalize(self) -> None:
        """Finalize the status (called when exiting context)."""
        pass


def toast(
    body: str,
    *,
    icon: str | None = None,
) -> None:
    """Display a toast notification.

    Args:
        body: The message to display.
        icon: Optional icon.
    """
    import time
    _emit_node(
        "toast",
        {
            "body": str(body),
            "icon": icon,
            "_ts": time.time(),
        },
    )


def balloons() -> None:
    """Display celebratory balloons animation."""
    import time
    _emit_node(
        "balloons",
        {"_ts": time.time()},
    )


def snow() -> None:
    """Display snowfall animation."""
    import time
    _emit_node(
        "snow",
        {"_ts": time.time()},
    )
