"""Interactive widgets for Fastlit — Streamlit-compatible signatures."""

from __future__ import annotations

from typing import Any, Callable, Sequence

from fastlit.runtime.context import get_current_session
from fastlit.ui.base import _emit_node
from fastlit.ui.widget_value import WidgetValue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_callback(
    on_change: Callable | None,
    args: list | tuple | None,
    kwargs: dict | None,
) -> None:
    """Fire an on_change callback if provided."""
    if on_change is not None:
        on_change(*(args or ()), **(kwargs or {}))


def _format_options(options: Sequence, format_func: Callable | None) -> list[str]:
    """Apply format_func to produce display labels."""
    if format_func is None:
        return [str(o) for o in options]
    return [str(format_func(o)) for o in options]


# ---------------------------------------------------------------------------
# st.button
# ---------------------------------------------------------------------------

def button(
    label: str,
    key: str | None = None,
    help: str | None = None,
    on_click: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    type: str = "secondary",
    icon: str | None = None,
    disabled: bool = False,
    use_container_width: bool | None = None,
) -> bool:
    """Display a button. Returns True if it was clicked on the previous run."""
    node = _emit_node(
        "button",
        {
            "label": label,
            "help": help,
            "type": type,
            "icon": icon,
            "disabled": disabled,
            "useContainerWidth": use_container_width or False,
        },
        key=key,
        is_widget=True,
    )
    session = get_current_session()
    clicked = session.widget_store.pop(node.id, False)
    if clicked:
        _run_callback(on_click, args, kwargs)
    return bool(clicked)


# ---------------------------------------------------------------------------
# st.slider
# ---------------------------------------------------------------------------

def slider(
    label: str,
    min_value: float | None = None,
    max_value: float | None = None,
    value: float | None = None,
    step: float | None = None,
    format: str | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> float | int:
    """Display a slider widget."""
    # Streamlit defaults: min=0, max=100 when all None
    if min_value is None:
        min_value = 0
    if max_value is None:
        max_value = 100
    if value is None:
        value = min_value
    if step is None:
        if isinstance(min_value, int) and isinstance(max_value, int) and isinstance(value, int):
            step = 1
        else:
            step = (max_value - min_value) / 100

    node = _emit_node(
        "slider",
        {
            "label": label,
            "min": min_value,
            "max": max_value,
            "value": value,
            "step": step,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )
    session = get_current_session()
    prev = session.widget_store.get(node.id, value)
    current = prev
    node.props["value"] = current
    if not isinstance(prev, type(value)) or prev != value:
        _run_callback(on_change, args, kwargs)
    if isinstance(min_value, int) and isinstance(max_value, int) and step == 1:
        return WidgetValue(int(current), node.id)
    return WidgetValue(float(current), node.id)


# ---------------------------------------------------------------------------
# st.text_input
# ---------------------------------------------------------------------------

def text_input(
    label: str,
    value: str = "",
    max_chars: int | None = None,
    key: str | None = None,
    type: str = "default",
    help: str | None = None,
    autocomplete: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    placeholder: str | None = None,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> str:
    """Display a single-line text input."""
    node = _emit_node(
        "text_input",
        {
            "label": label,
            "value": value,
            "placeholder": placeholder or "",
            "maxChars": max_chars,
            "inputType": type,
            "help": help,
            "autocomplete": autocomplete,
            "disabled": disabled,
            "labelVisibility": label_visibility,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )
    session = get_current_session()
    current = str(session.widget_store.get(node.id, value))
    node.props["value"] = current
    return WidgetValue(current, node.id)


# ---------------------------------------------------------------------------
# st.text_area
# ---------------------------------------------------------------------------

def text_area(
    label: str,
    value: str = "",
    height: int | None = None,
    max_chars: int | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    placeholder: str | None = None,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> str:
    """Display a multi-line text area."""
    node = _emit_node(
        "text_area",
        {
            "label": label,
            "value": value,
            "height": height,
            "placeholder": placeholder or "",
            "maxChars": max_chars,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )
    session = get_current_session()
    current = str(session.widget_store.get(node.id, value))
    node.props["value"] = current
    return WidgetValue(current, node.id)


# ---------------------------------------------------------------------------
# st.checkbox
# ---------------------------------------------------------------------------

def checkbox(
    label: str,
    value: bool = False,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> bool:
    """Display a checkbox."""
    node = _emit_node(
        "checkbox",
        {
            "label": label,
            "value": value,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )
    session = get_current_session()
    current = bool(session.widget_store.get(node.id, value))
    node.props["value"] = current
    return WidgetValue(current, node.id)


# ---------------------------------------------------------------------------
# st.selectbox
# ---------------------------------------------------------------------------

def selectbox(
    label: str,
    options: Sequence,
    index: int = 0,
    format_func: Callable | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    placeholder: str | None = None,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> Any | None:
    """Display a select dropdown."""
    raw_options = list(options)
    if not raw_options:
        return None
    display_labels = _format_options(raw_options, format_func)
    node = _emit_node(
        "selectbox",
        {
            "label": label,
            "options": display_labels,
            "index": index,
            "placeholder": placeholder,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )
    session = get_current_session()
    current_idx = session.widget_store.get(node.id, index)
    if isinstance(current_idx, int) and 0 <= current_idx < len(raw_options):
        node.props["index"] = current_idx
        return WidgetValue(raw_options[current_idx], node.id)
    node.props["index"] = index
    return WidgetValue(raw_options[index], node.id)


# ---------------------------------------------------------------------------
# st.radio
# ---------------------------------------------------------------------------

def radio(
    label: str,
    options: Sequence,
    index: int = 0,
    format_func: Callable | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    disabled: bool = False,
    horizontal: bool = False,
    captions: Sequence[str] | None = None,
    label_visibility: str = "visible",
) -> Any | None:
    """Display radio buttons."""
    raw_options = list(options)
    if not raw_options:
        return None
    display_labels = _format_options(raw_options, format_func)
    node = _emit_node(
        "radio",
        {
            "label": label,
            "options": display_labels,
            "index": index,
            "horizontal": horizontal,
            "captions": list(captions) if captions else None,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )
    session = get_current_session()
    current_idx = session.widget_store.get(node.id, index)
    if isinstance(current_idx, int) and 0 <= current_idx < len(raw_options):
        node.props["index"] = current_idx
        return WidgetValue(raw_options[current_idx], node.id)
    node.props["index"] = index
    return WidgetValue(raw_options[index], node.id)


# ---------------------------------------------------------------------------
# st.number_input
# ---------------------------------------------------------------------------

def number_input(
    label: str,
    min_value: float | None = None,
    max_value: float | None = None,
    value: float | int | str = "min",
    step: float | None = None,
    format: str | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    placeholder: str | None = None,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> float | int:
    """Display a numeric input."""
    # Resolve "min" sentinel like Streamlit
    if value == "min":
        value = min_value if min_value is not None else 0

    # Auto-determine step like Streamlit
    if step is None:
        if isinstance(value, int):
            step = 1
        else:
            step = 0.01

    node = _emit_node(
        "number_input",
        {
            "label": label,
            "min": min_value,
            "max": max_value,
            "value": value,
            "step": step,
            "placeholder": placeholder,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )
    session = get_current_session()
    current = session.widget_store.get(node.id, value)
    node.props["value"] = current
    if isinstance(value, int) and step == 1:
        return WidgetValue(int(current), node.id)
    return WidgetValue(float(current), node.id)
