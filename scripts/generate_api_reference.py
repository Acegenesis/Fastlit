from __future__ import annotations

import inspect
from pathlib import Path

import fastlit as st


OUT_PATH = Path("docs/API_REFERENCE.md")


EXAMPLE_OVERRIDES: dict[str, str] = {
    "title": 'st.title("My App")',
    "header": 'st.header("Section")',
    "subheader": 'st.subheader("Subsection")',
    "markdown": 'st.markdown("**bold** and `code`")',
    "write": 'st.write("Hello", {"a": 1})',
    "text": 'st.text("Raw monospace text")',
    "code": 'st.code("print(\'hello\')", language="python")',
    "caption": 'st.caption("Small helper text")',
    "metric": 'st.metric("Revenue", "$12.3k", delta="+5%")',
    "json": 'st.json({"key": "value"})',
    "latex": r'st.latex(r"E = mc^2")',
    "html": 'st.html("<b>Custom HTML</b>")',
    "badge": 'st.badge("Beta", color="blue")',
    "button": 'if st.button("Run"): st.success("Done")',
    "slider": 'value = st.slider("Volume", 0, 100, 50)',
    "text_input": 'name = st.text_input("Name", placeholder="Your name")',
    "text_area": 'bio = st.text_area("Bio")',
    "checkbox": 'enabled = st.checkbox("Enable feature", value=True)',
    "selectbox": 'choice = st.selectbox("Language", ["Python", "JS"])',
    "radio": 'mode = st.radio("Mode", ["A", "B"])',
    "number_input": 'n = st.number_input("Count", min_value=0, value=1)',
    "multiselect": 'tags = st.multiselect("Tags", ["a", "b", "c"])',
    "date_input": "day = st.date_input('Date')",
    "time_input": "when = st.time_input('Time')",
    "toggle": 'dark = st.toggle("Dark mode")',
    "color_picker": 'color = st.color_picker("Color", "#3B82F6")',
    "download_button": 'st.download_button("Download", "hello", file_name="hello.txt")',
    "select_slider": 'size = st.select_slider("Size", ["S", "M", "L"], value="M")',
    "file_uploader": 'file = st.file_uploader("Upload CSV", type=["csv"])',
    "feedback": 'rating = st.feedback("thumbs")',
    "pills": 'selected = st.pills("Category", ["A", "B", "C"])',
    "segmented_control": 'view = st.segmented_control("View", ["Table", "Chart"])',
    "camera_input": 'photo = st.camera_input("Take a photo")',
    "audio_input": 'audio = st.audio_input("Record audio")',
    "chat_message": 'with st.chat_message("assistant"): st.write("Hello!")',
    "chat_input": 'prompt = st.chat_input("Ask me anything...")',
    "dataframe": 'st.dataframe({"a": [1, 2], "b": [3, 4]})',
    "data_editor": 'edited = st.data_editor({"a": [1, 2]})',
    "table": 'st.table({"a": [1, 2], "b": [3, 4]})',
    "line_chart": 'st.line_chart({"x": [1, 2, 3], "y": [3, 2, 5]})',
    "bar_chart": 'st.bar_chart({"x": [1, 2, 3], "y": [3, 2, 5]})',
    "area_chart": 'st.area_chart({"x": [1, 2, 3], "y": [3, 2, 5]})',
    "scatter_chart": 'st.scatter_chart({"x": [1, 2, 3], "y": [3, 2, 5]})',
    "map": 'st.map([{"latitude": 48.85, "longitude": 2.35}])',
    "image": 'st.image("https://picsum.photos/600/300", caption="Sample")',
    "audio": 'st.audio("path/to/audio.mp3")',
    "video": 'st.video("path/to/video.mp4")',
    "logo": 'st.logo("https://picsum.photos/120/40")',
    "pdf": 'st.pdf("path/to/file.pdf")',
    "columns": "col1, col2 = st.columns(2)",
    "tabs": 'tab1, tab2 = st.tabs(["A", "B"])',
    "expander": 'with st.expander("Details"): st.write("Hidden content")',
    "container": "with st.container(): st.write('Inside container')",
    "empty": "placeholder = st.empty()",
    "form": 'with st.form("my_form"): st.form_submit_button("Submit")',
    "form_submit_button": 'submitted = st.form_submit_button("Submit")',
    "dialog": '@st.dialog("Confirm")\ndef dlg(): st.write("...")',
    "popover": 'with st.popover("Settings"): st.toggle("Enable")',
    "divider": "st.divider()",
    "navigation": 'page = st.navigation(["Home", "Data"])',
    "switch_page": 'st.switch_page("Home")',
    "set_sidebar_state": 'st.set_sidebar_state("collapsed")',
    "rerun": "st.rerun()",
    "stop": "st.stop()",
    "set_page_config": 'st.set_page_config(page_title="Demo", layout="wide")',
    "run_in_thread": "t = st.run_in_thread(lambda: 42)",
    "run_with_session_context": "st.run_with_session_context(my_fn, arg1)",
    "on_startup": "@st.on_startup\ndef init(): pass",
    "on_shutdown": "@st.on_shutdown\ndef cleanup(): pass",
    "cache_data": "@st.cache_data\ndef f(x): return x * 2",
    "cache_resource": "@st.cache_resource\ndef get_conn(): return object()",
    "success": 'st.success("Saved")',
    "info": 'st.info("FYI")',
    "warning": 'st.warning("Be careful")',
    "error": 'st.error("An error occurred")',
    "exception": "try:\n    1/0\nexcept Exception as e:\n    st.exception(e)",
    "progress": "p = st.progress(10)",
    "spinner": 'with st.spinner("Loading..."): pass',
    "status": 'with st.status("Working...") as s:\n    s.update(state="complete", label="Done")',
    "toast": 'st.toast("Done", icon="✅")',
    "balloons": "st.balloons()",
    "snow": "st.snow()",
    "write_stream": "st.write_stream(iter(['Hello ', 'world']))",
    "fragment": "@st.fragment\ndef part():\n    st.write('Partial rerun')",
}


def _is_public_function(name: str) -> bool:
    if name.startswith("_"):
        return False
    if name in {"UploadedFile", "RerunException", "StopException"}:
        return False
    obj = getattr(st, name, None)
    if obj is None:
        return False
    return callable(obj)


def _signature_of(name: str) -> str:
    obj = getattr(st, name)
    try:
        sig = inspect.signature(obj)
        return f"st.{name}{sig}"
    except (TypeError, ValueError):
        return f"st.{name}(...)"


def _params_markdown(name: str) -> str:
    obj = getattr(st, name)
    try:
        sig = inspect.signature(obj)
    except (TypeError, ValueError):
        return "- Parameters not introspectable."

    rows: list[str] = []
    for p in sig.parameters.values():
        default = "required" if p.default is inspect._empty else repr(p.default)
        annot = "Any" if p.annotation is inspect._empty else str(p.annotation).replace("typing.", "")
        rows.append(f"- `{p.name}`: `{annot}` (default: `{default}`)")
    return "\n".join(rows) if rows else "- No parameters."


def _example_of(name: str) -> str:
    override = EXAMPLE_OVERRIDES.get(name)
    if override:
        return override

    obj = getattr(st, name)
    try:
        sig = inspect.signature(obj)
    except (TypeError, ValueError):
        return f"st.{name}(...)"

    args: list[str] = []
    kwargs: list[str] = []
    for p in sig.parameters.values():
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue

        required = p.default is inspect._empty
        value = _guess_example_value(p.name, p.annotation)
        if required and p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            args.append(value)
        else:
            kwargs.append(f"{p.name}={value}")

    joined = ", ".join(args + kwargs)
    return f"st.{name}({joined})"


def _guess_example_value(param_name: str, annotation: object) -> str:
    ann = str(annotation).lower()
    name = param_name.lower()
    if "label" in name or name in {"title", "body", "text", "caption"}:
        return '"Example"'
    if "options" in name:
        return '["A", "B"]'
    if "data" in name:
        return '{"x": [1, 2], "y": [3, 4]}'
    if "fig" in name or "chart" in name:
        return "{}"
    if "key" in name:
        return '"demo_key"'
    if "int" in ann:
        return "1"
    if "float" in ann:
        return "1.0"
    if "bool" in ann:
        return "False"
    if "str" in ann:
        return '"value"'
    if "sequence" in ann or "list" in ann or "tuple" in ann:
        return "[1, 2]"
    if "dict" in ann or "mapping" in ann:
        return '{"a": 1}'
    return "None"


def build_reference() -> str:
    names = [n for n in dir(st) if _is_public_function(n)]
    names = sorted(set(names))
    parts: list[str] = []
    parts.append("# Fastlit API Reference (Auto-generated)")
    parts.append("")
    parts.append("Generated from real Python signatures in `fastlit`.")
    parts.append("Regenerate with: `python scripts/generate_api_reference.py`")
    parts.append("")
    parts.append(f"Total documented functions: **{len(names)}**")
    parts.append("")

    for name in names:
        parts.append(f"## `st.{name}`")
        parts.append("")
        parts.append("**Signature**")
        parts.append("```python")
        parts.append(_signature_of(name))
        parts.append("```")
        parts.append("")
        parts.append("**Parameters**")
        parts.append(_params_markdown(name))
        parts.append("")
        parts.append("**Example**")
        parts.append("```python")
        parts.append(_example_of(name))
        parts.append("```")
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(build_reference(), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
