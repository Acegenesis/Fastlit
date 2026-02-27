"""Fastlit — Streamlit-compatible, blazing fast, Python-first.

Usage:
    import fastlit as st
    st.title("Hello")
"""

from __future__ import annotations

from fastlit.ui.text import (
    title, header, subheader, markdown, write, text, metric, json, code,
    caption, latex, echo, html, help, write_stream, badge,
)
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
    feedback,
    pills,
    segmented_control,
    camera_input,
    audio_input,
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
    Page,
    switch_page,
    set_sidebar_state,
)
from fastlit.ui.chat import chat_message, chat_input
from fastlit.ui.fragment import fragment
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
from fastlit.ui.state import _get_session_state, _QueryParamsProxy
from fastlit.ui.secrets import _SecretsProxy
from fastlit.ui.context import _ContextProxy
from fastlit.runtime.session import RerunException, StopException
from fastlit.runtime.context import get_current_session, run_with_session_context, run_in_thread
from fastlit.cache import cache_data, cache_resource
from fastlit.connections import connection
import fastlit.connections as connections
import fastlit.components as components
from fastlit.ui.user import user


# --- Lifecycle hooks (B3) ---

def on_startup(fn):
    """Decorator to register a function to call on ASGI startup.

    Example::

        @st.on_startup
        def init_db():
            db_pool = create_pool(...)
    """
    from fastlit.server.app import register_startup
    register_startup(fn)
    return fn


def on_shutdown(fn):
    """Decorator to register a function to call on ASGI shutdown.

    Example::

        @st.on_shutdown
        async def close_db():
            await db_pool.close()
    """
    from fastlit.server.app import register_shutdown
    register_shutdown(fn)
    return fn


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
query_params = _QueryParamsProxy()
secrets = _SecretsProxy()
context = _ContextProxy()


def require_login() -> None:
    """Redirect to the login page if the current user is not authenticated.

    Call this at the top of any page that requires authentication::

        import fastlit as st

        st.require_login()
        st.write(f"Welcome, {st.user.name}!")

    When auth is not configured (no ``[auth]`` section in ``secrets.toml``),
    this function does nothing and the app works without authentication.
    """
    if not user.is_logged_in:
        from fastlit.runtime.session import _RequireLoginException
        raise _RequireLoginException()


def logout() -> None:
    """Clear the authentication session and redirect to the logout endpoint.

    Example::

        if st.button("Sign out"):
            st.logout()
    """
    switch_page("/auth/logout")


def rerun(scope: str = "full") -> None:
    """Stop the current run and trigger a rerun.

    Args:
        scope: "full" (default) or "fragment".
    """
    if scope not in {"full", "fragment"}:
        raise ValueError("scope must be 'full' or 'fragment'")
    raise RerunException(scope=scope)


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
    "html",
    "help",
    "write_stream",
    "badge",
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
    "feedback",
    "pills",
    "segmented_control",
    "camera_input",
    "audio_input",
    # Chat
    "chat_message",
    "chat_input",
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
    "Page",
    "switch_page",
    "set_sidebar_state",
    # State
    "session_state",
    "query_params",
    "rerun",
    "stop",
    "set_page_config",
    # Runtime context & secrets
    "secrets",
    "context",
    # Threading & lifecycle
    "run_in_thread",
    "run_with_session_context",
    "on_startup",
    "on_shutdown",
    # Cache
    "cache_data",
    "cache_resource",
    # Connections
    "connection",
    "connections",
    # Components
    "components",
    # Auth
    "user",
    "require_login",
    "logout",
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
