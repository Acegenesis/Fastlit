"""Fastlit — Streamlit-compatible, blazing fast, Python-first.

Usage:
    import fastlit as st
    st.title("Hello")
"""

from __future__ import annotations

from fastlit.ui.text import title, header, subheader, markdown, write, text, metric, json, code, caption, latex, echo
from fastlit.ui.widgets import (
    button,
    slider,
    text_input,
    text_area,
    checkbox,
    selectbox,
    radio,
    number_input,
    multiselect,
    date_input,
    time_input,
    toggle,
    color_picker,
    link_button,
    page_link,
    download_button,
    select_slider,
    file_uploader,
    UploadedFile,
)
from fastlit.ui.layout import (
    sidebar,
    columns,
    container,
    tabs,
    expander,
    empty,
    form,
    form_submit_button,
    dialog,
    popover,
    divider,
    navigation,
)
from fastlit.ui.dataframe import dataframe, data_editor, table
from fastlit.ui import column_config
from fastlit.ui.charts import (
    line_chart,
    bar_chart,
    area_chart,
    scatter_chart,
    map,
    plotly_chart,
    altair_chart,
    vega_lite_chart,
    pyplot,
    bokeh_chart,
    graphviz_chart,
    pydeck_chart,
)
from fastlit.ui.media import (
    image,
    audio,
    video,
    logo,
    pdf,
)
from fastlit.ui.status import (
    success,
    info,
    warning,
    error,
    exception,
    progress,
    spinner,
    status,
    toast,
    balloons,
    snow,
)
from fastlit.ui.state import _get_session_state
from fastlit.runtime.session import RerunException, StopException
from fastlit.runtime.context import get_current_session
from fastlit.cache import cache_data, cache_resource


# --- session_state as a module-level property ---
# We use a trick: a class instance whose attribute access delegates to
# the active session's state dict.


class _SessionStateProxy:
    """Proxy that forwards attribute access to the active session's state."""

    def __getattr__(self, name: str):
        return getattr(_get_session_state(), name)

    def __setattr__(self, name: str, value):
        setattr(_get_session_state(), name, value)

    def __delattr__(self, name: str):
        delattr(_get_session_state(), name)

    def __contains__(self, key):
        return key in _get_session_state()

    def __getitem__(self, key):
        return _get_session_state()[key]

    def __setitem__(self, key, value):
        _get_session_state()[key] = value

    def __delitem__(self, key):
        del _get_session_state()[key]

    def clear(self):
        _get_session_state().clear()

    def get(self, key, default=None):
        return _get_session_state().get(key, default)

    def keys(self):
        return _get_session_state().keys()

    def values(self):
        return _get_session_state().values()

    def items(self):
        return _get_session_state().items()

    def pop(self, key, *args):
        return _get_session_state().pop(key, *args)

    def setdefault(self, key, default=None):
        return _get_session_state().setdefault(key, default)

    def update(self, *args, **kwargs):
        _get_session_state().update(*args, **kwargs)

    def __len__(self):
        return len(_get_session_state())

    def __iter__(self):
        return iter(_get_session_state())

    def __bool__(self):
        return bool(_get_session_state())

    def __repr__(self):
        try:
            return repr(_get_session_state())
        except RuntimeError:
            return "SessionState(<no active session>)"


session_state = _SessionStateProxy()


def rerun() -> None:
    """Stop the current script run and trigger a rerun."""
    raise RerunException()


def stop() -> None:
    """Stop execution of the script.

    After calling st.stop(), no more elements will be rendered.
    """
    raise StopException()


def set_page_config(
    page_title: str | None = None,
    page_icon: str | None = None,
    layout: str = "centered",
    initial_sidebar_state: str = "auto",
    menu_items: dict | None = None,
) -> None:
    """Configure the page settings.

    Must be called before any other Streamlit commands.

    Args:
        page_title: The page title shown in the browser tab.
        page_icon: The page icon (emoji or image URL).
        layout: Page layout ("centered" or "wide").
        initial_sidebar_state: Initial sidebar state ("auto", "expanded", "collapsed").
        menu_items: Custom menu items dict with keys "Get Help", "Report a bug", "About".
    """
    from fastlit.ui.base import _emit_node

    _emit_node(
        "page_config",
        {
            "pageTitle": page_title,
            "pageIcon": page_icon,
            "layout": layout,
            "initialSidebarState": initial_sidebar_state,
            "menuItems": menu_items,
        },
    )


__all__ = [
    # Text elements
    "title",
    "header",
    "subheader",
    "markdown",
    "write",
    "text",
    "metric",
    "json",
    "code",
    "caption",
    "latex",
    "echo",
    # Input widgets
    "button",
    "slider",
    "text_input",
    "text_area",
    "checkbox",
    "selectbox",
    "radio",
    "number_input",
    "multiselect",
    "date_input",
    "time_input",
    "toggle",
    "color_picker",
    "link_button",
    "page_link",
    "download_button",
    "select_slider",
    "file_uploader",
    "UploadedFile",
    # Data display
    "dataframe",
    "data_editor",
    "table",
    "column_config",
    # Charts
    "line_chart",
    "bar_chart",
    "area_chart",
    "scatter_chart",
    "map",
    "plotly_chart",
    "altair_chart",
    "vega_lite_chart",
    "pyplot",
    "bokeh_chart",
    "graphviz_chart",
    "pydeck_chart",
    # Media
    "image",
    "audio",
    "video",
    "logo",
    "pdf",
    # Layout
    "sidebar",
    "columns",
    "container",
    "tabs",
    "expander",
    "empty",
    "form",
    "form_submit_button",
    "dialog",
    "popover",
    "divider",
    "navigation",
    # State
    "session_state",
    "rerun",
    "stop",
    "set_page_config",
    # Cache
    "cache_data",
    "cache_resource",
    # Status elements
    "success",
    "info",
    "warning",
    "error",
    "exception",
    "progress",
    "spinner",
    "status",
    "toast",
    "balloons",
    "snow",
]
