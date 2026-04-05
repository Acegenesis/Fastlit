"""st.fragment() - partial reruns for isolated UI sections."""

from __future__ import annotations

import datetime
import functools
from typing import Any, Callable, Literal

from fastlit.runtime.context import get_current_session
from fastlit.runtime.tree import UINode
from fastlit.ui.base import _make_id

FragmentPlaceholder = Literal["skeleton", "spinner", "none"]


def _parse_run_every(run_every: Any) -> float | None:
    """Convert *run_every* to seconds, or None if unset."""
    if run_every is None:
        return None
    if isinstance(run_every, datetime.timedelta):
        return run_every.total_seconds()
    if isinstance(run_every, (int, float)):
        return float(run_every)
    if isinstance(run_every, str):
        value = run_every.strip()
        if value.endswith("ms"):
            return float(value[:-2]) / 1000.0
        if value.endswith("s"):
            return float(value[:-1])
        if value.endswith("m"):
            return float(value[:-1]) * 60.0
        if value.endswith("h"):
            return float(value[:-1]) * 3600.0
        return float(value)
    raise ValueError(f"Invalid run_every value: {run_every!r}")


def fragment(
    func: Callable | None = None,
    *,
    run_every: Any = None,
    deferred: bool = False,
    placeholder: FragmentPlaceholder = "skeleton",
    min_height: int | None = None,
) -> Callable:
    """Decorator that turns a function into an isolated UI fragment.

    When a widget inside the fragment changes, only that fragment subtree is
    re-executed. When ``deferred=True``, the fragment renders a local loader
    during the parent full run and hydrates immediately afterwards.
    """

    interval_s: float | None = _parse_run_every(run_every)
    if placeholder not in {"skeleton", "spinner", "none"}:
        raise ValueError("placeholder must be 'skeleton', 'spinner', or 'none'")
    normalized_min_height = int(min_height) if min_height is not None else None

    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            session = get_current_session()
            fragment_id = _make_id("fragment")

            session._fragment_registry[fragment_id] = (f, args, kwargs)

            if interval_s is not None:
                session._fragment_run_every[fragment_id] = interval_s

            container_props: dict[str, Any] = {}
            old_subtree = session._fragment_subtrees.get(fragment_id)
            if deferred:
                container_props = {
                    "loading": True,
                    "placeholder": placeholder,
                }
                if normalized_min_height is not None:
                    container_props["minHeight"] = normalized_min_height

            container = UINode(type="fragment", id=fragment_id, props=container_props)
            if deferred and old_subtree is not None and old_subtree.children:
                container.replace_children(list(old_subtree.children))

            tree = session.current_tree
            assert tree is not None
            tree.append(container)
            if deferred:
                session._fragment_subtrees[fragment_id] = container
                session.register_deferred_fragment(fragment_id)
                return None

            tree.push_container(container)
            prev_frag = session._current_fragment_id
            session._current_fragment_id = fragment_id
            try:
                result = f(*args, **kwargs)
            finally:
                session._current_fragment_id = prev_frag
                tree.pop_container()

            session._fragment_subtrees[fragment_id] = container
            return result

        wrapper._is_fragment = True  # type: ignore[attr-defined]
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator
