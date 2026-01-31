"""Text display functions: st.title, st.header, st.subheader, st.markdown, st.write."""

from __future__ import annotations

from typing import Any

from fastlit.ui.base import _emit_node


def title(body: str) -> None:
    """Display a title (h1)."""
    _emit_node("title", {"text": str(body)})


def header(body: str) -> None:
    """Display a header (h2)."""
    _emit_node("header", {"text": str(body)})


def subheader(body: str) -> None:
    """Display a subheader (h3)."""
    _emit_node("subheader", {"text": str(body)})


def markdown(body: str) -> None:
    """Display markdown text."""
    _emit_node("markdown", {"text": str(body)})


def write(*args: Any) -> None:
    """Display arguments as text.

    For MVP, converts everything to string and renders as markdown.
    Phase 7 will add smart type detection (DataFrame, dict, etc.).
    """
    parts = []
    for arg in args:
        parts.append(str(arg))
    text = " ".join(parts)
    _emit_node("markdown", {"text": text})


def text(body: str) -> None:
    """Display fixed-width text."""
    _emit_node("text", {"text": str(body)})
