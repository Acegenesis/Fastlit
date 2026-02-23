"""Interactive widgets for Fastlit — Streamlit-compatible signatures."""

from __future__ import annotations

import os
import datetime
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


def _max_upload_bytes() -> int:
    """Maximum accepted upload size (bytes) for a single file."""
    try:
        mb = int(os.environ.get("FASTLIT_MAX_UPLOAD_MB", "10"))
    except ValueError:
        mb = 10
    mb = max(1, mb)
    return mb * 1024 * 1024


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
    icon_position: str = "left",
    disabled: bool = False,
    use_container_width: bool | None = None,
    width: str | int = "content",
    shortcut: str | None = None,
) -> bool:
    """Display a button. Returns True if it was clicked on the previous run.

    Args:
        label: Button label (supports Markdown).
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_click: Callback when button is clicked.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        type: Button style - "primary", "secondary" (default), or "tertiary".
        icon: Optional emoji or Material Symbols icon.
        icon_position: Icon position - "left" (default) or "right".
        disabled: If True, disable the button.
        use_container_width: Deprecated, use `width` instead.
        width: Button width - "content" (default), "stretch", or pixel value.
        shortcut: Optional keyboard shortcut (e.g., "Ctrl+K").

    Returns:
        True if clicked, False otherwise.
    """
    # Handle deprecated use_container_width
    actual_width = width
    if use_container_width:
        actual_width = "stretch"

    node = _emit_node(
        "button",
        {
            "label": label,
            "help": help,
            "type": type,
            "icon": icon,
            "iconPosition": icon_position,
            "disabled": disabled,
            "width": actual_width,
            "shortcut": shortcut,
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
    value: float | tuple[float, float] | None = None,
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
    width: str | int = "stretch",
) -> "float | int | tuple[float, float] | tuple[int, int]":
    """Display a slider widget.

    Args:
        label: Slider label (supports Markdown).
        min_value: Minimum value (default: 0).
        max_value: Maximum value (default: 100).
        value: Initial value (default: min_value). Pass a tuple ``(lo, hi)``
            for a range slider that returns two values.
        step: Step increment (default: 1 for int, 0.01 for float).
        format: Printf-style format string (e.g., "%d", "%.2f", "percent", "dollar").
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when value changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        disabled: If True, disable the slider.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        width: Slider width - "stretch" (default) or pixel value.

    Returns:
        Current slider value (int or float), or tuple for range sliders.
    """
    # Streamlit defaults: min=0, max=100 when all None
    if min_value is None:
        min_value = 0
    if max_value is None:
        max_value = 100

    if value is None:
        value = min_value

    # Detect range mode after defaulting scalar None.
    is_range = isinstance(value, (tuple, list))

    if is_range:
        if len(value) != 2:
            raise ValueError("Range slider value must be a tuple/list of length 2.")
        lo_raw, hi_raw = value[0], value[1]
        lo = min_value if lo_raw is None else lo_raw
        hi = max_value if hi_raw is None else hi_raw
        value = (lo, hi)
        ref_val = lo
    else:
        ref_val = value

    if step is None:
        if isinstance(min_value, int) and isinstance(max_value, int) and isinstance(ref_val, int):
            step = 1
        else:
            step = (max_value - min_value) / 100

    send_value = [lo, hi] if is_range else value

    node = _emit_node(
        "slider",
        {
            "label": label,
            "min": min_value,
            "max": max_value,
            "value": send_value,
            "step": step,
            "format": format,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
            "width": width,
            "isRange": is_range,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )
    session = get_current_session()
    current = session.widget_store.get(node.id, send_value)
    node.props["value"] = current

    is_int_slider = (
        isinstance(min_value, int)
        and isinstance(max_value, int)
        and isinstance(ref_val, int)
        and isinstance(step, int)
    )

    if is_range:
        if isinstance(current, list) and len(current) == 2:
            cur_lo = lo if current[0] is None else current[0]
            cur_hi = hi if current[1] is None else current[1]
            if is_int_slider:
                return WidgetValue((int(cur_lo), int(cur_hi)), node.id)
            return WidgetValue((float(cur_lo), float(cur_hi)), node.id)
        if is_int_slider:
            return WidgetValue((int(lo), int(hi)), node.id)
        return WidgetValue((float(lo), float(hi)), node.id)
    else:
        if is_int_slider:
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
    icon: str | None = None,
    width: str | int = "stretch",
) -> str:
    """Display a single-line text input.

    Args:
        label: Input label (supports Markdown).
        value: Initial value (default: "").
        max_chars: Maximum characters allowed.
        key: Unique widget key.
        type: Input type - "default" or "password".
        help: Tooltip text (supports Markdown).
        autocomplete: HTML autocomplete attribute value.
        on_change: Callback when value changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        placeholder: Placeholder text when empty.
        disabled: If True, disable the input.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        icon: Optional emoji, Material Symbols icon, or "spinner".
        width: Input width - "stretch" (default) or pixel value.

    Returns:
        Current input value.
    """
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
            "icon": icon,
            "width": width,
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
    height: str | int | None = None,
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
    width: str | int = "stretch",
) -> str:
    """Display a multi-line text area.

    Args:
        label: Input label (supports Markdown).
        value: Initial value (default: "").
        height: Area height - None (3 lines), "content", "stretch", or pixel value.
        max_chars: Maximum characters allowed.
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when value changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        placeholder: Placeholder text when empty.
        disabled: If True, disable the input.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        width: Input width - "stretch" (default) or pixel value.

    Returns:
        Current input value.
    """
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
            "width": width,
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
    width: str | int = "content",
) -> bool:
    """Display a checkbox.

    Args:
        label: Checkbox label (supports Markdown).
        value: Initial checked state (default: False).
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when value changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        disabled: If True, disable the checkbox.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        width: Widget width - "content" (default), "stretch", or pixel value.

    Returns:
        Current checked state.
    """
    node = _emit_node(
        "checkbox",
        {
            "label": label,
            "value": value,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
            "width": width,
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
    index: int | None = 0,
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
    accept_new_options: bool = False,
    width: str | int = "stretch",
) -> Any | None:
    """Display a select dropdown.

    Args:
        label: Selectbox label (supports Markdown).
        options: List of options to select from.
        index: Index of preselected option (default: 0). Use None for empty.
        format_func: Function to format option labels.
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when selection changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        placeholder: Text shown when no selection.
        disabled: If True, disable the selectbox.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        accept_new_options: If True, allow user to enter new options.
        width: Widget width - "stretch" (default) or pixel value.

    Returns:
        Selected option or None.
    """
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
            "acceptNewOptions": accept_new_options,
            "width": width,
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
    if index is None:
        return None
    node.props["index"] = index
    return WidgetValue(raw_options[index], node.id)


# ---------------------------------------------------------------------------
# st.radio
# ---------------------------------------------------------------------------

def radio(
    label: str,
    options: Sequence,
    index: int | None = 0,
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
    width: str | int = "content",
) -> Any | None:
    """Display radio buttons.

    Args:
        label: Radio group label (supports Markdown).
        options: List of options.
        index: Index of preselected option (default: 0). Use None for empty.
        format_func: Function to format option labels.
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when selection changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        disabled: If True, disable the radio buttons.
        horizontal: If True, arrange options horizontally.
        captions: List of captions to show below each option.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        width: Widget width - "content" (default), "stretch", or pixel value.

    Returns:
        Selected option or None.
    """
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
            "width": width,
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
    if index is None:
        return None
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
    icon: str | None = None,
    width: str | int = "stretch",
) -> float | int:
    """Display a numeric input.

    Args:
        label: Input label (supports Markdown).
        min_value: Minimum allowed value.
        max_value: Maximum allowed value.
        value: Initial value (default: "min" uses min_value or 0).
        step: Step increment (default: 1 for int, 0.01 for float).
        format: Printf-style format string (e.g., "%d", "%.2f").
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when value changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        placeholder: Placeholder text when empty.
        disabled: If True, disable the input.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        icon: Optional emoji or Material Symbols icon.
        width: Widget width - "stretch" (default) or pixel value.

    Returns:
        Current numeric value (int or float based on input types).
    """
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
            "format": format,
            "placeholder": placeholder,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
            "icon": icon,
            "width": width,
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


# ---------------------------------------------------------------------------
# st.multiselect
# ---------------------------------------------------------------------------

def multiselect(
    label: str,
    options: Sequence,
    default: Sequence | None = None,
    format_func: Callable | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    max_selections: int | None = None,
    placeholder: str | None = None,
    disabled: bool = False,
    label_visibility: str = "visible",
    accept_new_options: bool = False,
    width: str | int = "stretch",
) -> list:
    """Display a multi-select dropdown.

    Args:
        label: Widget label (supports Markdown).
        options: List of options to select from.
        default: Default selected values (list).
        format_func: Function to format option labels.
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when selection changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        max_selections: Maximum number of selections allowed.
        placeholder: Placeholder text when nothing is selected.
        disabled: If True, disable the widget.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        accept_new_options: If True, allow user to add new options.
        width: Widget width - "stretch" (default) or pixel value.

    Returns:
        List of selected values.
    """
    raw_options = list(options)
    if not raw_options:
        return []

    display_labels = _format_options(raw_options, format_func)

    # Convert default to list of values (strings)
    default_values: list[str] = []
    if default is not None:
        for val in default:
            if val in raw_options:
                idx = raw_options.index(val)
                default_values.append(display_labels[idx])

    node = _emit_node(
        "multiselect",
        {
            "label": label,
            "options": display_labels,
            "defaultValues": default_values,
            "maxSelections": max_selections,
            "placeholder": placeholder or "Select...",
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
            "acceptNewOptions": accept_new_options,
            "width": width,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )

    session = get_current_session()
    # Now we receive values (strings) instead of indices
    current_values = session.widget_store.get(node.id, default_values)

    # Ensure current_values is a list of valid option values
    if not isinstance(current_values, list):
        current_values = default_values

    # Filter to only valid options and convert back to original values
    valid_values = []
    for v in current_values:
        if v in display_labels:
            idx = display_labels.index(v)
            valid_values.append(raw_options[idx])

    node.props["selectedValues"] = [display_labels[raw_options.index(v)] for v in valid_values if v in raw_options]

    # Use WidgetValue for real-time text interpolation
    return WidgetValue(valid_values, node.id)


# ---------------------------------------------------------------------------
# st.date_input
# ---------------------------------------------------------------------------

def date_input(
    label: str,
    value: datetime.date | tuple[datetime.date, datetime.date] | str | None = "today",
    min_value: datetime.date | str | None = None,
    max_value: datetime.date | str | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    format: str = "YYYY/MM/DD",
    disabled: bool = False,
    label_visibility: str = "visible",
    width: str | int = "stretch",
) -> datetime.date | tuple[datetime.date, datetime.date] | None:
    """Display a date input widget.

    Args:
        label: Widget label (supports Markdown).
        value: Default date - "today", date object, ISO string, tuple for range, or None.
        min_value: Minimum selectable date (default: 10 years before value).
        max_value: Maximum selectable date (default: 10 years after value).
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when date changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        format: Date format - "YYYY/MM/DD", "DD/MM/YYYY", or "MM/DD/YYYY".
        disabled: If True, disable the widget.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        width: Widget width - "stretch" (default) or pixel value.

    Returns:
        Selected date, tuple of dates for range, or None.
    """
    # Handle "today" sentinel and None
    if value == "today":
        value = datetime.date.today()
    elif value is None:
        value = datetime.date.today()
    elif isinstance(value, str):
        value = datetime.date.fromisoformat(value)

    # Handle min/max value strings
    if isinstance(min_value, str):
        min_value = datetime.date.fromisoformat(min_value) if min_value != "today" else datetime.date.today()
    if isinstance(max_value, str):
        max_value = datetime.date.fromisoformat(max_value) if max_value != "today" else datetime.date.today()

    is_range = isinstance(value, tuple)

    # Serialize dates to ISO format for JSON
    if is_range:
        value_str = [value[0].isoformat(), value[1].isoformat()]
    else:
        value_str = value.isoformat()

    node = _emit_node(
        "date_input",
        {
            "label": label,
            "value": value_str,
            "isRange": is_range,
            "min": min_value.isoformat() if min_value else None,
            "max": max_value.isoformat() if max_value else None,
            "format": format,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
            "width": width,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )

    session = get_current_session()
    stored = session.widget_store.get(node.id, value_str)

    # Parse stored value back to date objects
    if is_range:
        if isinstance(stored, list) and len(stored) == 2:
            try:
                d1 = datetime.date.fromisoformat(stored[0])
                d2 = datetime.date.fromisoformat(stored[1])
                return WidgetValue((d1, d2), node.id)
            except (ValueError, TypeError):
                pass
        return WidgetValue(value, node.id)
    else:
        if isinstance(stored, str):
            try:
                return WidgetValue(datetime.date.fromisoformat(stored), node.id)
            except ValueError:
                pass
        return WidgetValue(value, node.id)


# ---------------------------------------------------------------------------
# st.time_input
# ---------------------------------------------------------------------------

def time_input(
    label: str,
    value: datetime.time | str | None = "now",
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    step: int = 900,  # 15 minutes in seconds
    disabled: bool = False,
    label_visibility: str = "visible",
    width: str | int = "stretch",
) -> datetime.time | None:
    """Display a time input widget.

    Args:
        label: Widget label (supports Markdown).
        value: Default time - "now", time object, ISO string, or None.
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when time changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        step: Step size in seconds (default: 900 = 15 minutes).
        disabled: If True, disable the widget.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        width: Widget width - "stretch" (default) or pixel value.

    Returns:
        Selected time or None.
    """
    # Handle "now" sentinel and string values
    if value == "now":
        value = datetime.datetime.now().time().replace(second=0, microsecond=0)
    elif value is None:
        value = datetime.time(0, 0)
    elif isinstance(value, str):
        parts = value.split(":")
        value = datetime.time(int(parts[0]), int(parts[1]))

    # Serialize to HH:MM format
    value_str = value.strftime("%H:%M")

    node = _emit_node(
        "time_input",
        {
            "label": label,
            "value": value_str,
            "step": step,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
            "width": width,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )

    session = get_current_session()
    stored = session.widget_store.get(node.id, value_str)

    if isinstance(stored, str):
        try:
            parts = stored.split(":")
            return WidgetValue(datetime.time(int(parts[0]), int(parts[1])), node.id)
        except (ValueError, IndexError):
            pass
    return WidgetValue(value, node.id)


# ---------------------------------------------------------------------------
# st.toggle
# ---------------------------------------------------------------------------

def toggle(
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
    width: str | int = "content",
) -> bool:
    """Display a toggle switch.

    Like a checkbox but with a switch UI.

    Args:
        label: Widget label (supports Markdown).
        value: Initial toggle state (default: False).
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when toggle changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        disabled: If True, disable the widget.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        width: Widget width - "content" (default), "stretch", or pixel value.

    Returns:
        Current toggle state.
    """
    node = _emit_node(
        "toggle",
        {
            "label": label,
            "value": value,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
            "width": width,
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
# st.color_picker
# ---------------------------------------------------------------------------

def color_picker(
    label: str,
    value: str = "#000000",
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    disabled: bool = False,
    label_visibility: str = "visible",
    width: str | int = "content",
) -> str:
    """Display a color picker widget.

    Args:
        label: Widget label (supports Markdown).
        value: Default color in hex format (#RRGGBB).
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when color changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        disabled: If True, disable the widget.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        width: Widget width - "content" (default), "stretch", or pixel value.

    Returns:
        Selected color in hex format (#RRGGBB).
    """
    # Ensure value starts with #
    if not value.startswith("#"):
        value = f"#{value}"

    node = _emit_node(
        "color_picker",
        {
            "label": label,
            "value": value,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
            "width": width,
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
# st.link_button
# ---------------------------------------------------------------------------

def link_button(
    label: str,
    url: str,
    *,
    help: str | None = None,
    type: str = "secondary",
    icon: str | None = None,
    disabled: bool = False,
    use_container_width: bool = False,
) -> None:
    """Display a link button that opens a URL.

    Args:
        label: The button label.
        url: The URL to open when clicked.
        help: Tooltip text.
        type: Button type ("primary" or "secondary").
        icon: Optional icon (emoji or icon name).
        disabled: If True, disable the button.
        use_container_width: If True, use full container width.
    """
    _emit_node(
        "link_button",
        {
            "label": label,
            "url": url,
            "help": help,
            "type": type,
            "icon": icon,
            "disabled": disabled,
            "useContainerWidth": use_container_width,
        },
    )


# ---------------------------------------------------------------------------
# st.page_link
# ---------------------------------------------------------------------------

def page_link(
    page: str,
    *,
    label: str | None = None,
    icon: str | None = None,
    help: str | None = None,
    disabled: bool = False,
    use_container_width: bool = False,
) -> None:
    """Display a link to another page in the app.

    Args:
        page: The page path or URL.
        label: The link label (defaults to page name).
        icon: Optional icon (emoji or icon name).
        help: Tooltip text.
        disabled: If True, disable the link.
        use_container_width: If True, use full container width.
    """
    _emit_node(
        "page_link",
        {
            "page": page,
            "label": label or page,
            "icon": icon,
            "help": help,
            "disabled": disabled,
            "useContainerWidth": use_container_width,
        },
    )


# ---------------------------------------------------------------------------
# st.download_button
# ---------------------------------------------------------------------------

def download_button(
    label: str,
    data: Any,
    file_name: str | None = None,
    mime: str | None = None,
    key: str | None = None,
    help: str | None = None,
    on_click: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    type: str = "secondary",
    icon: str | None = None,
    disabled: bool = False,
    use_container_width: bool = False,
) -> bool:
    """Display a download button.

    Args:
        label: The button label.
        data: The data to download (str, bytes, or file-like object).
        file_name: The name for the downloaded file.
        mime: The MIME type (auto-detected if not provided).
        key: Unique key for the widget.
        help: Tooltip text.
        on_click: Callback when clicked.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        type: Button type ("primary" or "secondary").
        icon: Optional icon.
        disabled: If True, disable the button.
        use_container_width: If True, use full container width.

    Returns:
        True if the button was clicked.
    """
    import base64

    # Convert data to base64
    if isinstance(data, str):
        b64_data = base64.b64encode(data.encode("utf-8")).decode("utf-8")
        mime = mime or "text/plain"
    elif isinstance(data, bytes):
        b64_data = base64.b64encode(data).decode("utf-8")
        mime = mime or "application/octet-stream"
    elif hasattr(data, "read"):
        content = data.read()
        if isinstance(content, str):
            b64_data = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        else:
            b64_data = base64.b64encode(content).decode("utf-8")
        mime = mime or "application/octet-stream"
    else:
        b64_data = base64.b64encode(str(data).encode("utf-8")).decode("utf-8")
        mime = mime or "text/plain"

    node = _emit_node(
        "download_button",
        {
            "label": label,
            "data": b64_data,
            "fileName": file_name or "download",
            "mime": mime,
            "help": help,
            "type": type,
            "icon": icon,
            "disabled": disabled,
            "useContainerWidth": use_container_width,
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
# st.select_slider
# ---------------------------------------------------------------------------

def select_slider(
    label: str,
    options: Sequence = (),
    value: Any | tuple[Any, Any] | None = None,
    format_func: Callable | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    disabled: bool = False,
    label_visibility: str = "visible",
    width: str | int = "stretch",
) -> Any | tuple[Any, Any]:
    """Display a slider with discrete options.

    Args:
        label: Widget label (supports Markdown).
        options: List of options to display.
        value: Default value or tuple for range selection.
        format_func: Function to format option labels.
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when value changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        disabled: If True, disable the widget.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        width: Widget width - "stretch" (default) or pixel value.

    Returns:
        Selected value or tuple of values for range selection.
    """
    raw_options = list(options)
    if not raw_options:
        return None

    display_labels = _format_options(raw_options, format_func)

    # Determine if range mode
    is_range = isinstance(value, tuple)

    # Get initial index/indices
    if is_range:
        start_idx = raw_options.index(value[0]) if value[0] in raw_options else 0
        end_idx = raw_options.index(value[1]) if value[1] in raw_options else len(raw_options) - 1
        default_indices = [start_idx, end_idx]
    else:
        if value is not None and value in raw_options:
            default_idx = raw_options.index(value)
        else:
            default_idx = 0
        default_indices = default_idx

    node = _emit_node(
        "select_slider",
        {
            "label": label,
            "options": display_labels,
            "value": default_indices,
            "isRange": is_range,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
            "width": width,
        },
        key=key,
        is_widget=True,
        no_rerun=True,
    )

    session = get_current_session()
    stored = session.widget_store.get(node.id, default_indices)

    if is_range:
        if isinstance(stored, list) and len(stored) == 2:
            idx1, idx2 = stored
            idx1 = max(0, min(idx1, len(raw_options) - 1))
            idx2 = max(0, min(idx2, len(raw_options) - 1))
            return WidgetValue((raw_options[idx1], raw_options[idx2]), node.id)
        return WidgetValue((raw_options[0], raw_options[-1]), node.id)
    else:
        if isinstance(stored, int) and 0 <= stored < len(raw_options):
            return WidgetValue(raw_options[stored], node.id)
        return WidgetValue(raw_options[0], node.id)


# ---------------------------------------------------------------------------
# st.file_uploader
# ---------------------------------------------------------------------------

def file_uploader(
    label: str,
    type: str | Sequence[str] | None = None,
    accept_multiple_files: bool = False,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    *,
    disabled: bool = False,
    label_visibility: str = "visible",
    width: str | int = "stretch",
    max_file_size_mb: int | None = None,
) -> Any:
    """Display a file uploader widget.

    Args:
        label: Widget label (supports Markdown).
        type: Allowed file extensions (e.g., ["png", "jpg"] or "csv").
        accept_multiple_files: If True, allow multiple files.
        key: Unique widget key.
        help: Tooltip text (supports Markdown).
        on_change: Callback when files change.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        disabled: If True, disable the widget.
        label_visibility: "visible" (default), "hidden", or "collapsed".
        width: Widget width - "stretch" (default) or pixel value.
        max_file_size_mb: Maximum accepted file size (MB) per file.
            If None, uses FASTLIT_MAX_UPLOAD_MB (default: 10).

    Returns:
        Uploaded file(s) or None.
    """
    # Normalize type to list
    if type is None:
        allowed_types = None
    elif isinstance(type, str):
        allowed_types = [type]
    else:
        allowed_types = list(type)

    max_size_bytes = (
        max(1, int(max_file_size_mb)) * 1024 * 1024
        if max_file_size_mb is not None
        else _max_upload_bytes()
    )

    node = _emit_node(
        "file_uploader",
        {
            "label": label,
            "allowedTypes": allowed_types,
            "acceptMultiple": accept_multiple_files,
            "maxSizeBytes": max_size_bytes,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
            "width": width,
        },
        key=key,
        is_widget=True,
    )

    session = get_current_session()
    stored = session.widget_store.get(node.id)

    if stored is None:
        return [] if accept_multiple_files else None

    # Convert stored data to UploadedFile objects
    if accept_multiple_files:
        if isinstance(stored, list):
            uploaded: list[UploadedFile] = []
            errors: list[str] = []
            for item in stored:
                file_obj, err = _make_uploaded_file(item, max_size_bytes)
                if file_obj is not None:
                    uploaded.append(file_obj)
                elif err:
                    errors.append(err)
            if errors:
                _emit_upload_warning(
                    "Some files were skipped: "
                    + "; ".join(errors[:3])
                    + ("; ..." if len(errors) > 3 else "")
                )
            return uploaded
        return []
    else:
        if stored:
            file_obj, err = _make_uploaded_file(stored, max_size_bytes)
            if err:
                _emit_upload_warning(err)
            return file_obj
        return None


def _emit_upload_warning(message: str) -> None:
    """Render a non-blocking warning in the app."""
    from fastlit.ui.status import warning as _warning
    _warning(message)


def _make_uploaded_file(
    data: dict,
    max_size_bytes: int,
) -> "tuple[UploadedFile | None, str | None]":
    """Create an UploadedFile object from stored data or return an error."""
    import base64

    if not isinstance(data, dict):
        return None, "Invalid uploaded file payload."

    name = data.get("name", "file")
    content_type = data.get("type", "application/octet-stream")
    b64_content = data.get("content", "")
    reported_size = data.get("size")
    if isinstance(reported_size, int) and reported_size > max_size_bytes:
        return None, (
            f"Uploaded file '{name}' exceeds max size "
            f"({reported_size} bytes > {max_size_bytes} bytes)."
        )
    if len(b64_content) > ((max_size_bytes + 2) // 3) * 4:
        return None, f"Uploaded file '{name}' exceeds max size before decoding."

    try:
        content = base64.b64decode(b64_content, validate=True) if b64_content else b""
    except Exception:
        return None, f"Uploaded file '{name}' is not valid base64."
    if len(content) > max_size_bytes:
        return None, (
            f"Uploaded file '{name}' exceeds max size "
            f"({len(content)} bytes > {max_size_bytes} bytes)."
        )

    return UploadedFile(name, content, content_type), None


class UploadedFile:
    """Represents an uploaded file."""

    def __init__(self, name: str, content: bytes, content_type: str):
        self.name = name
        self.type = content_type
        self.size = len(content)
        self._content = content
        self._pos = 0

    def read(self, size: int = -1) -> bytes:
        """Read content from the file."""
        if size < 0:
            result = self._content[self._pos:]
            self._pos = len(self._content)
        else:
            result = self._content[self._pos:self._pos + size]
            self._pos += len(result)
        return result

    def seek(self, pos: int) -> int:
        """Seek to a position in the file."""
        self._pos = max(0, min(pos, len(self._content)))
        return self._pos

    def tell(self) -> int:
        """Return current position in the file."""
        return self._pos

    def getvalue(self) -> bytes:
        """Get the entire file content."""
        return self._content

    def __repr__(self) -> str:
        return f"UploadedFile(name='{self.name}', size={self.size})"


# ---------------------------------------------------------------------------
# st.feedback
# ---------------------------------------------------------------------------

def feedback(
    sentiment_mapping: dict[int, str] | str | None = None,
    *,
    key: str | None = None,
    disabled: bool = False,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
) -> int | None:
    """Display a feedback widget (thumbs or stars).

    Args:
        sentiment_mapping: Either a dict mapping index to label,
            or a preset string: "thumbs" (default), "faces", "stars".
        key: Unique widget key.
        disabled: If True, disable the widget.
        on_change: Callback when selection changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.

    Returns:
        Index of the selected option, or None if nothing selected.
    """
    if sentiment_mapping is None:
        sentiment_mapping = "thumbs"

    if isinstance(sentiment_mapping, str):
        preset = sentiment_mapping
        options_map = None
    else:
        preset = "custom"
        options_map = {str(k): v for k, v in sentiment_mapping.items()}

    node = _emit_node(
        "feedback",
        {
            "preset": preset,
            "optionsMap": options_map,
            "disabled": disabled,
        },
        key=key,
        is_widget=True,
    )

    session = get_current_session()
    selected = session.widget_store.get(node.id)
    if selected is not None:
        _run_callback(on_change, args, kwargs)
        return int(selected)
    return None


# ---------------------------------------------------------------------------
# st.pills
# ---------------------------------------------------------------------------

def pills(
    label: str,
    options: Sequence,
    *,
    selection_mode: str = "single",
    default: Any | Sequence | None = None,
    format_func: Callable | None = None,
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> Any:
    """Display a pill selector widget.

    Args:
        label: Widget label.
        options: List of options.
        selection_mode: "single" (default) or "multi".
        default: Default selection(s).
        format_func: Function to format option labels.
        key: Unique widget key.
        help: Tooltip text.
        on_change: Callback when selection changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        disabled: If True, disable the widget.
        label_visibility: "visible" (default), "hidden", or "collapsed".

    Returns:
        Selected option (single mode) or list of options (multi mode).
    """
    raw_options = list(options)
    if not raw_options:
        return [] if selection_mode == "multi" else None

    display_labels = _format_options(raw_options, format_func)
    is_multi = selection_mode == "multi"

    # Compute default indices
    if default is None:
        default_indices = [] if is_multi else None
    elif is_multi:
        default_indices = [raw_options.index(d) for d in default if d in raw_options]
    else:
        default_indices = raw_options.index(default) if default in raw_options else None

    node = _emit_node(
        "pills",
        {
            "label": label,
            "options": display_labels,
            "selectionMode": selection_mode,
            "defaultIndices": default_indices,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
        },
        key=key,
        is_widget=True,
    )

    session = get_current_session()
    stored = session.widget_store.get(node.id, default_indices)

    if is_multi:
        if isinstance(stored, list):
            return WidgetValue([raw_options[i] for i in stored if 0 <= i < len(raw_options)], node.id)
        return WidgetValue([], node.id)
    else:
        if isinstance(stored, int) and 0 <= stored < len(raw_options):
            return WidgetValue(raw_options[stored], node.id)
        return WidgetValue(None, node.id)


# ---------------------------------------------------------------------------
# st.segmented_control
# ---------------------------------------------------------------------------

def segmented_control(
    label: str,
    options: Sequence,
    *,
    default: Any | None = None,
    format_func: Callable | None = None,
    selection_mode: str = "single",
    key: str | None = None,
    help: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    disabled: bool = False,
    label_visibility: str = "visible",
) -> Any:
    """Display a segmented control (button group) widget.

    Args:
        label: Widget label.
        options: List of options.
        default: Default selection.
        format_func: Function to format option labels.
        selection_mode: "single" (default) or "multi".
        key: Unique widget key.
        help: Tooltip text.
        on_change: Callback when selection changes.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        disabled: If True, disable the widget.
        label_visibility: "visible" (default), "hidden", or "collapsed".

    Returns:
        Selected option (single mode) or list of options (multi mode).
    """
    raw_options = list(options)
    if not raw_options:
        return [] if selection_mode == "multi" else None

    display_labels = _format_options(raw_options, format_func)
    is_multi = selection_mode == "multi"

    if default is None:
        default_idx = [] if is_multi else None
    elif is_multi:
        default_idx = [raw_options.index(d) for d in default if d in raw_options]
    else:
        default_idx = raw_options.index(default) if default in raw_options else 0

    node = _emit_node(
        "segmented_control",
        {
            "label": label,
            "options": display_labels,
            "selectionMode": selection_mode,
            "defaultIndex": default_idx,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
        },
        key=key,
        is_widget=True,
    )

    session = get_current_session()
    stored = session.widget_store.get(node.id, default_idx)

    if is_multi:
        if isinstance(stored, list):
            return WidgetValue([raw_options[i] for i in stored if 0 <= i < len(raw_options)], node.id)
        return WidgetValue([], node.id)
    else:
        if isinstance(stored, int) and 0 <= stored < len(raw_options):
            return WidgetValue(raw_options[stored], node.id)
        return WidgetValue(None, node.id)


# ---------------------------------------------------------------------------
# st.camera_input
# ---------------------------------------------------------------------------

def camera_input(
    label: str,
    *,
    key: str | None = None,
    help: str | None = None,
    disabled: bool = False,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    label_visibility: str = "visible",
) -> "UploadedFile | None":
    """Display a camera input widget for capturing photos.

    Args:
        label: Widget label.
        key: Unique widget key.
        help: Tooltip text.
        disabled: If True, disable the widget.
        on_change: Callback when photo is captured.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        label_visibility: "visible" (default), "hidden", or "collapsed".

    Returns:
        Captured photo as UploadedFile, or None.
    """
    node = _emit_node(
        "camera_input",
        {
            "label": label,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
        },
        key=key,
        is_widget=True,
    )

    session = get_current_session()
    stored = session.widget_store.get(node.id)

    if stored and isinstance(stored, dict):
        max_size_bytes = _max_upload_bytes()
        file_obj, err = _make_uploaded_file(stored, max_size_bytes)
        if err:
            _emit_upload_warning(err)
            return None
        if file_obj is not None:
            _run_callback(on_change, args, kwargs)
        return file_obj
    return None


# ---------------------------------------------------------------------------
# st.audio_input
# ---------------------------------------------------------------------------

def audio_input(
    label: str,
    *,
    key: str | None = None,
    help: str | None = None,
    disabled: bool = False,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    label_visibility: str = "visible",
) -> "UploadedFile | None":
    """Display an audio recorder widget.

    Args:
        label: Widget label.
        key: Unique widget key.
        help: Tooltip text.
        disabled: If True, disable the widget.
        on_change: Callback when recording is captured.
        args: Arguments to pass to the callback.
        kwargs: Keyword arguments to pass to the callback.
        label_visibility: "visible" (default), "hidden", or "collapsed".

    Returns:
        Recorded audio as UploadedFile, or None.
    """
    node = _emit_node(
        "audio_input",
        {
            "label": label,
            "help": help,
            "disabled": disabled,
            "labelVisibility": label_visibility,
        },
        key=key,
        is_widget=True,
    )

    session = get_current_session()
    stored = session.widget_store.get(node.id)

    if stored and isinstance(stored, dict):
        max_size_bytes = _max_upload_bytes()
        file_obj, err = _make_uploaded_file(stored, max_size_bytes)
        if err:
            _emit_upload_warning(err)
            return None
        if file_obj is not None:
            _run_callback(on_change, args, kwargs)
        return file_obj
    return None
