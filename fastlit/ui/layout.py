"""Layout containers: st.sidebar, st.columns, st.tabs, st.expander."""

from __future__ import annotations

from typing import Any, Sequence

from fastlit.runtime.containers import container_context
from fastlit.runtime.context import get_current_session
from fastlit.runtime.tree import UINode
from fastlit.ui.base import _make_id


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _get_or_create_sidebar() -> UINode:
    """Return the shared sidebar node for this run, creating it if needed."""
    session = get_current_session()
    tree = session.current_tree
    # Check if sidebar already exists as a child of root
    for child in tree.root.children:
        if child.type == "sidebar":
            return child
    # Create it
    node = UINode(type="sidebar", id="sidebar:0", props={})
    tree.root.children.insert(0, node)  # sidebar always first child
    return node


class _SidebarProxy:
    """Proxy object so that both `st.sidebar.title(...)` and
    `with st.sidebar:` work like in Streamlit."""

    def __enter__(self):
        session = get_current_session()
        node = _get_or_create_sidebar()
        session.current_tree.push_container(node)
        return self

    def __exit__(self, *args):
        session = get_current_session()
        session.current_tree.pop_container()

    # Forward st.* calls so st.sidebar.title("x") works
    def __getattr__(self, name: str):
        import fastlit as st

        func = getattr(st, name, None)
        if func is None:
            raise AttributeError(f"st.sidebar has no attribute '{name}'")

        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


sidebar = _SidebarProxy()


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------

class Column:
    """A single column returned by st.columns(). Used as a context manager."""

    def __init__(self, node: UINode, parent_node: UINode) -> None:
        self._node = node
        self._parent = parent_node

    def __enter__(self):
        session = get_current_session()
        session.current_tree.push_container(self._node)
        return self

    def __exit__(self, *args):
        session = get_current_session()
        session.current_tree.pop_container()

    # Forward st.* calls so col.write("x") works
    def __getattr__(self, name: str):
        import fastlit as st

        func = getattr(st, name, None)
        if func is None:
            raise AttributeError(f"Column has no attribute '{name}'")

        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


def columns(spec: int | Sequence[int], *, key: str | None = None) -> list[Column]:
    """Create columns. `spec` can be an int (equal widths) or a list of relative widths."""
    session = get_current_session()

    if isinstance(spec, int):
        widths = [1] * spec
    else:
        widths = list(spec)

    total = sum(widths)
    cols_id = _make_id("columns", key)
    cols_node = UINode(type="columns", id=cols_id, props={"widths": widths, "total": total})
    session.current_tree.append(cols_node)
    session.current_tree.push_container(cols_node)

    result = []
    for i, w in enumerate(widths):
        col_id = f"{cols_id}:col:{i}"
        col_node = UINode(type="column", id=col_id, props={"width": w, "index": i})
        cols_node.children.append(col_node)
        result.append(Column(col_node, cols_node))

    session.current_tree.pop_container()
    return result


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

class Tab:
    """A single tab returned by st.tabs(). Used as a context manager."""

    def __init__(self, node: UINode) -> None:
        self._node = node

    def __enter__(self):
        session = get_current_session()
        session.current_tree.push_container(self._node)
        return self

    def __exit__(self, *args):
        session = get_current_session()
        session.current_tree.pop_container()

    # Forward st.* calls
    def __getattr__(self, name: str):
        import fastlit as st

        func = getattr(st, name, None)
        if func is None:
            raise AttributeError(f"Tab has no attribute '{name}'")

        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


def tabs(labels: Sequence[str], *, key: str | None = None) -> list[Tab]:
    """Create tabs with the given labels."""
    session = get_current_session()
    labels_list = list(labels)

    tabs_id = _make_id("tabs", key)
    tabs_node = UINode(type="tabs", id=tabs_id, props={"labels": labels_list})
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
# Expander
# ---------------------------------------------------------------------------

class Expander:
    """An expandable/collapsible section. Used as a context manager."""

    def __init__(self, node: UINode) -> None:
        self._node = node

    def __enter__(self):
        session = get_current_session()
        tree = session.current_tree
        tree.append(self._node)
        tree.push_container(self._node)
        return self

    def __exit__(self, *args):
        session = get_current_session()
        session.current_tree.pop_container()

    # Forward st.* calls
    def __getattr__(self, name: str):
        import fastlit as st

        func = getattr(st, name, None)
        if func is None:
            raise AttributeError(f"Expander has no attribute '{name}'")

        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


def expander(label: str, *, expanded: bool = False, key: str | None = None) -> Expander:
    """Create a collapsible expander section."""
    exp_id = _make_id("expander", key)
    node = UINode(type="expander", id=exp_id, props={"label": label, "expanded": expanded})
    return Expander(node)
