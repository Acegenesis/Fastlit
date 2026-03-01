"""Layout containers — Streamlit-compatible signatures.

st.sidebar, st.columns, st.container, st.tabs, st.expander,
st.form, st.form_submit_button, st.popover, st.empty, st.divider.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from fastlit.runtime.context import get_current_session
from fastlit.runtime.page_discovery import discover_pages
from fastlit.runtime.navigation_slug import slugify_page_token
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

    @staticmethod
    def _is_attached(root: UINode, target: UINode) -> bool:
        stack = [root]
        while stack:
            node = stack.pop()
            if node is target:
                return True
            stack.extend(node.children)
        return False

    def __enter__(self):
        session = get_current_session()
        tree = session.current_tree
        if self._clear_on_enter:
            self._node.children.clear()
        if self._append_on_enter:
            # Avoid appending the same container node multiple times, even if
            # the current container changed since first attachment.
            already_attached = self._is_attached(tree.root, self._node)
            if not already_attached and tree.current_container is not self._node:
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
            session = get_current_session()
            tree = session.current_tree

            # If we're already inside this container context, avoid re-entering
            # it; re-entry can duplicate nodes in the tree.
            if tree.current_container is self._node:
                if self._clear_on_call:
                    self._node.children.clear()
                return func(*a, **kw)

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

def _slugify_page(value: str) -> str:
    return slugify_page_token(value)


@dataclass
class Page:
    """Multi-page app page definition.

    Use ``page.run()`` to render the selected page inside a global layout.
    """

    path: str
    title: str | None = None
    icon: str | None = None
    url_path: str | None = None
    default: bool = False

    def __post_init__(self) -> None:
        if self.title is None:
            self.title = Path(self.path).stem.replace("_", " ").title()
        if self.url_path is None:
            self.url_path = _slugify_page(self.title or self.path)

    def run(self) -> None:
        """Render this page inline inside the current app layout."""
        session = get_current_session()
        script_path = Path(self.path)
        base_script = getattr(session, "entry_script_path", session.script_path)
        base_dir = Path(base_script).resolve().parent if base_script else Path.cwd()
        if not script_path.is_absolute():
            script_path = (base_dir / script_path).resolve()
        else:
            script_path = script_path.resolve()
        script_path_str = str(script_path)
        if script_path_str in getattr(session, "_inline_rendered_scripts", set()):
            return
        session.run_inline_page_script(script_path_str)


def switch_page(page: str | Page) -> None:
    """Switch to a different page programmatically.

    This stops the current script and reruns with the target page selected.

    Args:
        page: The page name/slug (or Page object) to switch to.
    """
    from fastlit.runtime.session import SwitchPageException

    if isinstance(page, Page):
        target = page.url_path or page.title or page.path
    else:
        target = page
    raise SwitchPageException(str(target))


# ---------------------------------------------------------------------------
# Navigation — st.navigation(pages=None, *, key=None)
# ---------------------------------------------------------------------------

def navigation(
    pages: Sequence[str | Page] | None = None,
    *,
    key: str | None = None,
) -> str | Page:
    """Display a navigation menu with clickable text links.

    When ``pages`` is omitted, Fastlit auto-discovers ``*.py`` files inside a
    sibling ``pages/`` directory next to the app entry script. Page files can
    define sidebar metadata with ``PAGE_CONFIG`` or constants such as
    ``PAGE_TITLE``, ``PAGE_ICON``, ``PAGE_ORDER``, ``PAGE_DEFAULT``,
    ``PAGE_HIDDEN``, and ``PAGE_URL_PATH``. In that auto-discovery mode, the
    selected page is rendered implicitly inside the entry script layout.

    Returns the selected page label (str pages) or Page object (Page pages).
    When Page objects are used, call ``selected_page.run()`` to render the page
    inline inside the current script and keep a global layout around it.
    """
    session = get_current_session()
    auto_discovered_pages = pages is None
    if auto_discovered_pages:
        discovered = discover_pages(getattr(session, "entry_script_path", session.script_path))
        if not discovered:
            raise ValueError(
                "st.navigation() could not auto-discover any pages. "
                "Create a sibling 'pages/' directory next to your app entry "
                "script, or pass an explicit pages list."
            )
        opts: list[str | Page] = [
            Page(
                path=str(page.path),
                title=page.title,
                icon=page.icon,
                url_path=page.url_path,
                default=page.default,
            )
            for page in discovered
        ]
    else:
        opts = list(pages)
    if not opts:
        return ""

    base_script = getattr(session, "entry_script_path", session.script_path)
    base_dir = Path(base_script).resolve().parent if base_script else Path.cwd()
    labels: list[str] = []
    icons: list[str | None] = []
    url_paths: list[str] = []
    values: list[str | Page] = []
    page_scripts: dict[int, str] = {}
    default_idx = 0

    for i, item in enumerate(opts):
        if isinstance(item, Page):
            label = item.title or Path(item.path).stem
            labels.append(label)
            icons.append(item.icon)
            url_paths.append(item.url_path or _slugify_page(label))
            values.append(item)

            script_path = Path(item.path)
            if not script_path.is_absolute():
                script_path = (base_dir / script_path).resolve()
            else:
                script_path = script_path.resolve()
            page_scripts[i] = str(script_path)

            if item.default and default_idx == 0:
                default_idx = i
        else:
            label = str(item)
            labels.append(label)
            icons.append(None)
            url_paths.append(_slugify_page(label))
            values.append(label)

    node = _emit_node(
        "navigation",
        {
            "pages": labels,
            "icons": icons,
            "urlPaths": url_paths,
            "index": default_idx,
        },
        key=key,
        is_widget=True,
    )

    session.register_navigation_pages(
        nav_id=node.id,
        labels=labels,
        url_paths=url_paths,
        page_scripts=page_scripts,
        default_index=default_idx,
    )

    selected_idx = default_idx
    stored = session.widget_store.get(node.id)
    if stored is not None and isinstance(stored, int) and 0 <= stored < len(labels):
        selected_idx = stored
    node.props["index"] = selected_idx

    selected_script = page_scripts.get(selected_idx)
    if (
        auto_discovered_pages
        and selected_script is not None
        and session.script_path == getattr(session, "entry_script_path", session.script_path)
        and selected_script not in getattr(session, "_inline_rendered_scripts", set())
    ):
        current_container = session.current_tree.current_container
        session.run_inline_page_script(
            selected_script,
            root_level=current_container.type == "sidebar",
        )
    if (
        selected_script is not None
        and selected_script != session.script_path
        and session.script_path != getattr(session, "entry_script_path", session.script_path)
    ):
        # Keep selected index and rerun into the selected page script.
        session._switch_to_page_index(selected_idx, node.id)
        from fastlit.runtime.session import RerunException

        raise RerunException(scope="full")

    return values[selected_idx]
