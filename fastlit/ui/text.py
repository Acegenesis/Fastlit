"""Text display functions: st.title, st.header, st.subheader, st.markdown, st.write."""

from __future__ import annotations

import re
from typing import Any

from fastlit.ui.base import _emit_node

# Marker pattern: \x00W<widget_id>\x00<value>\x00
_MARKER_RE = re.compile(r"\x00W(.+?)\x00(.*?)\x00")


def _process_text(raw: str) -> dict:
    """Extract widget markers from text and return props dict.

    If markers are found, returns:
      {"text": <clean_text>, "_tpl": <template>, "_refs": {placeholder: widgetId}}
    Otherwise:
      {"text": <raw_text>}
    """
    matches = list(_MARKER_RE.finditer(raw))
    if not matches:
        return {"text": raw}

    # Build clean text (markers replaced with actual values)
    clean = _MARKER_RE.sub(r"\2", raw)

    # Build template (markers replaced with placeholders) and refs map
    refs = {}
    counter = 0

    def replacer(m: re.Match) -> str:
        nonlocal counter
        key = f"__w{counter}__"
        refs[key] = m.group(1)  # widget ID
        counter += 1
        return key

    template = _MARKER_RE.sub(replacer, raw)

    return {"text": clean, "_tpl": template, "_refs": refs}


def title(
    body: str,
    anchor: str | bool | None = None,
    *,
    help: str | None = None,
    width: str | int = "stretch",
    text_alignment: str = "left",
) -> None:
    """Display a title (h1).

    Args:
        body: The title text (supports GitHub-flavored Markdown).
        anchor: Custom anchor ID for linking. If False, no anchor. If None, auto-generate.
        help: Tooltip text to display (supports Markdown).
        width: Element width - "stretch" (default), "content", or pixel value.
        text_alignment: Horizontal alignment - "left" (default), "center", "right", or "justify".
    """
    props = _process_text(str(body))
    props["anchor"] = anchor
    props["help"] = help
    props["width"] = width
    props["textAlignment"] = text_alignment
    _emit_node("title", props)


def header(
    body: str,
    anchor: str | bool | None = None,
    *,
    divider: bool | str = False,
    help: str | None = None,
    width: str | int = "stretch",
    text_alignment: str = "left",
) -> None:
    """Display a header (h2).

    Args:
        body: The header text (supports GitHub-flavored Markdown).
        anchor: Custom anchor ID for linking. If False, no anchor. If None, auto-generate.
        divider: Show a colored divider below. Can be True, False, or a color
            ("blue", "green", "orange", "red", "violet", "yellow", "gray", "grey", "rainbow").
        help: Tooltip text to display (supports Markdown).
        width: Element width - "stretch" (default), "content", or pixel value.
        text_alignment: Horizontal alignment - "left" (default), "center", "right", or "justify".
    """
    props = _process_text(str(body))
    props["anchor"] = anchor
    props["divider"] = divider
    props["help"] = help
    props["width"] = width
    props["textAlignment"] = text_alignment
    _emit_node("header", props)


def subheader(
    body: str,
    anchor: str | bool | None = None,
    *,
    divider: bool | str = False,
    help: str | None = None,
    width: str | int = "stretch",
    text_alignment: str = "left",
) -> None:
    """Display a subheader (h3).

    Args:
        body: The subheader text (supports GitHub-flavored Markdown).
        anchor: Custom anchor ID for linking. If False, no anchor. If None, auto-generate.
        divider: Show a colored divider below. Can be True, False, or a color
            ("blue", "green", "orange", "red", "violet", "yellow", "gray", "grey", "rainbow").
        help: Tooltip text to display (supports Markdown).
        width: Element width - "stretch" (default), "content", or pixel value.
        text_alignment: Horizontal alignment - "left" (default), "center", "right", or "justify".
    """
    props = _process_text(str(body))
    props["anchor"] = anchor
    props["divider"] = divider
    props["help"] = help
    props["width"] = width
    props["textAlignment"] = text_alignment
    _emit_node("subheader", props)


def markdown(
    body: str,
    *,
    unsafe_allow_html: bool = False,
    help: str | None = None,
    width: str | int = "stretch",
    text_alignment: str = "left",
) -> None:
    """Display markdown text.

    Args:
        body: The markdown text (supports GitHub-flavored Markdown, emoji shortcodes,
            LaTeX expressions, colored text/backgrounds).
        unsafe_allow_html: If True, allow HTML in the markdown (use with caution).
        help: Tooltip text to display (supports Markdown).
        width: Element width - "stretch" (default), "content", or pixel value.
        text_alignment: Horizontal alignment - "left" (default), "center", "right", or "justify".
    """
    props = _process_text(str(body))
    props["unsafeAllowHtml"] = unsafe_allow_html
    props["help"] = help
    props["width"] = width
    props["textAlignment"] = text_alignment
    _emit_node("markdown", props)


def write(*args: Any, unsafe_allow_html: bool = False) -> None:
    """Display arguments as text with smart type detection.

    Supports multiple argument types:
    - Strings: rendered as markdown
    - DataFrames: rendered as dataframes
    - Dicts/lists: rendered as JSON
    - Charts: rendered as charts
    - Exceptions: rendered with traceback

    Args:
        *args: Arguments to display.
        unsafe_allow_html: If True, allow HTML (applies to string content).
    """
    for arg in args:
        _write_single(arg, unsafe_allow_html)


def _write_single(arg: Any, unsafe_allow_html: bool = False) -> None:
    """Write a single argument with smart type detection."""
    if arg is None:
        return

    # String -> markdown
    if isinstance(arg, str):
        props = _process_text(arg)
        props["unsafeAllowHtml"] = unsafe_allow_html
        _emit_node("markdown", props)
        return

    # Exception -> exception display
    if isinstance(arg, BaseException):
        from fastlit.ui.status import exception
        exception(arg)
        return

    # Try pandas DataFrame
    try:
        import pandas as pd
        if isinstance(arg, pd.DataFrame):
            from fastlit.ui.dataframe import dataframe
            dataframe(arg)
            return
    except ImportError:
        pass

    # Dict or list -> JSON
    if isinstance(arg, (dict, list)):
        json(arg)
        return

    # Plotly figure
    if hasattr(arg, "to_json") and hasattr(arg, "data"):
        from fastlit.ui.charts import plotly_chart
        plotly_chart(arg)
        return

    # Altair chart
    if hasattr(arg, "to_dict") and hasattr(arg, "mark"):
        from fastlit.ui.charts import altair_chart
        altair_chart(arg)
        return

    # Matplotlib figure
    if hasattr(arg, "savefig"):
        from fastlit.ui.charts import pyplot
        pyplot(arg)
        return

    # Default: convert to string and render as markdown
    props = _process_text(str(arg))
    props["unsafeAllowHtml"] = unsafe_allow_html
    _emit_node("markdown", props)


def text(
    body: str,
    *,
    help: str | None = None,
    width: str | int = "content",
    text_alignment: str = "left",
) -> None:
    """Display fixed-width text.

    Args:
        body: The text to display.
        help: Tooltip text to display (supports Markdown).
        width: Element width - "content" (default), "stretch", or pixel value.
        text_alignment: Horizontal alignment - "left" (default), "center", "right", or "justify".
    """
    props = _process_text(str(body))
    props["help"] = help
    props["width"] = width
    props["textAlignment"] = text_alignment
    _emit_node("text", props)


def metric(
    label: str,
    value: Any,
    delta: Any | None = None,
    delta_color: str = "normal",
    help: str | None = None,
    label_visibility: str = "visible",
    border: bool = False,
) -> None:
    """Display a metric with an optional delta indicator.

    Args:
        label: The metric label.
        value: The metric value.
        delta: The delta value (shows as +/- indicator).
        delta_color: Color of the delta ("normal", "inverse", "off").
        help: Tooltip text.
        label_visibility: "visible", "hidden", or "collapsed".
        border: If True, show a border around the metric.
    """
    _emit_node(
        "metric",
        {
            "label": str(label),
            "value": str(value) if value is not None else "-",
            "delta": str(delta) if delta is not None else None,
            "deltaColor": delta_color,
            "help": help,
            "labelVisibility": label_visibility,
            "border": border,
        },
    )


def json(body: Any, *, expanded: bool | int = True) -> None:
    """Display JSON data with syntax highlighting.

    Args:
        body: The JSON data (dict, list, or JSON string).
        expanded: If True, expand all. If int, expand to that depth.
    """
    import json as json_module

    # Convert to JSON-serializable format
    if isinstance(body, str):
        # Parse and re-serialize to validate and format
        try:
            parsed = json_module.loads(body)
            data = parsed
        except json_module.JSONDecodeError:
            data = body
    else:
        data = body

    _emit_node(
        "json",
        {
            "data": data,
            "expanded": expanded,
        },
    )


def code(
    body: str,
    language: str | None = "python",
    line_numbers: bool = False,
    *,
    wrap_lines: bool = False,
    height: str | int = "content",
    width: str | int = "stretch",
) -> None:
    """Display a code block with syntax highlighting.

    Args:
        body: The code to display.
        language: Programming language for syntax highlighting (default: "python").
            Set to None for plain monospace text.
        line_numbers: If True, show line numbers.
        wrap_lines: If True, wrap long lines.
        height: Code block height - "content" (default), "stretch", or pixel value.
        width: Code block width - "stretch" (default), "content", or pixel value.
    """
    _emit_node(
        "code",
        {
            "code": str(body),
            "language": language,
            "lineNumbers": line_numbers,
            "wrapLines": wrap_lines,
            "height": height,
            "width": width,
        },
    )


def caption(
    body: str,
    *,
    unsafe_allow_html: bool = False,
    help: str | None = None,
    width: str | int = "stretch",
    text_alignment: str = "left",
) -> None:
    """Display small caption text.

    Args:
        body: The caption text (supports GitHub-flavored Markdown).
        unsafe_allow_html: If True, allow HTML (use with caution).
        help: Tooltip text (supports Markdown).
        width: Element width - "stretch" (default), "content", or pixel value.
        text_alignment: Horizontal alignment - "left" (default), "center", "right", or "justify".
    """
    props = _process_text(str(body))
    props["help"] = help
    props["unsafeAllowHtml"] = unsafe_allow_html
    props["width"] = width
    props["textAlignment"] = text_alignment
    _emit_node("caption", props)


def latex(
    body: str,
    *,
    help: str | None = None,
    width: str | int = "stretch",
) -> None:
    """Display mathematical equations using LaTeX.

    Args:
        body: LaTeX expression or SymPy expression (without delimiters).
        help: Tooltip text (supports Markdown).
        width: Element width - "stretch" (default), "content", or pixel value.

    Example:
        st.latex(r"E = mc^2")
        st.latex(r"\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}")
    """
    # Support SymPy expressions
    if hasattr(body, "_repr_latex_"):
        body = body._repr_latex_()
    elif hasattr(body, "__latex__"):
        body = body.__latex__()

    _emit_node(
        "latex",
        {
            "text": str(body),
            "help": help,
            "width": width,
        },
    )


def echo(code_location: str = "above") -> "EchoContext":
    """Display code in the app alongside its output.

    Usage:
        with st.echo():
            st.write("Hello")

    Args:
        code_location: Where to display the code ("above" or "below").

    Returns:
        Context manager for echo block.
    """
    return EchoContext(code_location)


def html(body: str, *, width: str | int = "stretch") -> None:
    """Display raw HTML in the app.

    The HTML is sanitized on the client side for security.

    Args:
        body: The HTML string to display.
        width: Element width - "stretch" (default), "content", or pixel value.
    """
    _emit_node("html", {"body": str(body), "width": width})


def help(obj: Any) -> None:
    """Display the documentation of a Python object.

    Shows the object's type, signature (if callable), and docstring.

    Args:
        obj: The Python object to display help for.
    """
    import inspect

    parts: list[str] = []

    # Type info
    obj_type = type(obj).__name__
    obj_name = getattr(obj, "__name__", getattr(obj, "__qualname__", repr(obj)))
    parts.append(f"# {obj_name}")
    parts.append(f"**Type:** `{obj_type}`")

    # Signature for callables
    if callable(obj):
        try:
            sig = inspect.signature(obj)
            parts.append(f"**Signature:** `{obj_name}{sig}`")
        except (ValueError, TypeError):
            pass

    # Docstring
    doc = inspect.getdoc(obj)
    if doc:
        parts.append(f"\n{doc}")
    else:
        parts.append("\n*No documentation available.*")

    _emit_node("markdown", {"text": "\n\n".join(parts)})


def write_stream(stream: Any) -> str:
    """Stream a generator to the UI, displaying chunks as they arrive.

    Compatible with Streamlit's st.write_stream() API.  The function emits
    an empty placeholder node immediately, then registers the generator for
    deferred consumption: the WebSocket handler iterates the stream *after*
    the initial patch is sent so each chunk appears in real time.

    This is ideal for LLM streaming (OpenAI, Anthropic, etc.) where each
    ``next()`` call may take hundreds of milliseconds.

    Args:
        stream: A sync generator, iterator, or iterable that yields text
            chunks.  Async generators are not supported (wrap with
            ``asyncio.run_coroutine_threadsafe`` or consume manually).

    Returns:
        Empty string immediately (the full text is not available until
        streaming completes).  Use ``st.session_state`` to store the result
        if you need it in subsequent reruns.
    """
    from fastlit.runtime.context import get_current_session

    session = get_current_session()

    # Emit a placeholder node — _emit_node returns the UINode with its stable id.
    node = _emit_node("markdown", {"text": "", "isStreaming": True})

    # Register the generator for post-patch streaming by the WS handler.
    session._deferred_streams.append((node.id, iter(stream)))

    # Return empty string — streaming happens asynchronously after this run.
    return ""


def badge(
    label: str,
    *,
    color: str = "blue",
    icon: str | None = None,
) -> None:
    """Display an inline badge/tag.

    Args:
        label: The badge text.
        color: Badge color - "blue" (default), "green", "red", "orange",
            "violet", "yellow", "gray", "grey".
        icon: Optional icon (emoji).
    """
    _emit_node(
        "badge",
        {
            "label": str(label),
            "color": color,
            "icon": icon,
        },
    )


class EchoContext:
    """Context manager for st.echo."""

    def __init__(self, code_location: str = "above"):
        self._code_location = code_location
        self._code_lines: list[str] = []

    def __enter__(self):
        import inspect
        import linecache

        # Get the calling frame's code
        frame = inspect.currentframe()
        if frame and frame.f_back:
            outer = frame.f_back
            try:
                filename = outer.f_code.co_filename
                lineno = outer.f_lineno
                # Read lines after the 'with' statement
                lines = []
                indent = None
                for i in range(lineno + 1, lineno + 100):
                    line = linecache.getline(filename, i)
                    if not line:
                        break
                    # Detect initial indent
                    stripped = line.lstrip()
                    if stripped and indent is None:
                        indent = len(line) - len(stripped)
                    # Stop at dedented line (end of with block)
                    if stripped and indent is not None:
                        current_indent = len(line) - len(stripped)
                        if current_indent < indent:
                            break
                    if indent is not None:
                        # Remove the base indent
                        if len(line) >= indent:
                            lines.append(line[indent:])
                        else:
                            lines.append(line)
                self._code_lines = lines
            except Exception:
                self._code_lines = ["# Code not available"]

        if self._code_location == "above" and self._code_lines:
            code("".join(self._code_lines).rstrip(), language="python")

        return self

    def __exit__(self, *args):
        if self._code_location == "below" and self._code_lines:
            code("".join(self._code_lines).rstrip(), language="python")
