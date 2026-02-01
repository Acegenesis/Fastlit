"""Container context management for layout widgets (sidebar, columns, tabs, expander)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from fastlit.runtime.context import get_current_session
from fastlit.runtime.tree import UINode


@contextmanager
def container_context(node: UINode) -> Generator[None, None, None]:
    """Push a container node onto the tree stack, yield, then pop."""
    session = get_current_session()
    tree = session.current_tree
    tree.append(node)
    tree.push_container(node)
    try:
        yield
    finally:
        tree.pop_container()
