"""Layout containers — Streamlit-compatible signatures.

st.sidebar, st.columns, st.container, st.tabs, st.expander,
st.form, st.form_submit_button, st.popover, st.empty, st.divider.
"""

from __future__ import annotations

from typing import Callable, Sequence

from fastlit.runtime.context import get_current_session
from fastlit.runtime.tree import UINode
from fastlit.ui.base import _make_id, _emit_node


# ---------------------------------------------------------------------------
# Base Container Proxy — eliminates duplicate __enter__/__exit__/__getattr__
# ---------------------------------------------------------------------------

class _ContainerProxy:
    """Base class for container context managers.

    Consolidates the common pattern of:
    - __enter__: optionally append node to tree, push as container
    - __exit__: pop container from tree
    - __getattr__: wrap st.* functions to run within container context
    """

    _node: UINode
    _append_on_enter: bool = True   # Whether to append node to tree on enter
    _clear_on_enter: bool = False   # Whether to clear children on enter
    _clear_on_call: bool = False    # Whether to clear children when calling methods
    _name: str = "Container"        # Name for error messages

    def __init__(self, node: UINode) -> None:
        self._node = node

    def __enter__(self):
        session = get_current_session()
        tree = session.current_tree
        if self._clear_on_enter:
            self._node.children.clear()
        if self._append_on_enter:
            tree.append(self._node)
        tree.push_container(self._node)
        return self

    def __exit__(self, *args):
        get_current_session().current_tree.pop_container()

    def __getattr__(self, name: str):
        import fastlit as st

        func = getattr(st, name, None)
        if func is None:
            raise AttributeError(f"{self._name} has no attribute '{name}'")

        def wrapper(*a, **kw):
            with self:
                if self._clear_on_call:
                    self._node.children.clear()
                return func(*a, **kw)
        return wrapper


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _get_or_create_sidebar() -> UINode:
    """Return the shared sidebar node for this run, creating it if needed."""
    session = get_current_session()
    tree = session.current_tree
    if tree._sidebar is not None:
        return tree._sidebar
    node = UINode(type="sidebar", id="sidebar:0", props={})
    tree.root.children.insert(0, node)
    tree._sidebar = node
    return node


class _SidebarProxy:
    """Proxy object so that both ``st.sidebar.title(...)`` and
    ``with st.sidebar:`` work like in Streamlit."""

    def __enter__(self):
        node = _get_or_create_sidebar()
        get_current_session().current_tree.push_container(node)
        return self

    def __exit__(self, *args):
        get_current_session().current_tree.pop_container()

    def __getattr__(self, name: str):
        import fastlit as st

        func = getattr(st, name, None)
        if func is None:
            raise AttributeError(f"st.sidebar has no attribute '{name}'")

        def wrapper(*a, **kw):
            with self:
                return func(*a, **kw)
        return wrapper


sidebar = _SidebarProxy()


# ---------------------------------------------------------------------------
# Columns — st.columns(spec, *, gap="small", vertical_alignment="top",
#                        border=False)
# ---------------------------------------------------------------------------

class Column(_ContainerProxy):
    """A single column returned by st.columns(). Used as a context manager."""

    _append_on_enter = False  # Parent columns node handles appending
    _name = "Column"

    def __init__(self, node: UINode, parent_node: UINode) -> None:
        super().__init__(node)
        self._parent = parent_node


def columns(
    spec: int | Sequence[int | float],
    *,
    gap: str | None = "small",
    vertical_alignment: str = "top",
    border: bool = False,
    key: str | None = None,
) -> list[Column]:
    """Create columns. ``spec`` can be an int (equal widths) or a list of relative widths."""
    session = get_current_session()

    if isinstance(spec, int):
        widths = [1] * spec
    else:
        widths = list(spec)

    total = sum(widths)
    cols_id = _make_id("columns", key)
    cols_node = UINode(
        type="columns",
        id=cols_id,
        props={
            "widths": widths,
            "total": total,
            "gap": gap,
            "verticalAlignment": vertical_alignment,
            "border": border,
        },
    )
    session.current_tree.append(cols_node)
    session.current_tree.push_container(cols_node)

    result = []
    for i, w in enumerate(widths):
        col_id = f"{cols_id}:col:{i}"
        col_node = UINode(
            type="column",
            id=col_id,
            props={"width": w, "index": i, "border": border},
        )
        cols_node.children.append(col_node)
        result.append(Column(col_node, cols_node))

    session.current_tree.pop_container()
    return result


# ---------------------------------------------------------------------------
# Tabs — st.tabs(tabs, *, default=None)
# ---------------------------------------------------------------------------

class Tab(_ContainerProxy):
    """A single tab returned by st.tabs(). Used as a context manager."""

    _append_on_enter = False  # Parent tabs node handles appending
    _name = "Tab"


def tabs(
    tab_labels: Sequence[str],
    *,
    default: str | None = None,
    key: str | None = None,
) -> list[Tab]:
    """Create tabs with the given labels."""
    session = get_current_session()
    labels_list = list(tab_labels)

    default_index = 0
    if default is not None and default in labels_list:
        default_index = labels_list.index(default)

    tabs_id = _make_id("tabs", key)
    tabs_node = UINode(
        type="tabs",
        id=tabs_id,
        props={"labels": labels_list, "defaultIndex": default_index},
    )
    session.current_tree.append(tabs_node)
    session.current_tree.push_container(tabs_node)

    result = []
    for i, label in enumerate(labels_list):
        tab_id = f"{tabs_id}:tab:{i}"
        tab_node = UINode(type="tab", id=tab_id, props={"label": label, "index": i})
        tabs_node.children.append(tab_node)
        result.append(Tab(tab_node))

    session.current_tree.pop_container()
    return result


# ---------------------------------------------------------------------------
# Expander — st.expander(label, expanded=False, *, icon=None)
# ---------------------------------------------------------------------------

class Expander(_ContainerProxy):
    """An expandable/collapsible section. Used as a context manager."""

    _name = "Expander"


def expander(
    label: str,
    expanded: bool = False,
    *,
    icon: str | None = None,
    key: str | None = None,
) -> Expander:
    """Create a collapsible expander section."""
    exp_id = _make_id("expander", key)
    node = UINode(
        type="expander",
        id=exp_id,
        props={"label": label, "expanded": expanded, "icon": icon},
    )
    return Expander(node)


# ---------------------------------------------------------------------------
# Container — st.container(*, border=None, key=None, height=None)
# ---------------------------------------------------------------------------

class Container(_ContainerProxy):
    """A generic container. Used as a context manager."""

    _name = "Container"


def container(
    *,
    border: bool | None = None,
    key: str | None = None,
    height: int | str | None = None,
) -> Container:
    """Insert a multi-element container."""
    cid = _make_id("container", key)
    node = UINode(
        type="container",
        id=cid,
        props={"border": border or False, "height": height},
    )
    return Container(node)


# ---------------------------------------------------------------------------
# Empty — st.empty()
# ---------------------------------------------------------------------------

class Empty(_ContainerProxy):
    """A single-element placeholder that can be updated or cleared.

    Supports ``with st.empty():`` and direct method calls like
    ``placeholder.write(...)``.
    """

    _append_on_enter = False  # Already appended in empty() function
    _clear_on_enter = True    # Clear children when entering context
    _clear_on_call = True     # Clear children when calling methods
    _name = "Empty"

    def empty(self):
        """Clear the placeholder."""
        self._node.children.clear()


def empty() -> Empty:
    """Insert a single-element container that can be updated/cleared."""
    session = get_current_session()
    eid = _make_id("empty")
    node = UINode(type="empty", id=eid, props={})
    session.current_tree.append(node)
    return Empty(node)


# ---------------------------------------------------------------------------
# Form — st.form(key, clear_on_submit=False, *, enter_to_submit=True,
#                  border=True)
# ---------------------------------------------------------------------------

class Form(_ContainerProxy):
    """A form container that batches widget values until submitted."""

    _name = "Form"


def form(
    key: str,
    clear_on_submit: bool = False,
    *,
    enter_to_submit: bool = True,
    border: bool = True,
) -> Form:
    """Create a form that batches widget interactions."""
    fid = f"form:{key}"
    node = UINode(
        type="form",
        id=fid,
        props={
            "formKey": key,
            "clearOnSubmit": clear_on_submit,
            "enterToSubmit": enter_to_submit,
            "border": border,
        },
    )
    return Form(node)


def form_submit_button(
    label: str = "Submit",
    *,
    help: str | None = None,
    on_click: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
    type: str = "secondary",
    disabled: bool = False,
    use_container_width: bool = False,
    key: str | None = None,
) -> bool:
    """Display a form submit button. Returns True when the form was submitted."""
    node = _emit_node(
        "form_submit_button",
        {
            "label": label,
            "help": help,
            "type": type,
            "disabled": disabled,
            "useContainerWidth": use_container_width,
        },
        key=key,
        is_widget=True,
    )
    session = get_current_session()
    clicked = session.widget_store.pop(node.id, False)
    if clicked and on_click is not None:
        on_click(*(args or ()), **(kwargs or {}))
    return bool(clicked)


# ---------------------------------------------------------------------------
# Dialog — @st.dialog(title, *, width="small")
# ---------------------------------------------------------------------------

def dialog(
    title: str,
    *,
    width: str = "small",
    dismissible: bool = True,
) -> Callable:
    """Decorator that wraps a function in a modal dialog.

    Usage::

        @st.dialog("My Dialog")
        def my_dialog():
            st.write("Hello from dialog")
            if st.button("Close"):
                st.rerun()
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            session = get_current_session()
            did = _make_id("dialog")
            node = UINode(
                type="dialog",
                id=did,
                props={
                    "title": title,
                    "width": width,
                    "dismissible": dismissible,
                    "open": True,
                },
            )
            tree = session.current_tree
            tree.append(node)
            tree.push_container(node)
            try:
                result = func(*args, **kwargs)
            finally:
                tree.pop_container()
            return result
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Popover — st.popover(label, *, help=None, disabled=False)
# ---------------------------------------------------------------------------

class Popover(_ContainerProxy):
    """A popover container triggered by a button."""

    _name = "Popover"


def popover(
    label: str,
    *,
    type: str = "secondary",
    help: str | None = None,
    disabled: bool = False,
    use_container_width: bool | None = None,
    key: str | None = None,
) -> Popover:
    """Create a popover element triggered by a button."""
    pid = _make_id("popover", key)
    node = UINode(
        type="popover",
        id=pid,
        props={
            "label": label,
            "type": type,
            "help": help,
            "disabled": disabled or False,
            "useContainerWidth": use_container_width or False,
        },
    )
    return Popover(node)


# ---------------------------------------------------------------------------
# Divider — st.divider()
# ---------------------------------------------------------------------------

def divider() -> None:
    """Display a horizontal rule."""
    _emit_node("divider", {})


# ---------------------------------------------------------------------------
# set_sidebar_state — st.set_sidebar_state(state)
# ---------------------------------------------------------------------------

def set_sidebar_state(state: str) -> None:
    """Set the sidebar state programmatically.

    Args:
        state: "collapsed" or "expanded".

    The node is always emitted at the root level so App.tsx can find it
    regardless of what container is currently active.
    """
    session = get_current_session()
    node_id = "k:sidebar_state"  # stable ID — only one sidebar state at a time
    node = UINode(type="sidebar_state", id=node_id, props={"state": state})
    session.current_tree.root.children.append(node)


# ---------------------------------------------------------------------------
# switch_page — st.switch_page(page)
# ---------------------------------------------------------------------------

def switch_page(page: str) -> None:
    """Switch to a different page programmatically.

    This stops the current script and reruns with the target page selected.

    Args:
        page: The name of the page to switch to (must match a page in st.navigation).
    """
    from fastlit.runtime.session import SwitchPageException
    raise SwitchPageException(page)


# ---------------------------------------------------------------------------
# Navigation — st.navigation(pages, *, key=None)
# ---------------------------------------------------------------------------

def navigation(
    pages: Sequence[str],
    *,
    key: str | None = None,
) -> str:
    """Display a navigation menu with clickable text links.

    Returns the label of the currently selected page.
    """
    opts = list(pages)
    node = _emit_node(
        "navigation",
        {"pages": opts, "index": 0},
        key=key,
        is_widget=True,
    )
    session = get_current_session()
    stored = session.widget_store.get(node.id)
    if stored is not None and isinstance(stored, int) and 0 <= stored < len(opts):
        node.props["index"] = stored
        return opts[stored]
    return opts[0] if opts else ""
