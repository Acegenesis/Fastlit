"""Interactive widgets for Fastlit."""

from __future__ import annotations

from typing import Any, Sequence

from fastlit.runtime.context import get_current_session
from fastlit.ui.base import _emit_node
from fastlit.ui.widget_value import WidgetValue


def button(label: str, *, key: str | None = None) -> bool:
    """Display a button. Returns True if it was clicked on the previous run."""
    node = _emit_node("button", {"label": label}, key=key, is_widget=True)
    session = get_current_session()
    clicked = session.widget_store.pop(node.id, False)
    return bool(clicked)


def slider(
    label: str,
    min_value: float = 0,
    max_value: float = 100,
    value: float | None = None,
    step: float | None = None,
    *,
    key: str | None = None,
) -> float | int:
    """Display a slider widget."""
    if value is None:
        value = min_value
    if step is None:
        if isinstance(min_value, int) and isinstance(max_value, int) and isinstance(value, int):
            step = 1
        else:
            step = (max_value - min_value) / 100

    node = _emit_node(
        "slider",
        {"label": label, "min": min_value, "max": max_value, "value": value, "step": step},
        key=key,
        is_widget=True,
    )
    session = get_current_session()
    current = session.widget_store.get(node.id, value)
    node.props["value"] = current
    if isinstance(min_value, int) and isinstance(max_value, int) and step == 1:
        return WidgetValue(int(current), node.id)
    return WidgetValue(float(current), node.id)


def text_input(
    label: str,
    value: str = "",
    *,
    placeholder: str = "",
    max_chars: int | None = None,
    key: str | None = None,
) -> str:
    """Display a single-line text input."""
    node = _emit_node(
        "text_input",
        {"label": label, "value": value, "placeholder": placeholder, "maxChars": max_chars},
        key=key,
        is_widget=True,
    )
    session = get_current_session()
    current = str(session.widget_store.get(node.id, value))
    node.props["value"] = current
    return WidgetValue(current, node.id)


def text_area(
    label: str,
    value: str = "",
    *,
    height: int = 150,
    placeholder: str = "",
    max_chars: int | None = None,
    key: str | None = None,
) -> str:
    """Display a multi-line text area."""
    node = _emit_node(
        "text_area",
        {"label": label, "value": value, "height": height, "placeholder": placeholder, "maxChars": max_chars},
        key=key,
        is_widget=True,
    )
    session = get_current_session()
    current = str(session.widget_store.get(node.id, value))
    node.props["value"] = current
    return WidgetValue(current, node.id)


def checkbox(
    label: str,
    value: bool = False,
    *,
    key: str | None = None,
) -> bool:
    """Display a checkbox."""
    node = _emit_node(
        "checkbox",
        {"label": label, "value": value},
        key=key,
        is_widget=True,
    )
    session = get_current_session()
    current = bool(session.widget_store.get(node.id, value))
    node.props["value"] = current
    return WidgetValue(current, node.id)


def selectbox(
    label: str,
    options: Sequence[str],
    index: int = 0,
    *,
    key: str | None = None,
) -> str | None:
    """Display a select dropdown."""
    options_list = list(options)
    if not options_list:
        return None
    node = _emit_node(
        "selectbox",
        {"label": label, "options": options_list, "index": index},
        key=key,
        is_widget=True,
    )
    session = get_current_session()
    current_idx = session.widget_store.get(node.id, index)
    if isinstance(current_idx, int) and 0 <= current_idx < len(options_list):
        node.props["index"] = current_idx
        return WidgetValue(options_list[current_idx], node.id)
    node.props["index"] = index
    return WidgetValue(options_list[index], node.id)


def radio(
    label: str,
    options: Sequence[str],
    index: int = 0,
    *,
    key: str | None = None,
) -> str | None:
    """Display radio buttons."""
    options_list = list(options)
    if not options_list:
        return None
    node = _emit_node(
        "radio",
        {"label": label, "options": options_list, "index": index},
        key=key,
        is_widget=True,
    )
    session = get_current_session()
    current_idx = session.widget_store.get(node.id, index)
    if isinstance(current_idx, int) and 0 <= current_idx < len(options_list):
        node.props["index"] = current_idx
        return WidgetValue(options_list[current_idx], node.id)
    node.props["index"] = index
    return WidgetValue(options_list[index], node.id)


def number_input(
    label: str,
    min_value: float | None = None,
    max_value: float | None = None,
    value: float = 0,
    step: float = 1,
    *,
    key: str | None = None,
) -> float | int:
    """Display a numeric input."""
    node = _emit_node(
        "number_input",
        {"label": label, "min": min_value, "max": max_value, "value": value, "step": step},
        key=key,
        is_widget=True,
    )
    session = get_current_session()
    current = session.widget_store.get(node.id, value)
    node.props["value"] = current
    if isinstance(value, int) and step == 1:
        return WidgetValue(int(current), node.id)
    return WidgetValue(float(current), node.id)
