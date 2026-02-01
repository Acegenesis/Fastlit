"""Text display functions: st.title, st.header, st.subheader, st.markdown, st.write."""

from __future__ import annotations

import re
from typing import Any

from fastlit.ui.base import _emit_node

# Marker pattern: \x00W<widget_id>\x00<value>\x00
_MARKER_RE = re.compile(r"\x00W(.+?)\x00(.*?)\x00")


def _process_text(raw: str) -> dict:
    """Extract widget markers from text and return props dict.

    If markers are found, returns:
      {"text": <clean_text>, "_tpl": <template>, "_refs": {placeholder: widgetId}}
    Otherwise:
      {"text": <raw_text>}
    """
    matches = list(_MARKER_RE.finditer(raw))
    if not matches:
        return {"text": raw}

    # Build clean text (markers replaced with actual values)
    clean = _MARKER_RE.sub(r"\2", raw)

    # Build template (markers replaced with placeholders) and refs map
    refs = {}
    counter = 0

    def replacer(m: re.Match) -> str:
        nonlocal counter
        key = f"__w{counter}__"
        refs[key] = m.group(1)  # widget ID
        counter += 1
        return key

    template = _MARKER_RE.sub(replacer, raw)

    return {"text": clean, "_tpl": template, "_refs": refs}


def title(body: str) -> None:
    """Display a title (h1)."""
    props = _process_text(str(body))
    _emit_node("title", props)


def header(body: str) -> None:
    """Display a header (h2)."""
    props = _process_text(str(body))
    _emit_node("header", props)


def subheader(body: str) -> None:
    """Display a subheader (h3)."""
    props = _process_text(str(body))
    _emit_node("subheader", props)


def markdown(body: str) -> None:
    """Display markdown text."""
    props = _process_text(str(body))
    _emit_node("markdown", props)


def write(*args: Any) -> None:
    """Display arguments as text.

    For MVP, converts everything to string and renders as markdown.
    Phase 7 will add smart type detection (DataFrame, dict, etc.).
    """
    parts = []
    for arg in args:
        parts.append(str(arg))
    raw = " ".join(parts)
    props = _process_text(raw)
    _emit_node("markdown", props)


def text(body: str) -> None:
    """Display fixed-width text."""
    props = _process_text(str(body))
    _emit_node("text", props)
