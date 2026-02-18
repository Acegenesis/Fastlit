"""Chat components for Fastlit — st.chat_message, st.chat_input."""

from __future__ import annotations

from typing import Any, Callable

from fastlit.runtime.context import get_current_session
from fastlit.runtime.tree import UINode
from fastlit.ui.base import _emit_node, _make_id


class ChatMessage:
    """Context manager for a chat message bubble.

    Usage::

        with st.chat_message("user"):
            st.write("Hello!")
    """

    def __init__(self, node: UINode) -> None:
        self._node = node

    def __enter__(self):
        session = get_current_session()
        tree = session.current_tree
        tree.append(self._node)
        tree.push_container(self._node)
        return self

    def __exit__(self, *args):
        get_current_session().current_tree.pop_container()

    def __getattr__(self, name: str):
        import fastlit as st

        func = getattr(st, name, None)
        if func is None:
            raise AttributeError(f"ChatMessage has no attribute '{name}'")

        def wrapper(*a, **kw):
            with self:
                return func(*a, **kw)
        return wrapper


def chat_message(
    name: str,
    *,
    avatar: str | None = None,
) -> ChatMessage:
    """Display a chat message bubble.

    Args:
        name: The message author — "user", "assistant", "ai", "human",
            or any custom name.
        avatar: Custom avatar (emoji, URL, or None for default).

    Returns:
        A context manager. Use ``with st.chat_message("user"):`` to add
        content inside the bubble.
    """
    msg_id = _make_id("chat_message")
    node = UINode(
        type="chat_message",
        id=msg_id,
        props={
            "name": name,
            "avatar": avatar,
        },
    )
    return ChatMessage(node)


def chat_input(
    placeholder: str = "Type a message...",
    *,
    key: str | None = None,
    max_chars: int | None = None,
    disabled: bool = False,
    on_submit: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
) -> str | None:
    """Display a chat input widget pinned to the bottom of the app.

    Returns the submitted text (once), or None if nothing was submitted.

    Args:
        placeholder: Placeholder text in the input.
        key: Unique widget key.
        max_chars: Maximum characters allowed.
        disabled: If True, disable the input.
        on_submit: Callback when text is submitted.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.

    Returns:
        The submitted text string, or None.
    """
    node = _emit_node(
        "chat_input",
        {
            "placeholder": placeholder,
            "maxChars": max_chars,
            "disabled": disabled,
        },
        key=key,
        is_widget=True,
    )

    session = get_current_session()
    # chat_input is one-shot: pop the value (don't persist across reruns)
    submitted = session.widget_store.pop(node.id, None)

    if submitted is not None and on_submit is not None:
        on_submit(*(args or ()), **(kwargs or {}))

    return submitted
