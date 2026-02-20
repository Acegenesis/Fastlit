# Fastlit API Reference (Auto-generated)

Generated from real Python signatures in `fastlit`.
Regenerate with: `python scripts/generate_api_reference.py`

Total documented functions: **96**

## `st.altair_chart`

**Signature**
```python
st.altair_chart(altair_chart: 'Any', *, use_container_width: 'bool' = True, theme: 'str | None' = 'streamlit', key: 'str | None' = None) -> 'None'
```

**Parameters**
- `altair_chart`: `Any` (default: `required`)
- `use_container_width`: `bool` (default: `True`)
- `theme`: `str | None` (default: `'streamlit'`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.altair_chart({}, use_container_width=False, theme="value", key="demo_key")
```

## `st.area_chart`

**Signature**
```python
st.area_chart(data: 'Any', *, x: 'str | None' = None, y: 'str | Sequence[str] | None' = None, color: 'str | Sequence[str] | None' = None, width: 'int | None' = None, height: 'int | None' = None, use_container_width: 'bool' = True, stack: 'bool' = False) -> 'None'
```

**Parameters**
- `data`: `Any` (default: `required`)
- `x`: `str | None` (default: `None`)
- `y`: `str | Sequence[str] | None` (default: `None`)
- `color`: `str | Sequence[str] | None` (default: `None`)
- `width`: `int | None` (default: `None`)
- `height`: `int | None` (default: `None`)
- `use_container_width`: `bool` (default: `True`)
- `stack`: `bool` (default: `False`)

**Example**
```python
st.area_chart({"x": [1, 2, 3], "y": [3, 2, 5]})
```

## `st.audio`

**Signature**
```python
st.audio(data: 'Any', format: 'str' = 'audio/wav', start_time: 'int' = 0, *, sample_rate: 'int | None' = None, end_time: 'int | None' = None, loop: 'bool' = False, autoplay: 'bool' = False, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `data`: `Any` (default: `required`)
- `format`: `str` (default: `'audio/wav'`)
- `start_time`: `int` (default: `0`)
- `sample_rate`: `int | None` (default: `None`)
- `end_time`: `int | None` (default: `None`)
- `loop`: `bool` (default: `False`)
- `autoplay`: `bool` (default: `False`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.audio("path/to/audio.mp3")
```

## `st.audio_input`

**Signature**
```python
st.audio_input(label: 'str', *, key: 'str | None' = None, help: 'str | None' = None, disabled: 'bool' = False, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, label_visibility: 'str' = 'visible') -> "'UploadedFile | None'"
```

**Parameters**
- `label`: `str` (default: `required`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `label_visibility`: `str` (default: `'visible'`)

**Example**
```python
audio = st.audio_input("Record audio")
```

## `st.badge`

**Signature**
```python
st.badge(label: 'str', *, color: 'str' = 'blue', icon: 'str | None' = None) -> 'None'
```

**Parameters**
- `label`: `str` (default: `required`)
- `color`: `str` (default: `'blue'`)
- `icon`: `str | None` (default: `None`)

**Example**
```python
st.badge("Beta", color="blue")
```

## `st.balloons`

**Signature**
```python
st.balloons() -> 'None'
```

**Parameters**
- No parameters.

**Example**
```python
st.balloons()
```

## `st.bar_chart`

**Signature**
```python
st.bar_chart(data: 'Any', *, x: 'str | None' = None, y: 'str | Sequence[str] | None' = None, color: 'str | Sequence[str] | None' = None, width: 'int | None' = None, height: 'int | None' = None, use_container_width: 'bool' = True, horizontal: 'bool' = False) -> 'None'
```

**Parameters**
- `data`: `Any` (default: `required`)
- `x`: `str | None` (default: `None`)
- `y`: `str | Sequence[str] | None` (default: `None`)
- `color`: `str | Sequence[str] | None` (default: `None`)
- `width`: `int | None` (default: `None`)
- `height`: `int | None` (default: `None`)
- `use_container_width`: `bool` (default: `True`)
- `horizontal`: `bool` (default: `False`)

**Example**
```python
st.bar_chart({"x": [1, 2, 3], "y": [3, 2, 5]})
```

## `st.bokeh_chart`

**Signature**
```python
st.bokeh_chart(figure: 'Any', *, use_container_width: 'bool' = True, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `figure`: `Any` (default: `required`)
- `use_container_width`: `bool` (default: `True`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.bokeh_chart({}, use_container_width=False, key="demo_key")
```

## `st.button`

**Signature**
```python
st.button(label: 'str', key: 'str | None' = None, help: 'str | None' = None, on_click: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, type: 'str' = 'secondary', icon: 'str | None' = None, icon_position: 'str' = 'left', disabled: 'bool' = False, use_container_width: 'bool | None' = None, width: 'str | int' = 'content', shortcut: 'str | None' = None) -> 'bool'
```

**Parameters**
- `label`: `str` (default: `required`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_click`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `type`: `str` (default: `'secondary'`)
- `icon`: `str | None` (default: `None`)
- `icon_position`: `str` (default: `'left'`)
- `disabled`: `bool` (default: `False`)
- `use_container_width`: `bool | None` (default: `None`)
- `width`: `str | int` (default: `'content'`)
- `shortcut`: `str | None` (default: `None`)

**Example**
```python
if st.button("Run"): st.success("Done")
```

## `st.cache_data`

**Signature**
```python
st.cache_data(func: 'F | None' = None, *, ttl: 'float | None' = None, max_entries: 'int' = 1000, copy: 'bool' = True) -> 'Any'
```

**Parameters**
- `func`: `F | None` (default: `None`)
- `ttl`: `float | None` (default: `None`)
- `max_entries`: `int` (default: `1000`)
- `copy`: `bool` (default: `True`)

**Example**
```python
@st.cache_data
def f(x): return x * 2
```

## `st.cache_resource`

**Signature**
```python
st.cache_resource(func: 'F | None' = None) -> 'Any'
```

**Parameters**
- `func`: `F | None` (default: `None`)

**Example**
```python
@st.cache_resource
def get_conn(): return object()
```

## `st.camera_input`

**Signature**
```python
st.camera_input(label: 'str', *, key: 'str | None' = None, help: 'str | None' = None, disabled: 'bool' = False, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, label_visibility: 'str' = 'visible') -> "'UploadedFile | None'"
```

**Parameters**
- `label`: `str` (default: `required`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `label_visibility`: `str` (default: `'visible'`)

**Example**
```python
photo = st.camera_input("Take a photo")
```

## `st.caption`

**Signature**
```python
st.caption(body: 'str', *, unsafe_allow_html: 'bool' = False, help: 'str | None' = None, width: 'str | int' = 'stretch', text_alignment: 'str' = 'left') -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `unsafe_allow_html`: `bool` (default: `False`)
- `help`: `str | None` (default: `None`)
- `width`: `str | int` (default: `'stretch'`)
- `text_alignment`: `str` (default: `'left'`)

**Example**
```python
st.caption("Small helper text")
```

## `st.chat_input`

**Signature**
```python
st.chat_input(placeholder: 'str' = 'Type a message...', *, key: 'str | None' = None, max_chars: 'int | None' = None, disabled: 'bool' = False, on_submit: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None) -> 'str | None'
```

**Parameters**
- `placeholder`: `str` (default: `'Type a message...'`)
- `key`: `str | None` (default: `None`)
- `max_chars`: `int | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `on_submit`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)

**Example**
```python
prompt = st.chat_input("Ask me anything...")
```

## `st.chat_message`

**Signature**
```python
st.chat_message(name: 'str', *, avatar: 'str | None' = None) -> 'ChatMessage'
```

**Parameters**
- `name`: `str` (default: `required`)
- `avatar`: `str | None` (default: `None`)

**Example**
```python
with st.chat_message("assistant"): st.write("Hello!")
```

## `st.checkbox`

**Signature**
```python
st.checkbox(label: 'str', value: 'bool' = False, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, disabled: 'bool' = False, label_visibility: 'str' = 'visible', width: 'str | int' = 'content') -> 'bool'
```

**Parameters**
- `label`: `str` (default: `required`)
- `value`: `bool` (default: `False`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `width`: `str | int` (default: `'content'`)

**Example**
```python
enabled = st.checkbox("Enable feature", value=True)
```

## `st.code`

**Signature**
```python
st.code(body: 'str', language: 'str | None' = 'python', line_numbers: 'bool' = False, *, wrap_lines: 'bool' = False, height: 'str | int' = 'content', width: 'str | int' = 'stretch') -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `language`: `str | None` (default: `'python'`)
- `line_numbers`: `bool` (default: `False`)
- `wrap_lines`: `bool` (default: `False`)
- `height`: `str | int` (default: `'content'`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
st.code("print('hello')", language="python")
```

## `st.color_picker`

**Signature**
```python
st.color_picker(label: 'str', value: 'str' = '#000000', key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, disabled: 'bool' = False, label_visibility: 'str' = 'visible', width: 'str | int' = 'content') -> 'str'
```

**Parameters**
- `label`: `str` (default: `required`)
- `value`: `str` (default: `'#000000'`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `width`: `str | int` (default: `'content'`)

**Example**
```python
color = st.color_picker("Color", "#3B82F6")
```

## `st.columns`

**Signature**
```python
st.columns(spec: 'int | Sequence[int | float]', *, gap: 'str | None' = 'small', vertical_alignment: 'str' = 'top', border: 'bool' = False, key: 'str | None' = None) -> 'list[Column]'
```

**Parameters**
- `spec`: `int | Sequence[int | float]` (default: `required`)
- `gap`: `str | None` (default: `'small'`)
- `vertical_alignment`: `str` (default: `'top'`)
- `border`: `bool` (default: `False`)
- `key`: `str | None` (default: `None`)

**Example**
```python
col1, col2 = st.columns(2)
```

## `st.container`

**Signature**
```python
st.container(*, border: 'bool | None' = None, key: 'str | None' = None, height: 'int | str | None' = None) -> 'Container'
```

**Parameters**
- `border`: `bool | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `height`: `int | str | None` (default: `None`)

**Example**
```python
with st.container(): st.write('Inside container')
```

## `st.data_editor`

**Signature**
```python
st.data_editor(data: 'Any', *, width: 'int | None' = None, height: 'int | None' = None, use_container_width: 'bool' = True, hide_index: 'bool | None' = None, column_order: 'list[str] | None' = None, column_config: 'dict | None' = None, num_rows: 'str' = 'fixed', disabled: 'bool | list[str]' = False, key: 'str | None' = None, on_change: 'Any' = None) -> 'Any'
```

**Parameters**
- `data`: `Any` (default: `required`)
- `width`: `int | None` (default: `None`)
- `height`: `int | None` (default: `None`)
- `use_container_width`: `bool` (default: `True`)
- `hide_index`: `bool | None` (default: `None`)
- `column_order`: `list[str] | None` (default: `None`)
- `column_config`: `dict | None` (default: `None`)
- `num_rows`: `str` (default: `'fixed'`)
- `disabled`: `bool | list[str]` (default: `False`)
- `key`: `str | None` (default: `None`)
- `on_change`: `Any` (default: `None`)

**Example**
```python
edited = st.data_editor({"a": [1, 2]})
```

## `st.dataframe`

**Signature**
```python
st.dataframe(data: 'Any', *, height: 'int | None' = None, use_container_width: 'bool' = True, hide_index: 'bool' = False, max_rows: 'int | None' = None, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `data`: `Any` (default: `required`)
- `height`: `int | None` (default: `None`)
- `use_container_width`: `bool` (default: `True`)
- `hide_index`: `bool` (default: `False`)
- `max_rows`: `int | None` (default: `None`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.dataframe({"a": [1, 2], "b": [3, 4]})
```

## `st.date_input`

**Signature**
```python
st.date_input(label: 'str', value: 'datetime.date | tuple[datetime.date, datetime.date] | str | None' = 'today', min_value: 'datetime.date | str | None' = None, max_value: 'datetime.date | str | None' = None, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, format: 'str' = 'YYYY/MM/DD', disabled: 'bool' = False, label_visibility: 'str' = 'visible', width: 'str | int' = 'stretch') -> 'datetime.date | tuple[datetime.date, datetime.date] | None'
```

**Parameters**
- `label`: `str` (default: `required`)
- `value`: `datetime.date | tuple[datetime.date, datetime.date] | str | None` (default: `'today'`)
- `min_value`: `datetime.date | str | None` (default: `None`)
- `max_value`: `datetime.date | str | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `format`: `str` (default: `'YYYY/MM/DD'`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
day = st.date_input('Date')
```

## `st.dialog`

**Signature**
```python
st.dialog(title: 'str', *, width: 'str' = 'small', dismissible: 'bool' = True) -> 'Callable'
```

**Parameters**
- `title`: `str` (default: `required`)
- `width`: `str` (default: `'small'`)
- `dismissible`: `bool` (default: `True`)

**Example**
```python
@st.dialog("Confirm")
def dlg(): st.write("...")
```

## `st.divider`

**Signature**
```python
st.divider() -> 'None'
```

**Parameters**
- No parameters.

**Example**
```python
st.divider()
```

## `st.download_button`

**Signature**
```python
st.download_button(label: 'str', data: 'Any', file_name: 'str | None' = None, mime: 'str | None' = None, key: 'str | None' = None, help: 'str | None' = None, on_click: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, type: 'str' = 'secondary', icon: 'str | None' = None, disabled: 'bool' = False, use_container_width: 'bool' = False) -> 'bool'
```

**Parameters**
- `label`: `str` (default: `required`)
- `data`: `Any` (default: `required`)
- `file_name`: `str | None` (default: `None`)
- `mime`: `str | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_click`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `type`: `str` (default: `'secondary'`)
- `icon`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `use_container_width`: `bool` (default: `False`)

**Example**
```python
st.download_button("Download", "hello", file_name="hello.txt")
```

## `st.echo`

**Signature**
```python
st.echo(code_location: 'str' = 'above') -> "'EchoContext'"
```

**Parameters**
- `code_location`: `str` (default: `'above'`)

**Example**
```python
st.echo(code_location="value")
```

## `st.empty`

**Signature**
```python
st.empty() -> 'Empty'
```

**Parameters**
- No parameters.

**Example**
```python
placeholder = st.empty()
```

## `st.error`

**Signature**
```python
st.error(body: 'str', *, icon: 'str | None' = None) -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `icon`: `str | None` (default: `None`)

**Example**
```python
st.error("An error occurred")
```

## `st.exception`

**Signature**
```python
st.exception(exception: 'BaseException | None' = None) -> 'None'
```

**Parameters**
- `exception`: `BaseException | None` (default: `None`)

**Example**
```python
try:
    1/0
except Exception as e:
    st.exception(e)
```

## `st.expander`

**Signature**
```python
st.expander(label: 'str', expanded: 'bool' = False, *, icon: 'str | None' = None, key: 'str | None' = None) -> 'Expander'
```

**Parameters**
- `label`: `str` (default: `required`)
- `expanded`: `bool` (default: `False`)
- `icon`: `str | None` (default: `None`)
- `key`: `str | None` (default: `None`)

**Example**
```python
with st.expander("Details"): st.write("Hidden content")
```

## `st.feedback`

**Signature**
```python
st.feedback(sentiment_mapping: 'dict[int, str] | str | None' = None, *, key: 'str | None' = None, disabled: 'bool' = False, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None) -> 'int | None'
```

**Parameters**
- `sentiment_mapping`: `dict[int, str] | str | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)

**Example**
```python
rating = st.feedback("thumbs")
```

## `st.file_uploader`

**Signature**
```python
st.file_uploader(label: 'str', type: 'str | Sequence[str] | None' = None, accept_multiple_files: 'bool' = False, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, disabled: 'bool' = False, label_visibility: 'str' = 'visible', width: 'str | int' = 'stretch', max_file_size_mb: 'int | None' = None) -> 'Any'
```

**Parameters**
- `label`: `str` (default: `required`)
- `type`: `str | Sequence[str] | None` (default: `None`)
- `accept_multiple_files`: `bool` (default: `False`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `width`: `str | int` (default: `'stretch'`)
- `max_file_size_mb`: `int | None` (default: `None`)

**Example**
```python
file = st.file_uploader("Upload CSV", type=["csv"])
```

## `st.form`

**Signature**
```python
st.form(key: 'str', clear_on_submit: 'bool' = False, *, enter_to_submit: 'bool' = True, border: 'bool' = True) -> 'Form'
```

**Parameters**
- `key`: `str` (default: `required`)
- `clear_on_submit`: `bool` (default: `False`)
- `enter_to_submit`: `bool` (default: `True`)
- `border`: `bool` (default: `True`)

**Example**
```python
with st.form("my_form"): st.form_submit_button("Submit")
```

## `st.form_submit_button`

**Signature**
```python
st.form_submit_button(label: 'str' = 'Submit', *, help: 'str | None' = None, on_click: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, type: 'str' = 'secondary', disabled: 'bool' = False, use_container_width: 'bool' = False, key: 'str | None' = None) -> 'bool'
```

**Parameters**
- `label`: `str` (default: `'Submit'`)
- `help`: `str | None` (default: `None`)
- `on_click`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `type`: `str` (default: `'secondary'`)
- `disabled`: `bool` (default: `False`)
- `use_container_width`: `bool` (default: `False`)
- `key`: `str | None` (default: `None`)

**Example**
```python
submitted = st.form_submit_button("Submit")
```

## `st.fragment`

**Signature**
```python
st.fragment(func: 'Callable | None' = None, *, run_every: 'Any' = None) -> 'Callable'
```

**Parameters**
- `func`: `Callable | None` (default: `None`)
- `run_every`: `Any` (default: `None`)

**Example**
```python
@st.fragment
def part():
    st.write('Partial rerun')
```

## `st.get_current_session`

**Signature**
```python
st.get_current_session() -> 'Session'
```

**Parameters**
- No parameters.

**Example**
```python
st.get_current_session()
```

## `st.graphviz_chart`

**Signature**
```python
st.graphviz_chart(figure_or_dot: 'Any', *, use_container_width: 'bool' = True, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `figure_or_dot`: `Any` (default: `required`)
- `use_container_width`: `bool` (default: `True`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.graphviz_chart({}, use_container_width=False, key="demo_key")
```

## `st.header`

**Signature**
```python
st.header(body: 'str', anchor: 'str | bool | None' = None, *, divider: 'bool | str' = False, help: 'str | None' = None, width: 'str | int' = 'stretch', text_alignment: 'str' = 'left') -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `anchor`: `str | bool | None` (default: `None`)
- `divider`: `bool | str` (default: `False`)
- `help`: `str | None` (default: `None`)
- `width`: `str | int` (default: `'stretch'`)
- `text_alignment`: `str` (default: `'left'`)

**Example**
```python
st.header("Section")
```

## `st.help`

**Signature**
```python
st.help(obj: 'Any') -> 'None'
```

**Parameters**
- `obj`: `Any` (default: `required`)

**Example**
```python
st.help(None)
```

## `st.html`

**Signature**
```python
st.html(body: 'str', *, width: 'str | int' = 'stretch') -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
st.html("<b>Custom HTML</b>")
```

## `st.image`

**Signature**
```python
st.image(image: 'Any', caption: 'str | None' = None, width: 'int | None' = None, use_container_width: "bool | Literal['auto', 'always', 'never']" = 'auto', clamp: 'bool' = False, channels: 'str' = 'RGB', output_format: 'str' = 'auto', *, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `image`: `Any` (default: `required`)
- `caption`: `str | None` (default: `None`)
- `width`: `int | None` (default: `None`)
- `use_container_width`: `bool | Literal['auto', 'always', 'never']` (default: `'auto'`)
- `clamp`: `bool` (default: `False`)
- `channels`: `str` (default: `'RGB'`)
- `output_format`: `str` (default: `'auto'`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.image("https://picsum.photos/600/300", caption="Sample")
```

## `st.info`

**Signature**
```python
st.info(body: 'str', *, icon: 'str | None' = None) -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `icon`: `str | None` (default: `None`)

**Example**
```python
st.info("FYI")
```

## `st.json`

**Signature**
```python
st.json(body: 'Any', *, expanded: 'bool | int' = True) -> 'None'
```

**Parameters**
- `body`: `Any` (default: `required`)
- `expanded`: `bool | int` (default: `True`)

**Example**
```python
st.json({"key": "value"})
```

## `st.latex`

**Signature**
```python
st.latex(body: 'str', *, help: 'str | None' = None, width: 'str | int' = 'stretch') -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `help`: `str | None` (default: `None`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
st.latex(r"E = mc^2")
```

## `st.line_chart`

**Signature**
```python
st.line_chart(data: 'Any', *, x: 'str | None' = None, y: 'str | Sequence[str] | None' = None, color: 'str | Sequence[str] | None' = None, width: 'int | None' = None, height: 'int | None' = None, use_container_width: 'bool' = True) -> 'None'
```

**Parameters**
- `data`: `Any` (default: `required`)
- `x`: `str | None` (default: `None`)
- `y`: `str | Sequence[str] | None` (default: `None`)
- `color`: `str | Sequence[str] | None` (default: `None`)
- `width`: `int | None` (default: `None`)
- `height`: `int | None` (default: `None`)
- `use_container_width`: `bool` (default: `True`)

**Example**
```python
st.line_chart({"x": [1, 2, 3], "y": [3, 2, 5]})
```

## `st.link_button`

**Signature**
```python
st.link_button(label: 'str', url: 'str', *, help: 'str | None' = None, type: 'str' = 'secondary', icon: 'str | None' = None, disabled: 'bool' = False, use_container_width: 'bool' = False) -> 'None'
```

**Parameters**
- `label`: `str` (default: `required`)
- `url`: `str` (default: `required`)
- `help`: `str | None` (default: `None`)
- `type`: `str` (default: `'secondary'`)
- `icon`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `use_container_width`: `bool` (default: `False`)

**Example**
```python
st.link_button("Example", "value", help="value", type="value", icon="value", disabled=False, use_container_width=False)
```

## `st.logo`

**Signature**
```python
st.logo(image: 'Any', *, size: 'str' = 'medium', link: 'str | None' = None, icon_image: 'Any | None' = None, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `image`: `Any` (default: `required`)
- `size`: `str` (default: `'medium'`)
- `link`: `str | None` (default: `None`)
- `icon_image`: `Any | None` (default: `None`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.logo("https://picsum.photos/120/40")
```

## `st.map`

**Signature**
```python
st.map(data: 'Any' = None, *, latitude: 'str | None' = None, longitude: 'str | None' = None, color: 'str | None' = None, size: 'str | None' = None, zoom: 'int | None' = None, use_container_width: 'bool' = True, height: 'int | None' = None) -> 'None'
```

**Parameters**
- `data`: `Any` (default: `None`)
- `latitude`: `str | None` (default: `None`)
- `longitude`: `str | None` (default: `None`)
- `color`: `str | None` (default: `None`)
- `size`: `str | None` (default: `None`)
- `zoom`: `int | None` (default: `None`)
- `use_container_width`: `bool` (default: `True`)
- `height`: `int | None` (default: `None`)

**Example**
```python
st.map([{"latitude": 48.85, "longitude": 2.35}])
```

## `st.markdown`

**Signature**
```python
st.markdown(body: 'str', *, unsafe_allow_html: 'bool' = False, help: 'str | None' = None, width: 'str | int' = 'stretch', text_alignment: 'str' = 'left') -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `unsafe_allow_html`: `bool` (default: `False`)
- `help`: `str | None` (default: `None`)
- `width`: `str | int` (default: `'stretch'`)
- `text_alignment`: `str` (default: `'left'`)

**Example**
```python
st.markdown("**bold** and `code`")
```

## `st.metric`

**Signature**
```python
st.metric(label: 'str', value: 'Any', delta: 'Any | None' = None, delta_color: 'str' = 'normal', help: 'str | None' = None, label_visibility: 'str' = 'visible', border: 'bool' = False) -> 'None'
```

**Parameters**
- `label`: `str` (default: `required`)
- `value`: `Any` (default: `required`)
- `delta`: `Any | None` (default: `None`)
- `delta_color`: `str` (default: `'normal'`)
- `help`: `str | None` (default: `None`)
- `label_visibility`: `str` (default: `'visible'`)
- `border`: `bool` (default: `False`)

**Example**
```python
st.metric("Revenue", "$12.3k", delta="+5%")
```

## `st.multiselect`

**Signature**
```python
st.multiselect(label: 'str', options: 'Sequence', default: 'Sequence | None' = None, format_func: 'Callable | None' = None, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, max_selections: 'int | None' = None, placeholder: 'str | None' = None, disabled: 'bool' = False, label_visibility: 'str' = 'visible', accept_new_options: 'bool' = False, width: 'str | int' = 'stretch') -> 'list'
```

**Parameters**
- `label`: `str` (default: `required`)
- `options`: `Sequence` (default: `required`)
- `default`: `Sequence | None` (default: `None`)
- `format_func`: `Callable | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `max_selections`: `int | None` (default: `None`)
- `placeholder`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `accept_new_options`: `bool` (default: `False`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
tags = st.multiselect("Tags", ["a", "b", "c"])
```

## `st.navigation`

**Signature**
```python
st.navigation(pages: 'Sequence[str]', *, key: 'str | None' = None) -> 'str'
```

**Parameters**
- `pages`: `Sequence[str]` (default: `required`)
- `key`: `str | None` (default: `None`)

**Example**
```python
page = st.navigation(["Home", "Data"])
```

## `st.number_input`

**Signature**
```python
st.number_input(label: 'str', min_value: 'float | None' = None, max_value: 'float | None' = None, value: 'float | int | str' = 'min', step: 'float | None' = None, format: 'str | None' = None, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, placeholder: 'str | None' = None, disabled: 'bool' = False, label_visibility: 'str' = 'visible', icon: 'str | None' = None, width: 'str | int' = 'stretch') -> 'float | int'
```

**Parameters**
- `label`: `str` (default: `required`)
- `min_value`: `float | None` (default: `None`)
- `max_value`: `float | None` (default: `None`)
- `value`: `float | int | str` (default: `'min'`)
- `step`: `float | None` (default: `None`)
- `format`: `str | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `placeholder`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `icon`: `str | None` (default: `None`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
n = st.number_input("Count", min_value=0, value=1)
```

## `st.on_shutdown`

**Signature**
```python
st.on_shutdown(fn)
```

**Parameters**
- `fn`: `Any` (default: `required`)

**Example**
```python
@st.on_shutdown
def cleanup(): pass
```

## `st.on_startup`

**Signature**
```python
st.on_startup(fn)
```

**Parameters**
- `fn`: `Any` (default: `required`)

**Example**
```python
@st.on_startup
def init(): pass
```

## `st.page_link`

**Signature**
```python
st.page_link(page: 'str', *, label: 'str | None' = None, icon: 'str | None' = None, help: 'str | None' = None, disabled: 'bool' = False, use_container_width: 'bool' = False) -> 'None'
```

**Parameters**
- `page`: `str` (default: `required`)
- `label`: `str | None` (default: `None`)
- `icon`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `use_container_width`: `bool` (default: `False`)

**Example**
```python
st.page_link("value", label="Example", icon="value", help="value", disabled=False, use_container_width=False)
```

## `st.pdf`

**Signature**
```python
st.pdf(data: 'Any', *, width: 'int | None' = None, height: 'int | None' = None, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `data`: `Any` (default: `required`)
- `width`: `int | None` (default: `None`)
- `height`: `int | None` (default: `None`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.pdf("path/to/file.pdf")
```

## `st.pills`

**Signature**
```python
st.pills(label: 'str', options: 'Sequence', *, selection_mode: 'str' = 'single', default: 'Any | Sequence | None' = None, format_func: 'Callable | None' = None, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, disabled: 'bool' = False, label_visibility: 'str' = 'visible') -> 'Any'
```

**Parameters**
- `label`: `str` (default: `required`)
- `options`: `Sequence` (default: `required`)
- `selection_mode`: `str` (default: `'single'`)
- `default`: `Any | Sequence | None` (default: `None`)
- `format_func`: `Callable | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)

**Example**
```python
selected = st.pills("Category", ["A", "B", "C"])
```

## `st.plotly_chart`

**Signature**
```python
st.plotly_chart(figure_or_data: 'Any', *, use_container_width: 'bool' = True, theme: 'str | None' = 'streamlit', on_select: 'Any' = None, key: 'str | None' = None) -> 'list[int] | None'
```

**Parameters**
- `figure_or_data`: `Any` (default: `required`)
- `use_container_width`: `bool` (default: `True`)
- `theme`: `str | None` (default: `'streamlit'`)
- `on_select`: `Any` (default: `None`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.plotly_chart({"x": [1, 2], "y": [3, 4]}, use_container_width=False, theme="value", on_select=None, key="demo_key")
```

## `st.popover`

**Signature**
```python
st.popover(label: 'str', *, type: 'str' = 'secondary', help: 'str | None' = None, disabled: 'bool' = False, use_container_width: 'bool | None' = None, key: 'str | None' = None) -> 'Popover'
```

**Parameters**
- `label`: `str` (default: `required`)
- `type`: `str` (default: `'secondary'`)
- `help`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `use_container_width`: `bool | None` (default: `None`)
- `key`: `str | None` (default: `None`)

**Example**
```python
with st.popover("Settings"): st.toggle("Enable")
```

## `st.progress`

**Signature**
```python
st.progress(value: 'float | int', text: 'str | None' = None, *, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `value`: `float | int` (default: `required`)
- `text`: `str | None` (default: `None`)
- `key`: `str | None` (default: `None`)

**Example**
```python
p = st.progress(10)
```

## `st.pydeck_chart`

**Signature**
```python
st.pydeck_chart(pydeck_obj: 'Any' = None, *, use_container_width: 'bool' = True, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `pydeck_obj`: `Any` (default: `None`)
- `use_container_width`: `bool` (default: `True`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.pydeck_chart(pydeck_obj=None, use_container_width=False, key="demo_key")
```

## `st.pyplot`

**Signature**
```python
st.pyplot(fig: 'Any' = None, *, clear_figure: 'bool' = True, use_container_width: 'bool' = True, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `fig`: `Any` (default: `None`)
- `clear_figure`: `bool` (default: `True`)
- `use_container_width`: `bool` (default: `True`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.pyplot(fig={}, clear_figure={}, use_container_width=False, key="demo_key")
```

## `st.radio`

**Signature**
```python
st.radio(label: 'str', options: 'Sequence', index: 'int | None' = 0, format_func: 'Callable | None' = None, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, disabled: 'bool' = False, horizontal: 'bool' = False, captions: 'Sequence[str] | None' = None, label_visibility: 'str' = 'visible', width: 'str | int' = 'content') -> 'Any | None'
```

**Parameters**
- `label`: `str` (default: `required`)
- `options`: `Sequence` (default: `required`)
- `index`: `int | None` (default: `0`)
- `format_func`: `Callable | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `horizontal`: `bool` (default: `False`)
- `captions`: `Sequence[str] | None` (default: `None`)
- `label_visibility`: `str` (default: `'visible'`)
- `width`: `str | int` (default: `'content'`)

**Example**
```python
mode = st.radio("Mode", ["A", "B"])
```

## `st.rerun`

**Signature**
```python
st.rerun() -> 'None'
```

**Parameters**
- No parameters.

**Example**
```python
st.rerun()
```

## `st.run_in_thread`

**Signature**
```python
st.run_in_thread(fn: 'Callable', *args: 'Any', **kwargs: 'Any') -> 'threading.Thread'
```

**Parameters**
- `fn`: `Callable` (default: `required`)
- `args`: `Any` (default: `required`)
- `kwargs`: `Any` (default: `required`)

**Example**
```python
t = st.run_in_thread(lambda: 42)
```

## `st.run_with_session_context`

**Signature**
```python
st.run_with_session_context(fn: 'Callable', *args: 'Any', **kwargs: 'Any') -> 'Any'
```

**Parameters**
- `fn`: `Callable` (default: `required`)
- `args`: `Any` (default: `required`)
- `kwargs`: `Any` (default: `required`)

**Example**
```python
st.run_with_session_context(my_fn, arg1)
```

## `st.scatter_chart`

**Signature**
```python
st.scatter_chart(data: 'Any', *, x: 'str | None' = None, y: 'str | None' = None, color: 'str | None' = None, size: 'str | None' = None, width: 'int | None' = None, height: 'int | None' = None, use_container_width: 'bool' = True) -> 'None'
```

**Parameters**
- `data`: `Any` (default: `required`)
- `x`: `str | None` (default: `None`)
- `y`: `str | None` (default: `None`)
- `color`: `str | None` (default: `None`)
- `size`: `str | None` (default: `None`)
- `width`: `int | None` (default: `None`)
- `height`: `int | None` (default: `None`)
- `use_container_width`: `bool` (default: `True`)

**Example**
```python
st.scatter_chart({"x": [1, 2, 3], "y": [3, 2, 5]})
```

## `st.segmented_control`

**Signature**
```python
st.segmented_control(label: 'str', options: 'Sequence', *, default: 'Any | None' = None, format_func: 'Callable | None' = None, selection_mode: 'str' = 'single', key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, disabled: 'bool' = False, label_visibility: 'str' = 'visible') -> 'Any'
```

**Parameters**
- `label`: `str` (default: `required`)
- `options`: `Sequence` (default: `required`)
- `default`: `Any | None` (default: `None`)
- `format_func`: `Callable | None` (default: `None`)
- `selection_mode`: `str` (default: `'single'`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)

**Example**
```python
view = st.segmented_control("View", ["Table", "Chart"])
```

## `st.select_slider`

**Signature**
```python
st.select_slider(label: 'str', options: 'Sequence' = (), value: 'Any | tuple[Any, Any] | None' = None, format_func: 'Callable | None' = None, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, disabled: 'bool' = False, label_visibility: 'str' = 'visible', width: 'str | int' = 'stretch') -> 'Any | tuple[Any, Any]'
```

**Parameters**
- `label`: `str` (default: `required`)
- `options`: `Sequence` (default: `()`)
- `value`: `Any | tuple[Any, Any] | None` (default: `None`)
- `format_func`: `Callable | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
size = st.select_slider("Size", ["S", "M", "L"], value="M")
```

## `st.selectbox`

**Signature**
```python
st.selectbox(label: 'str', options: 'Sequence', index: 'int | None' = 0, format_func: 'Callable | None' = None, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, placeholder: 'str | None' = None, disabled: 'bool' = False, label_visibility: 'str' = 'visible', accept_new_options: 'bool' = False, width: 'str | int' = 'stretch') -> 'Any | None'
```

**Parameters**
- `label`: `str` (default: `required`)
- `options`: `Sequence` (default: `required`)
- `index`: `int | None` (default: `0`)
- `format_func`: `Callable | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `placeholder`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `accept_new_options`: `bool` (default: `False`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
choice = st.selectbox("Language", ["Python", "JS"])
```

## `st.set_page_config`

**Signature**
```python
st.set_page_config(page_title: 'str | None' = None, page_icon: 'str | None' = None, layout: 'str' = 'centered', initial_sidebar_state: 'str' = 'auto', menu_items: 'dict | None' = None) -> 'None'
```

**Parameters**
- `page_title`: `str | None` (default: `None`)
- `page_icon`: `str | None` (default: `None`)
- `layout`: `str` (default: `'centered'`)
- `initial_sidebar_state`: `str` (default: `'auto'`)
- `menu_items`: `dict | None` (default: `None`)

**Example**
```python
st.set_page_config(page_title="Demo", layout="wide")
```

## `st.set_sidebar_state`

**Signature**
```python
st.set_sidebar_state(state: 'str') -> 'None'
```

**Parameters**
- `state`: `str` (default: `required`)

**Example**
```python
st.set_sidebar_state("collapsed")
```

## `st.slider`

**Signature**
```python
st.slider(label: 'str', min_value: 'float | None' = None, max_value: 'float | None' = None, value: 'float | tuple[float, float] | None' = None, step: 'float | None' = None, format: 'str | None' = None, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, disabled: 'bool' = False, label_visibility: 'str' = 'visible', width: 'str | int' = 'stretch') -> "'float | int | tuple[float, float] | tuple[int, int]'"
```

**Parameters**
- `label`: `str` (default: `required`)
- `min_value`: `float | None` (default: `None`)
- `max_value`: `float | None` (default: `None`)
- `value`: `float | tuple[float, float] | None` (default: `None`)
- `step`: `float | None` (default: `None`)
- `format`: `str | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
value = st.slider("Volume", 0, 100, 50)
```

## `st.snow`

**Signature**
```python
st.snow() -> 'None'
```

**Parameters**
- No parameters.

**Example**
```python
st.snow()
```

## `st.spinner`

**Signature**
```python
st.spinner(text: 'str' = 'Loading...') -> 'Generator[None, None, None]'
```

**Parameters**
- `text`: `str` (default: `'Loading...'`)

**Example**
```python
with st.spinner("Loading..."): pass
```

## `st.status`

**Signature**
```python
st.status(label: 'str', *, expanded: 'bool' = True, state: 'str' = 'running') -> "Generator['StatusContainer', None, None]"
```

**Parameters**
- `label`: `str` (default: `required`)
- `expanded`: `bool` (default: `True`)
- `state`: `str` (default: `'running'`)

**Example**
```python
with st.status("Working...") as s:
    s.update(state="complete", label="Done")
```

## `st.stop`

**Signature**
```python
st.stop() -> 'None'
```

**Parameters**
- No parameters.

**Example**
```python
st.stop()
```

## `st.subheader`

**Signature**
```python
st.subheader(body: 'str', anchor: 'str | bool | None' = None, *, divider: 'bool | str' = False, help: 'str | None' = None, width: 'str | int' = 'stretch', text_alignment: 'str' = 'left') -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `anchor`: `str | bool | None` (default: `None`)
- `divider`: `bool | str` (default: `False`)
- `help`: `str | None` (default: `None`)
- `width`: `str | int` (default: `'stretch'`)
- `text_alignment`: `str` (default: `'left'`)

**Example**
```python
st.subheader("Subsection")
```

## `st.success`

**Signature**
```python
st.success(body: 'str', *, icon: 'str | None' = None) -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `icon`: `str | None` (default: `None`)

**Example**
```python
st.success("Saved")
```

## `st.switch_page`

**Signature**
```python
st.switch_page(page: 'str') -> 'None'
```

**Parameters**
- `page`: `str` (default: `required`)

**Example**
```python
st.switch_page("Home")
```

## `st.table`

**Signature**
```python
st.table(data: 'Any', *, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `data`: `Any` (default: `required`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.table({"a": [1, 2], "b": [3, 4]})
```

## `st.tabs`

**Signature**
```python
st.tabs(tab_labels: 'Sequence[str]', *, default: 'str | None' = None, key: 'str | None' = None) -> 'list[Tab]'
```

**Parameters**
- `tab_labels`: `Sequence[str]` (default: `required`)
- `default`: `str | None` (default: `None`)
- `key`: `str | None` (default: `None`)

**Example**
```python
tab1, tab2 = st.tabs(["A", "B"])
```

## `st.text`

**Signature**
```python
st.text(body: 'str', *, help: 'str | None' = None, width: 'str | int' = 'content', text_alignment: 'str' = 'left') -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `help`: `str | None` (default: `None`)
- `width`: `str | int` (default: `'content'`)
- `text_alignment`: `str` (default: `'left'`)

**Example**
```python
st.text("Raw monospace text")
```

## `st.text_area`

**Signature**
```python
st.text_area(label: 'str', value: 'str' = '', height: 'str | int | None' = None, max_chars: 'int | None' = None, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, placeholder: 'str | None' = None, disabled: 'bool' = False, label_visibility: 'str' = 'visible', width: 'str | int' = 'stretch') -> 'str'
```

**Parameters**
- `label`: `str` (default: `required`)
- `value`: `str` (default: `''`)
- `height`: `str | int | None` (default: `None`)
- `max_chars`: `int | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `placeholder`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
bio = st.text_area("Bio")
```

## `st.text_input`

**Signature**
```python
st.text_input(label: 'str', value: 'str' = '', max_chars: 'int | None' = None, key: 'str | None' = None, type: 'str' = 'default', help: 'str | None' = None, autocomplete: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, placeholder: 'str | None' = None, disabled: 'bool' = False, label_visibility: 'str' = 'visible', icon: 'str | None' = None, width: 'str | int' = 'stretch') -> 'str'
```

**Parameters**
- `label`: `str` (default: `required`)
- `value`: `str` (default: `''`)
- `max_chars`: `int | None` (default: `None`)
- `key`: `str | None` (default: `None`)
- `type`: `str` (default: `'default'`)
- `help`: `str | None` (default: `None`)
- `autocomplete`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `placeholder`: `str | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `icon`: `str | None` (default: `None`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
name = st.text_input("Name", placeholder="Your name")
```

## `st.time_input`

**Signature**
```python
st.time_input(label: 'str', value: 'datetime.time | str | None' = 'now', key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, step: 'int' = 900, disabled: 'bool' = False, label_visibility: 'str' = 'visible', width: 'str | int' = 'stretch') -> 'datetime.time | None'
```

**Parameters**
- `label`: `str` (default: `required`)
- `value`: `datetime.time | str | None` (default: `'now'`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `step`: `int` (default: `900`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `width`: `str | int` (default: `'stretch'`)

**Example**
```python
when = st.time_input('Time')
```

## `st.title`

**Signature**
```python
st.title(body: 'str', anchor: 'str | bool | None' = None, *, help: 'str | None' = None, width: 'str | int' = 'stretch', text_alignment: 'str' = 'left') -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `anchor`: `str | bool | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `width`: `str | int` (default: `'stretch'`)
- `text_alignment`: `str` (default: `'left'`)

**Example**
```python
st.title("My App")
```

## `st.toast`

**Signature**
```python
st.toast(body: 'str', *, icon: 'str | None' = None) -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `icon`: `str | None` (default: `None`)

**Example**
```python
st.toast("Done", icon="✅")
```

## `st.toggle`

**Signature**
```python
st.toggle(label: 'str', value: 'bool' = False, key: 'str | None' = None, help: 'str | None' = None, on_change: 'Callable | None' = None, args: 'list | tuple | None' = None, kwargs: 'dict | None' = None, *, disabled: 'bool' = False, label_visibility: 'str' = 'visible', width: 'str | int' = 'content') -> 'bool'
```

**Parameters**
- `label`: `str` (default: `required`)
- `value`: `bool` (default: `False`)
- `key`: `str | None` (default: `None`)
- `help`: `str | None` (default: `None`)
- `on_change`: `Callable | None` (default: `None`)
- `args`: `list | tuple | None` (default: `None`)
- `kwargs`: `dict | None` (default: `None`)
- `disabled`: `bool` (default: `False`)
- `label_visibility`: `str` (default: `'visible'`)
- `width`: `str | int` (default: `'content'`)

**Example**
```python
dark = st.toggle("Dark mode")
```

## `st.vega_lite_chart`

**Signature**
```python
st.vega_lite_chart(data: 'Any' = None, spec: 'dict | None' = None, *, use_container_width: 'bool' = True, theme: 'str | None' = 'streamlit', key: 'str | None' = None) -> 'None'
```

**Parameters**
- `data`: `Any` (default: `None`)
- `spec`: `dict | None` (default: `None`)
- `use_container_width`: `bool` (default: `True`)
- `theme`: `str | None` (default: `'streamlit'`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.vega_lite_chart(data={"x": [1, 2], "y": [3, 4]}, spec={"a": 1}, use_container_width=False, theme="value", key="demo_key")
```

## `st.video`

**Signature**
```python
st.video(data: 'Any', format: 'str' = 'video/mp4', start_time: 'int' = 0, *, subtitles: 'dict | None' = None, end_time: 'int | None' = None, loop: 'bool' = False, autoplay: 'bool' = False, muted: 'bool' = False, key: 'str | None' = None) -> 'None'
```

**Parameters**
- `data`: `Any` (default: `required`)
- `format`: `str` (default: `'video/mp4'`)
- `start_time`: `int` (default: `0`)
- `subtitles`: `dict | None` (default: `None`)
- `end_time`: `int | None` (default: `None`)
- `loop`: `bool` (default: `False`)
- `autoplay`: `bool` (default: `False`)
- `muted`: `bool` (default: `False`)
- `key`: `str | None` (default: `None`)

**Example**
```python
st.video("path/to/video.mp4")
```

## `st.warning`

**Signature**
```python
st.warning(body: 'str', *, icon: 'str | None' = None) -> 'None'
```

**Parameters**
- `body`: `str` (default: `required`)
- `icon`: `str | None` (default: `None`)

**Example**
```python
st.warning("Be careful")
```

## `st.write`

**Signature**
```python
st.write(*args: 'Any', unsafe_allow_html: 'bool' = False) -> 'None'
```

**Parameters**
- `args`: `Any` (default: `required`)
- `unsafe_allow_html`: `bool` (default: `False`)

**Example**
```python
st.write("Hello", {"a": 1})
```

## `st.write_stream`

**Signature**
```python
st.write_stream(stream: 'Any') -> 'str'
```

**Parameters**
- `stream`: `Any` (default: `required`)

**Example**
```python
st.write_stream(iter(['Hello ', 'world']))
```
