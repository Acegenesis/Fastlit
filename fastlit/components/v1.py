"""st.components.v1 — Custom component API compatible with Streamlit's protocol."""

from __future__ import annotations

import functools
import os
from typing import Any, Callable

# Global registry: component_name → resolved URL
_component_registry: dict[str, str] = {}


def declare_component(
    name: str,
    *,
    url: str | None = None,
    path: str | None = None,
) -> Callable[..., Any]:
    """Register a custom component and return a callable component function.

    Use ``url=`` for development mode (component served by its own dev server)
    and ``path=`` for production (Fastlit serves the built assets).

    Args:
        name: Unique component identifier.
        url: Dev-server URL, e.g. ``"http://localhost:3001"``.
        path: Path to the component's built frontend directory, e.g.
            ``"./my_component/frontend/build"``.  Fastlit will serve these
            files at ``/_components/<name>/``.

    Returns:
        A callable that, when invoked from a Fastlit script, renders the
        component and returns the latest value sent by the iframe.

    Examples::

        # Dev mode
        my_comp = st.components.v1.declare_component(
            "my_comp", url="http://localhost:3001"
        )
        value = my_comp(label="Hello", key="c1")

        # Prod mode
        my_comp = st.components.v1.declare_component(
            "my_comp", path="./my_component/frontend/build"
        )
        value = my_comp(label="Hello", key="c1")
    """
    if url is None and path is None:
        raise ValueError(
            "declare_component() requires either url= (dev mode) or path= (prod mode)."
        )
    if url is not None and path is not None:
        raise ValueError("declare_component() accepts either url= or path=, not both.")

    if path is not None:
        _register_static_path(name, path)
        resolved_url: str = f"/_components/{name}/index.html"
    else:
        resolved_url = url  # type: ignore[assignment]

    _component_registry[name] = resolved_url

    @functools.wraps(lambda **kw: None)
    def component_fn(
        *args: Any,
        key: str | None = None,
        default: Any = None,
        **kwargs: Any,
    ) -> Any:
        """Render the component and return its current value.

        Args:
            key: Optional stable key to override auto-generated ID.
            default: Value returned before the component sends its first event.
            **kwargs: Arbitrary props forwarded to the component iframe via
                ``streamlit:render`` postMessage.
        """
        if args:
            raise TypeError(
                f"Component '{name}' does not accept positional arguments."
            )
        from fastlit.runtime.context import get_current_session
        from fastlit.ui.base import _emit_node

        session = get_current_session()
        node = _emit_node(
            "custom_component",
            {
                "componentUrl": resolved_url,
                "componentName": name,
                "args": kwargs,
                "default": default,
            },
            key=key,
            is_widget=True,
        )
        stored = session.widget_store.get(node.id)
        return stored if stored is not None else default

    component_fn.__name__ = name
    component_fn.__qualname__ = f"declare_component.<locals>.{name}"
    return component_fn


def html(
    html_string: str,
    *,
    height: int | None = None,
    scrolling: bool = False,
) -> None:
    """Render arbitrary HTML inside a sandboxed iframe.

    Scripts are allowed (``sandbox="allow-scripts"``) but the iframe cannot
    access the parent page DOM or cookies.

    Args:
        html_string: Raw HTML to render.
        height: Height of the iframe in pixels. Defaults to 150.
        scrolling: Whether to show scrollbars. Defaults to False.

    Example::

        st.components.v1.html(
            "<h1 style='color:red'>Hello</h1>",
            height=100,
        )
    """
    from fastlit.ui.base import _emit_node

    _emit_node("static_html", {
        "html": html_string,
        "height": height if height is not None else 150,
        "scrolling": scrolling,
    })


def iframe(
    src: str,
    *,
    height: int | None = None,
    scrolling: bool = False,
) -> None:
    """Embed an external URL in an iframe (display only, no Python events).

    Args:
        src: URL to embed.
        height: Height of the iframe in pixels. Defaults to 150.
        scrolling: Whether to show scrollbars. Defaults to False.

    Example::

        st.components.v1.iframe("https://example.com", height=400)
    """
    from fastlit.ui.base import _emit_node

    _emit_node("static_html", {
        "src": src,
        "height": height if height is not None else 150,
        "scrolling": scrolling,
    })


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _register_static_path(name: str, path: str) -> None:
    """Register a component's build directory to be served by Fastlit."""
    abs_path = os.path.abspath(path)
    if not os.path.isdir(abs_path):
        raise FileNotFoundError(
            f"Component '{name}': build directory not found: {abs_path!r}\n"
            f"Make sure you have built the component frontend first."
        )
    from fastlit.server.app import register_component_path
    register_component_path(name, abs_path)
