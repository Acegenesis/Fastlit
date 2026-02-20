"""st.fragment() — partial reruns for decorated functions."""

from __future__ import annotations

import datetime
import functools
from typing import Any, Callable

from fastlit.runtime.context import get_current_session
from fastlit.ui.base import _make_id
from fastlit.runtime.tree import UINode


def _parse_run_every(run_every: Any) -> float | None:
    """Convert *run_every* to a float number of seconds, or None if unset.

    Accepted formats:
    - ``None`` → disabled
    - ``int`` / ``float`` → seconds
    - ``datetime.timedelta`` → ``.total_seconds()``
    - ``str`` → ``"500ms"``, ``"5s"``, ``"2m"``, ``"1h"``
      (trailing unit; no unit = seconds)
    """
    if run_every is None:
        return None
    if isinstance(run_every, datetime.timedelta):
        return run_every.total_seconds()
    if isinstance(run_every, (int, float)):
        return float(run_every)
    if isinstance(run_every, str):
        s = run_every.strip()
        if s.endswith("ms"):
            return float(s[:-2]) / 1000.0
        if s.endswith("s"):
            return float(s[:-1])
        if s.endswith("m"):
            return float(s[:-1]) * 60.0
        if s.endswith("h"):
            return float(s[:-1]) * 3600.0
        return float(s)  # bare number → assume seconds
    raise ValueError(f"Invalid run_every value: {run_every!r}")


def fragment(func: Callable | None = None, *, run_every: Any = None) -> Callable:
    """Decorator that turns a function into an isolated UI fragment.

    When a widget inside the fragment changes, only the fragment's subtree
    is re-executed and patched — the rest of the page stays untouched.

    Usage::

        @st.fragment
        def counter():
            if "n" not in st.session_state:
                st.session_state.n = 0
            if st.button("Increment"):
                st.session_state.n += 1
            st.metric("Count", st.session_state.n)

        counter()
        st.write("This text is never re-rendered when the button is clicked.")

    Args:
        func: The function to decorate (when used as ``@st.fragment`` without
            parentheses).
        run_every: Auto-refresh interval.  Accepts ``int``/``float`` seconds,
            a ``datetime.timedelta``, or a string like ``"5s"``, ``"2m"``,
            ``"500ms"``.  When set, the fragment re-executes automatically at
            that interval even without user interaction — useful for live
            dashboards, metrics, and real-time feeds.
    """
    interval_s: float | None = _parse_run_every(run_every)

    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            session = get_current_session()

            # Compute a stable ID for the fragment container using the
            # *caller's* file+line (walk frame to user code, same as _make_id).
            fragment_id = _make_id("fragment")

            # Register the function so run_fragment() can call it later.
            session._fragment_registry[fragment_id] = (f, args, kwargs)

            # Store the auto-refresh interval for this fragment.
            # This dict persists across full reruns so the WS handler can
            # maintain asyncio timer tasks across the session lifetime.
            if interval_s is not None:
                session._fragment_run_every[fragment_id] = interval_s

            # Create the fragment container node and attach it to the tree.
            container = UINode(type="fragment", id=fragment_id, props={})
            session.current_tree.append(container)
            session.current_tree.push_container(container)

            # Execute the function — all st.* calls go into the container.
            prev_frag = session._current_fragment_id
            session._current_fragment_id = fragment_id
            try:
                result = f(*args, **kwargs)
            finally:
                session._current_fragment_id = prev_frag
                session.current_tree.pop_container()

            # Persist the subtree so run_fragment() can diff against it.
            session._fragment_subtrees[fragment_id] = container
            return result

        wrapper._is_fragment = True  # type: ignore[attr-defined]
        return wrapper

    if func is not None:
        # Used as @st.fragment (no parentheses)
        return decorator(func)
    # Used as @st.fragment(...) with keyword args
    return decorator
