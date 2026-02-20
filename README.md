# Fastlit

**Streamlit-compatible, blazing fast, Python-first UI framework**

Fastlit is a high-performance alternative to Streamlit with the same familiar `st.*` API. Build interactive data apps in Python with instant UI updates, virtualized DataFrames, and modern React components.

## Why Fastlit?

Streamlit is great for prototyping, but its "rerun the entire script" model becomes costly when you have:

- Rich pages with many components
- Large DataFrames (50k+ rows)
- Frequent interactions (sliders, filters)
- Repetitive computations
- Multi-user production deployments

Fastlit keeps the same simplicity but with a runtime that:

- **Sends incremental patches** instead of full page refreshes
- **Reduces recomputation** with smart caching
- **Optimizes heavy renders** (tables, charts) with virtualization
- **Provides instant feedback** with React-first architecture

## Features

| Feature | Description |
|---------|-------------|
| **Streamlit API** | Same `st.*` syntax — drop-in replacement for most apps |
| **Diff/Patch UI** | Only changed elements are sent via WebSocket |
| **Virtualized DataFrames** | Smooth scrolling for millions of rows |
| **Server-side DataFrame Paging** | Large tables stream row windows from backend |
| **Multi-level Cache** | `@cache_data` (TTL+LRU) and `@cache_resource` (singleton) |
| **Rerun Guardrails** | Max sessions, bounded concurrent runs, run timeout |
| **WS Backpressure** | Bounded per-session queue + event coalescing |
| **Runtime Metrics** | Built-in `/_fastlit/metrics` endpoint |
| **Hot Reload** | Backend + frontend HMR in dev mode |
| **Modern UI** | Tailwind CSS + Radix UI + shadcn components |
| **Instant Widgets** | Slider/input updates without server roundtrip |
| **Multi-page Navigation** | Built-in page routing with cache |

## Installation

```bash
pip install fastlit
```

**Requirements:** Python 3.11+

## Quick Start

Create `app.py`:

```python
import fastlit as st

st.title("My First Fastlit App")

name = st.text_input("What's your name?", placeholder="Enter your name...")
st.write(f"Hello, {name}!")

n = st.slider("Pick a number", 1, 100, 50)
st.write(f"You selected: {n}")

if st.button("Click me!"):
    st.balloons()
    st.success("Button clicked!")
```

Run it:

```bash
fastlit run app.py
```

Development mode with hot reload:

```bash
fastlit run app.py --dev
```

Production profile (example):

```bash
fastlit run app.py --host 0.0.0.0 --port 8501 --workers 4 --limit-concurrency 200 --backlog 2048 --max-sessions 300 --max-concurrent-runs 8 --run-timeout-seconds 45
```

Open http://localhost:8501 in your browser.

---

## Table of Contents

- [Text Elements](#text-elements)
- [Auto-generated API Reference](#auto-generated-api-reference)
- [Input Widgets](#input-widgets)
- [Layout Components](#layout-components)
- [Data Display](#data-display)
- [Charts](#charts)
- [Media](#media)
- [Status Elements](#status-elements)
- [Chat Components](#chat-components)
- [State Management](#state-management)
- [Caching](#caching)
- [Control Flow](#control-flow)
- [Page Configuration](#page-configuration)
- [Advanced Features](#advanced-features)
- [Architecture](#architecture)
- [CLI Reference](#cli-reference)
- [Configuration](#configuration)
- [Deployment](#deployment)

---

## Auto-generated API Reference

For exact signatures and parameter defaults of every `st.*` function, use:

- `docs/API_REFERENCE.md`

This file is generated from real Python signatures (source of truth):

```bash
python scripts/generate_api_reference.py
```

---

## Text Elements

### st.title()

Display a large title (h1).

```python
st.title(
    body,                      # str: The title text (supports Markdown)
    anchor=None,               # str | bool | None: Custom anchor ID, False to disable
    *,
    help=None,                 # str | None: Tooltip text
    width="stretch",           # str | int: "stretch", "content", or pixel value
    text_alignment="left",     # str: "left", "center", "right", "justify"
)
```

**Example:**
```python
st.title("Welcome to My App")
st.title("Centered Title", text_alignment="center")
```

### st.header()

Display a section header (h2).

```python
st.header(
    body,                      # str: The header text
    anchor=None,               # str | bool | None: Custom anchor ID
    *,
    divider=False,             # bool | str: Show divider ("blue", "green", "orange", "red", "violet", "rainbow")
    help=None,                 # str | None: Tooltip text
    width="stretch",
    text_alignment="left",
)
```

**Example:**
```python
st.header("Data Analysis", divider="blue")
st.header("Results", divider="rainbow")
```

### st.subheader()

Display a subsection header (h3).

```python
st.subheader(
    body,
    anchor=None,
    *,
    divider=False,
    help=None,
    width="stretch",
    text_alignment="left",
)
```

### st.markdown()

Display Markdown-formatted text with support for GitHub-flavored Markdown, emoji shortcodes, and LaTeX.

```python
st.markdown(
    body,                      # str: Markdown text
    *,
    unsafe_allow_html=False,   # bool: Allow raw HTML (use with caution)
    help=None,
    width="stretch",
    text_alignment="left",
)
```

**Example:**
```python
st.markdown("**Bold**, *italic*, `code`")
st.markdown("Emoji: :rocket: :fire:")
st.markdown("Math: $E = mc^2$")
st.markdown(":blue[Colored text] and :red-background[highlighted]")
```

### st.write()

Smart content renderer with automatic type detection.

```python
st.write(*args, unsafe_allow_html=False)
```

**Supported types:**
- `str` → Markdown
- `dict`, `list` → JSON viewer
- `pd.DataFrame` → Interactive dataframe
- `Exception` → Error with traceback
- Plotly/Altair/Matplotlib figures → Charts

**Example:**
```python
st.write("Hello", {"key": "value"}, my_dataframe)
```

### st.text()

Display fixed-width monospace text.

```python
st.text(
    body,                      # str: Text to display
    *,
    help=None,
    width="content",
    text_alignment="left",
)
```

### st.code()

Display a code block with syntax highlighting.

```python
st.code(
    body,                      # str: Code to display
    language="python",         # str | None: Language for highlighting
    line_numbers=False,        # bool: Show line numbers
    *,
    wrap_lines=False,          # bool: Wrap long lines
    height="content",          # str | int: Height
    width="stretch",
)
```

**Example:**
```python
st.code("""
def hello():
    return "Hello, World!"
""", language="python", line_numbers=True)
```

### st.caption()

Display small caption text.

```python
st.caption(
    body,
    *,
    unsafe_allow_html=False,
    help=None,
    width="stretch",
    text_alignment="left",
)
```

### st.latex()

Display mathematical equations using LaTeX.

```python
st.latex(
    body,                      # str: LaTeX expression (no delimiters needed)
    *,
    help=None,
    width="stretch",
)
```

**Example:**
```python
st.latex(r"E = mc^2")
st.latex(r"\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}")
```

### st.html()

Display raw HTML (sanitized for security).

```python
st.html(body, *, width="stretch")
```

### st.json()

Display JSON data with syntax highlighting and expand/collapse.

```python
st.json(
    body,                      # dict | list | str: JSON data
    *,
    expanded=True,             # bool | int: Expand all or to depth
)
```

### st.metric()

Display a KPI metric with optional delta indicator.

```python
st.metric(
    label,                     # str: Metric label
    value,                     # Any: Metric value
    delta=None,                # Any: Delta value (+/- indicator)
    delta_color="normal",      # str: "normal", "inverse", "off"
    help=None,
    label_visibility="visible",
    border=False,              # bool: Show border
)
```

**Example:**
```python
st.metric("Revenue", "$12,345", delta="+5.2%")
st.metric("Errors", 23, delta="-8%", delta_color="inverse")
```

### st.badge()

Display an inline badge/tag.

```python
st.badge(
    label,                     # str: Badge text
    *,
    color="blue",              # str: "blue", "green", "red", "orange", "violet", "yellow", "gray"
    icon=None,                 # str: Optional emoji
)
```

### st.echo()

Display code alongside its output.

```python
with st.echo():
    x = 10
    st.write(x)  # Shows both the code and "10"
```

### st.help()

Display documentation for a Python object.

```python
st.help(obj)  # Shows type, signature, and docstring
```

---

## Input Widgets

### st.button()

Display a clickable button.

```python
clicked = st.button(
    label,                     # str: Button label
    key=None,                  # str | None: Unique widget key
    help=None,                 # str | None: Tooltip
    on_click=None,             # Callable: Callback function
    args=None,                 # tuple: Callback arguments
    kwargs=None,               # dict: Callback keyword arguments
    *,
    type="secondary",          # str: "primary", "secondary", "tertiary"
    icon=None,                 # str: Emoji or icon name
    icon_position="left",      # str: "left" or "right"
    disabled=False,            # bool: Disable the button
    use_container_width=None,  # bool: Deprecated, use width
    width="content",           # str | int: "content", "stretch", or pixels
    shortcut=None,             # str: Keyboard shortcut (e.g., "Ctrl+K")
)
# Returns: bool - True if clicked
```

**Example:**
```python
if st.button("Submit", type="primary", icon="🚀"):
    st.success("Submitted!")

# With callback
def on_click():
    st.session_state.count += 1

st.button("Increment", on_click=on_click)
```

### st.link_button()

Display a button that opens a URL.

```python
st.link_button(
    label,                     # str: Button label
    url,                       # str: URL to open
    *,
    help=None,
    type="secondary",
    icon=None,
    disabled=False,
    use_container_width=False,
)
```

### st.download_button()

Display a download button.

```python
clicked = st.download_button(
    label,                     # str: Button label
    data,                      # str | bytes | file: Data to download
    file_name=None,            # str: Downloaded file name
    mime=None,                 # str: MIME type (auto-detected)
    key=None,
    help=None,
    on_click=None,
    args=None,
    kwargs=None,
    *,
    type="secondary",
    icon=None,
    disabled=False,
    use_container_width=False,
)
```

**Example:**
```python
csv = df.to_csv(index=False)
st.download_button("Download CSV", csv, "data.csv", "text/csv")
```

### st.checkbox()

Display a checkbox.

```python
checked = st.checkbox(
    label,                     # str: Checkbox label
    value=False,               # bool: Initial state
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    disabled=False,
    label_visibility="visible",  # str: "visible", "hidden", "collapsed"
    width="content",
)
# Returns: bool
```

### st.toggle()

Display an on/off switch.

```python
enabled = st.toggle(
    label,
    value=False,
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    disabled=False,
    label_visibility="visible",
    width="content",
)
# Returns: bool
```

### st.radio()

Display radio buttons.

```python
selected = st.radio(
    label,                     # str: Widget label
    options,                   # Sequence: List of options
    index=0,                   # int | None: Index of default selection
    format_func=None,          # Callable: Function to format labels
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    disabled=False,
    horizontal=False,          # bool: Arrange horizontally
    captions=None,             # Sequence[str]: Captions below each option
    label_visibility="visible",
    width="content",
)
# Returns: Selected option value
```

**Example:**
```python
lang = st.radio(
    "Select language",
    ["Python", "JavaScript", "Rust"],
    horizontal=True,
    captions=["Dynamic", "Web", "Fast"]
)
```

### st.selectbox()

Display a dropdown select.

```python
selected = st.selectbox(
    label,
    options,
    index=0,                   # int | None: Default index, None for empty
    format_func=None,
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    placeholder=None,          # str: Placeholder text
    disabled=False,
    label_visibility="visible",
    accept_new_options=False,  # bool: Allow user to add new options
    width="stretch",
)
# Returns: Selected option value or None
```

### st.multiselect()

Display a multi-select dropdown.

```python
selected = st.multiselect(
    label,
    options,
    default=None,              # Sequence: Default selected values
    format_func=None,
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    max_selections=None,       # int: Maximum selections allowed
    placeholder="Select...",
    disabled=False,
    label_visibility="visible",
    accept_new_options=False,
    width="stretch",
)
# Returns: list of selected values
```

**Example:**
```python
skills = st.multiselect(
    "Select skills",
    ["Python", "SQL", "Docker", "AWS"],
    default=["Python"],
    max_selections=3
)
```

### st.slider()

Display a numeric slider.

```python
value = st.slider(
    label,
    min_value=None,            # float: Minimum (default: 0)
    max_value=None,            # float: Maximum (default: 100)
    value=None,                # float | tuple: Initial value(s)
    step=None,                 # float: Step increment
    format=None,               # str: Printf format (e.g., "%.2f", "percent")
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    disabled=False,
    label_visibility="visible",
    width="stretch",
)
# Returns: float/int or tuple for range slider
```

**Example:**
```python
# Single value
volume = st.slider("Volume", 0, 100, 50)

# Range slider
price_range = st.slider("Price range", 0.0, 1000.0, (100.0, 500.0))
lo, hi = price_range
```

### st.select_slider()

Display a slider with discrete options.

```python
value = st.select_slider(
    label,
    options=(),                # Sequence: Options to select from
    value=None,                # Any | tuple: Default value(s)
    format_func=None,
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    disabled=False,
    label_visibility="visible",
    width="stretch",
)
```

**Example:**
```python
size = st.select_slider("Size", ["XS", "S", "M", "L", "XL"], value="M")
```

### st.number_input()

Display a numeric input field.

```python
value = st.number_input(
    label,
    min_value=None,
    max_value=None,
    value="min",               # float | int | str: Initial value ("min" = min_value)
    step=None,                 # float: Step (1 for int, 0.01 for float)
    format=None,               # str: Printf format
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    placeholder=None,
    disabled=False,
    label_visibility="visible",
    icon=None,
    width="stretch",
)
# Returns: int or float
```

### st.text_input()

Display a single-line text input.

```python
value = st.text_input(
    label,
    value="",                  # str: Initial value
    max_chars=None,            # int: Maximum characters
    key=None,
    type="default",            # str: "default" or "password"
    help=None,
    autocomplete=None,         # str: HTML autocomplete attribute
    on_change=None,
    args=None,
    kwargs=None,
    *,
    placeholder=None,
    disabled=False,
    label_visibility="visible",
    icon=None,                 # str: Icon or "spinner"
    width="stretch",
)
# Returns: str
```

**Example:**
```python
name = st.text_input("Name", placeholder="Enter your name...")
password = st.text_input("Password", type="password")
```

### st.text_area()

Display a multi-line text input.

```python
value = st.text_area(
    label,
    value="",
    height=None,               # str | int: None (3 lines), "content", "stretch", or pixels
    max_chars=None,
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    placeholder=None,
    disabled=False,
    label_visibility="visible",
    width="stretch",
)
# Returns: str
```

### st.date_input()

Display a date picker.

```python
value = st.date_input(
    label,
    value="today",             # date | tuple | str | None: Default date(s)
    min_value=None,            # date: Minimum date
    max_value=None,            # date: Maximum date
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    format="YYYY/MM/DD",       # str: "YYYY/MM/DD", "DD/MM/YYYY", "MM/DD/YYYY"
    disabled=False,
    label_visibility="visible",
    width="stretch",
)
# Returns: date or tuple[date, date] for range
```

**Example:**
```python
import datetime

# Single date
date = st.date_input("Pick a date", datetime.date.today())

# Date range
start, end = st.date_input(
    "Select range",
    (datetime.date.today(), datetime.date.today() + datetime.timedelta(days=7))
)
```

### st.time_input()

Display a time picker.

```python
value = st.time_input(
    label,
    value="now",               # time | str | None: Default time
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    step=900,                  # int: Step in seconds (default: 15 min)
    disabled=False,
    label_visibility="visible",
    width="stretch",
)
# Returns: datetime.time
```

### st.color_picker()

Display a color picker.

```python
color = st.color_picker(
    label,
    value="#000000",           # str: Default color (hex)
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    disabled=False,
    label_visibility="visible",
    width="content",
)
# Returns: str (hex color)
```

### st.file_uploader()

Display a file upload widget.

```python
files = st.file_uploader(
    label,
    type=None,                 # str | list: Allowed extensions (e.g., ["csv", "txt"])
    accept_multiple_files=False,
    max_file_size_mb=None,     # int | None: Per-file max size in MB (default from FASTLIT_MAX_UPLOAD_MB)
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    *,
    disabled=False,
    label_visibility="visible",
    width="stretch",
)
# Returns: UploadedFile | list[UploadedFile] | None
```

**UploadedFile properties:**
- `name`: File name
- `type`: MIME type
- `size`: Size in bytes
- `read()`: Read content
- `getvalue()`: Get all bytes

**Upload limits:**
- Default max file size comes from `FASTLIT_MAX_UPLOAD_MB` (default: 10 MB)
- You can override per widget with `max_file_size_mb=...`

**Example:**
```python
uploaded = st.file_uploader("Upload CSV", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
    st.dataframe(df)
```

### st.camera_input()

Display a camera input for capturing photos.

```python
photo = st.camera_input(
    label,
    *,
    key=None,
    help=None,
    disabled=False,
    on_change=None,
    args=None,
    kwargs=None,
    label_visibility="visible",
)
# Returns: UploadedFile | None
```

### st.audio_input()

Display an audio recorder.

```python
audio = st.audio_input(
    label,
    *,
    key=None,
    help=None,
    disabled=False,
    on_change=None,
    args=None,
    kwargs=None,
    label_visibility="visible",
)
# Returns: UploadedFile | None
```

### st.feedback()

Display a feedback widget (thumbs, stars, faces).

```python
rating = st.feedback(
    sentiment_mapping=None,    # dict | str: "thumbs", "stars", "faces", or custom dict
    *,
    key=None,
    disabled=False,
    on_change=None,
    args=None,
    kwargs=None,
)
# Returns: int | None (selected index)
```

### st.pills()

Display a pill selector.

```python
selected = st.pills(
    label,
    options,
    *,
    selection_mode="single",   # str: "single" or "multi"
    default=None,
    format_func=None,
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    disabled=False,
    label_visibility="visible",
)
# Returns: value (single) or list (multi)
```

### st.segmented_control()

Display a segmented control (button group).

```python
selected = st.segmented_control(
    label,
    options,
    *,
    default=None,
    format_func=None,
    selection_mode="single",
    key=None,
    help=None,
    on_change=None,
    args=None,
    kwargs=None,
    disabled=False,
    label_visibility="visible",
)
```

---

## Layout Components

### st.sidebar

Container for sidebar content. Use as context manager or with attribute access.

```python
# Context manager
with st.sidebar:
    st.title("Sidebar")
    option = st.selectbox("Choose", ["A", "B", "C"])

# Attribute access
st.sidebar.title("Sidebar")
st.sidebar.selectbox("Choose", ["A", "B", "C"])
```

### st.columns()

Create horizontal columns.

```python
columns = st.columns(
    spec,                      # int | list: Number of columns or list of widths
    *,
    gap="small",               # str: "small", "medium", "large"
    vertical_alignment="top",  # str: "top", "center", "bottom"
    border=False,              # bool: Show border
    key=None,
)
# Returns: list[Column]
```

**Example:**
```python
# Equal columns
col1, col2, col3 = st.columns(3)
with col1:
    st.write("Column 1")
with col2:
    st.write("Column 2")
with col3:
    st.write("Column 3")

# Custom widths
left, right = st.columns([2, 1])  # 2:1 ratio
```

### st.tabs()

Create tabbed content.

```python
tabs = st.tabs(
    tab_labels,                # Sequence[str]: Tab labels
    *,
    default=None,              # str: Default selected tab
    key=None,
)
# Returns: list[Tab]
```

**Example:**
```python
tab1, tab2, tab3 = st.tabs(["Overview", "Data", "Settings"])

with tab1:
    st.write("Overview content")

with tab2:
    st.dataframe(df)

with tab3:
    st.write("Settings content")
```

### st.expander()

Create a collapsible section.

```python
expander = st.expander(
    label,                     # str: Expander label
    expanded=False,            # bool: Initially expanded
    *,
    icon=None,                 # str: Icon
    key=None,
)
# Returns: Expander context manager
```

**Example:**
```python
with st.expander("Click to see details"):
    st.write("Hidden content here")
    st.code("print('Hello')")
```

### st.container()

Create a generic container.

```python
container = st.container(
    *,
    border=None,               # bool: Show border
    key=None,
    height=None,               # int | str: Container height
)
```

**Example:**
```python
with st.container(border=True):
    st.write("Bordered content")
```

### st.empty()

Create a single-element placeholder that can be updated or cleared.

```python
placeholder = st.empty()
placeholder.write("Initial content")
# Later...
placeholder.write("Updated content")
placeholder.empty()  # Clear
```

### st.form()

Create a form that batches widget interactions.

```python
form = st.form(
    key,                       # str: Unique form key
    clear_on_submit=False,     # bool: Clear values after submit
    *,
    enter_to_submit=True,      # bool: Submit on Enter key
    border=True,               # bool: Show border
)
```

**Example:**
```python
with st.form("my_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0)
    submitted = st.form_submit_button("Submit")

if submitted:
    st.write(f"Name: {name}, Age: {age}")
```

### st.form_submit_button()

Display a form submit button (use inside `st.form()`).

```python
submitted = st.form_submit_button(
    label="Submit",
    *,
    help=None,
    on_click=None,
    args=None,
    kwargs=None,
    type="secondary",
    disabled=False,
    use_container_width=False,
    key=None,
)
# Returns: bool
```

### st.dialog()

Create a modal dialog (decorator).

```python
@st.dialog("Dialog Title", width="small")
def my_dialog():
    st.write("Dialog content")
    if st.button("Close"):
        st.rerun()

# Usage
if st.button("Open Dialog"):
    my_dialog()
```

### st.popover()

Create a popover triggered by a button.

```python
popover = st.popover(
    label,                     # str: Button label
    *,
    type="secondary",
    help=None,
    disabled=False,
    use_container_width=None,
    key=None,
)
```

**Example:**
```python
with st.popover("Settings"):
    st.checkbox("Enable feature")
    st.slider("Volume", 0, 100)
```

### st.divider()

Display a horizontal divider line.

```python
st.divider()
```

### st.navigation()

Display a navigation menu for multi-page apps.

```python
selected = st.navigation(
    pages,                     # Sequence[str]: Page names
    *,
    key=None,
)
# Returns: str (selected page name)
```

**Example:**
```python
page = st.sidebar.navigation(["Home", "Data", "Settings"])

if page == "Home":
    st.title("Home")
elif page == "Data":
    st.title("Data")
elif page == "Settings":
    st.title("Settings")
```

### st.switch_page()

Navigate to a different page programmatically.

```python
st.switch_page(page_name)  # str: Page name to switch to
```

### st.set_sidebar_state()

Control sidebar visibility programmatically.

```python
st.set_sidebar_state("collapsed")  # or "expanded"
```

---

## Data Display

### st.dataframe()

Display an interactive DataFrame with virtualization.

```python
st.dataframe(
    data,                      # DataFrame | dict | list: Data to display
    *,
    height=None,               # int: Height in pixels (auto-sizes up to 400px)
    use_container_width=True,  # bool: Stretch to container
    hide_index=False,          # bool: Hide row index
    max_rows=None,             # int | None: Max preview rows serialized in initial payload
    key=None,
)
```

For large pandas DataFrames, Fastlit can serve row windows from the backend via `/_fastlit/dataframe/{source_id}` to reduce initial payload size.

**Example:**
```python
import pandas as pd

df = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "City": ["Paris", "London", "Berlin"],
})

st.dataframe(df, height=300)
```

### st.data_editor()

Display an editable DataFrame.

```python
edited_df = st.data_editor(
    data,
    *,
    width=None,
    height=None,
    use_container_width=True,
    hide_index=None,
    column_order=None,         # list[str]: Column display order
    column_config=None,        # dict: Column configurations
    num_rows="fixed",          # str: "fixed" or "dynamic"
    disabled=False,            # bool | list[str]: Disable all or specific columns
    key=None,
    on_change=None,            # Callable: Callback when data changes
)
# Returns: Edited data
```

**Example:**
```python
edited = st.data_editor(
    df,
    num_rows="dynamic",
    column_config={
        "Age": st.column_config.NumberColumn("Age", min_value=0, max_value=120),
        "Active": st.column_config.CheckboxColumn("Active"),
    }
)
```

### Column Configuration

Configure columns for `st.data_editor()`:

```python
# Text column
st.column_config.TextColumn(label, max_chars=None, validate=None)

# Number column
st.column_config.NumberColumn(label, min_value=None, max_value=None, step=None, format=None)

# Checkbox column
st.column_config.CheckboxColumn(label)

# Selectbox column
st.column_config.SelectboxColumn(label, options=[])

# Date column
st.column_config.DateColumn(label, min_value=None, max_value=None, format=None)

# Time column
st.column_config.TimeColumn(label, min_value=None, max_value=None, format=None)

# Datetime column
st.column_config.DatetimeColumn(label, min_value=None, max_value=None, format=None, timezone=None)

# Progress column
st.column_config.ProgressColumn(label, min_value=0, max_value=100, format=None)

# Link column
st.column_config.LinkColumn(label, display_text=None, validate=None)

# Image column
st.column_config.ImageColumn(label)

# Line chart column
st.column_config.LineChartColumn(label, y_min=None, y_max=None)

# Bar chart column
st.column_config.BarChartColumn(label, y_min=None, y_max=None)

# List column
st.column_config.ListColumn(label)
```

### st.table()

Display a static table (for small data, no virtualization).

```python
st.table(data, *, key=None)
```

---

## Charts

### st.line_chart()

Display a line chart.

```python
st.line_chart(
    data,                      # DataFrame | dict | list
    *,
    x=None,                    # str: X-axis column (default: index)
    y=None,                    # str | list[str]: Y-axis column(s)
    color=None,                # str | list[str]: Line color(s)
    width=None,                # int: Width in pixels
    height=None,               # int: Height in pixels (default: 300)
    use_container_width=True,
)
```

**Example:**
```python
data = {
    "date": ["Jan", "Feb", "Mar", "Apr"],
    "sales": [100, 150, 120, 180],
    "profit": [20, 35, 25, 45],
}
st.line_chart(data, x="date", y=["sales", "profit"])
```

### st.bar_chart()

Display a bar chart.

```python
st.bar_chart(
    data,
    *,
    x=None,
    y=None,
    color=None,
    width=None,
    height=None,
    use_container_width=True,
    horizontal=False,          # bool: Horizontal bars
)
```

### st.area_chart()

Display an area chart.

```python
st.area_chart(
    data,
    *,
    x=None,
    y=None,
    color=None,
    width=None,
    height=None,
    use_container_width=True,
    stack=False,               # bool: Stack areas
)
```

### st.scatter_chart()

Display a scatter plot.

```python
st.scatter_chart(
    data,
    *,
    x=None,
    y=None,
    color=None,                # str: Color or column for color encoding
    size=None,                 # str: Column for point size
    width=None,
    height=None,
    use_container_width=True,
)
```

### st.map()

Display a map with points.

```python
st.map(
    data=None,                 # DataFrame | list: Data with lat/lon columns
    *,
    latitude=None,             # str: Latitude column name
    longitude=None,            # str: Longitude column name
    color=None,                # str: Marker color
    size=None,                 # str: Column for marker size
    zoom=None,                 # int: Initial zoom level
    use_container_width=True,
    height=None,               # int: Height (default: 400)
)
```

**Example:**
```python
locations = pd.DataFrame({
    "lat": [48.8566, 51.5074, 52.5200],
    "lon": [2.3522, -0.1278, 13.4050],
})
st.map(locations, zoom=4)
```

### st.plotly_chart()

Display a Plotly figure.

```python
selected = st.plotly_chart(
    figure_or_data,            # Plotly figure or dict
    *,
    use_container_width=True,
    theme="streamlit",         # str | None: Theme
    on_select=None,            # Callable: Selection callback
    key=None,
)
# Returns: list[int] | None if on_select is set
```

**Example:**
```python
import plotly.express as px

fig = px.scatter(df, x="x", y="y", color="category")
st.plotly_chart(fig)

# With selection
def on_select(indices):
    st.write(f"Selected: {indices}")

st.plotly_chart(fig, on_select=on_select)
```

### st.altair_chart()

Display an Altair chart.

```python
st.altair_chart(
    altair_chart,              # Altair chart object
    *,
    use_container_width=True,
    theme="streamlit",
    key=None,
)
```

### st.vega_lite_chart()

Display a Vega-Lite chart.

```python
st.vega_lite_chart(
    data=None,
    spec=None,                 # dict: Vega-Lite specification
    *,
    use_container_width=True,
    theme="streamlit",
    key=None,
)
```

### st.pyplot()

Display a Matplotlib figure.

```python
st.pyplot(
    fig=None,                  # Matplotlib figure (None = current figure)
    *,
    clear_figure=True,         # bool: Clear figure after rendering
    use_container_width=True,
    key=None,
)
```

### st.bokeh_chart()

Display a Bokeh chart.

```python
st.bokeh_chart(
    figure,                    # Bokeh figure
    *,
    use_container_width=True,
    key=None,
)
```

### st.graphviz_chart()

Display a Graphviz diagram.

```python
st.graphviz_chart(
    figure_or_dot,             # Graphviz object or DOT string
    *,
    use_container_width=True,
    key=None,
)
```

**Example:**
```python
st.graphviz_chart("""
    digraph {
        A -> B -> C
        B -> D
    }
""")
```

### st.pydeck_chart()

Display a PyDeck chart.

```python
st.pydeck_chart(
    pydeck_obj=None,           # PyDeck Deck object
    *,
    use_container_width=True,
    key=None,
)
```

---

## Media

### st.image()

Display an image.

```python
st.image(
    image,                     # str | bytes | PIL.Image | np.ndarray
    caption=None,              # str: Caption below image
    width=None,                # int: Width in pixels
    use_container_width="auto",  # bool | str: "auto", "always", "never"
    clamp=False,
    channels="RGB",            # str: "RGB" or "BGR"
    output_format="auto",      # str: "auto", "PNG", "JPEG"
    *,
    key=None,
)
```

**Example:**
```python
st.image("photo.jpg", caption="My photo", width=400)
st.image("https://example.com/image.png")
```

### st.audio()

Display an audio player.

```python
st.audio(
    data,                      # str | bytes | np.ndarray: Audio source
    format="audio/wav",        # str: MIME type
    start_time=0,              # int: Start time in seconds
    *,
    sample_rate=None,          # int: For numpy arrays
    end_time=None,
    loop=False,
    autoplay=False,
    key=None,
)
```

### st.video()

Display a video player.

```python
st.video(
    data,                      # str | bytes: Video source
    format="video/mp4",
    start_time=0,
    *,
    subtitles=None,            # dict: {label: subtitle_file_path}
    end_time=None,
    loop=False,
    autoplay=False,
    muted=False,
    key=None,
)
```

### st.logo()

Display an app logo (typically in sidebar).

```python
st.logo(
    image,                     # Image source
    *,
    size="medium",             # str: "small", "medium", "large"
    link=None,                 # str: URL to link to
    icon_image=None,           # Image: Smaller icon version
    key=None,
)
```

### st.pdf()

Display a PDF document.

```python
st.pdf(
    data,                      # str | bytes: PDF source
    *,
    width=None,
    height=None,               # int: Height (default: 600)
    key=None,
)
```

---

## Status Elements

### st.success() / st.info() / st.warning() / st.error()

Display alert messages.

```python
st.success(body, *, icon=None)
st.info(body, *, icon=None)
st.warning(body, *, icon=None)
st.error(body, *, icon=None)
```

**Example:**
```python
st.success("Operation completed!")
st.info("Here's some information")
st.warning("Be careful!")
st.error("Something went wrong")
```

### st.exception()

Display an exception with traceback.

```python
st.exception(exception=None)  # BaseException or None for current exception
```

### st.progress()

Display a progress bar.

```python
st.progress(
    value,                     # float | int: 0-100 or 0.0-1.0
    text=None,                 # str: Text above progress bar
    *,
    key=None,
)
```

### st.spinner()

Display a loading spinner (context manager).

```python
with st.spinner("Loading..."):
    # Do expensive work
    time.sleep(2)
```

### st.status()

Display an updatable status container.

```python
with st.status("Processing...", expanded=True) as status:
    st.write("Step 1...")
    # Do work
    st.write("Step 2...")
    status.update(label="Complete!", state="complete")
```

### st.toast()

Display a toast notification.

```python
st.toast(body, *, icon=None)
```

### st.balloons()

Display celebratory balloons animation.

```python
st.balloons()
```

### st.snow()

Display snowfall animation.

```python
st.snow()
```

---

## Chat Components

### st.chat_message()

Display a chat message bubble (context manager).

```python
message = st.chat_message(
    name,                      # str: "user", "assistant", "ai", "human", or custom
    *,
    avatar=None,               # str: Emoji, URL, or None for default
)
```

**Example:**
```python
with st.chat_message("user"):
    st.write("Hello!")

with st.chat_message("assistant", avatar="🤖"):
    st.write("Hi! How can I help?")
```

### st.chat_input()

Display a chat input widget (pinned to bottom).

```python
prompt = st.chat_input(
    placeholder="Type a message...",
    *,
    key=None,
    max_chars=None,
    disabled=False,
    on_submit=None,
    args=None,
    kwargs=None,
)
# Returns: str | None (one-shot, not persisted)
```

**Example:**
```python
if prompt := st.chat_input("Ask me anything"):
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        st.write(f"You said: {prompt}")
```

---

## State Management

### st.session_state

Session-scoped state dictionary with attribute access.

```python
# Initialize
if "counter" not in st.session_state:
    st.session_state.counter = 0

# Read
value = st.session_state.counter
value = st.session_state["counter"]

# Write
st.session_state.counter = 10
st.session_state["counter"] = 10

# Delete
del st.session_state.counter

# Clear all
st.session_state.clear()

# Dict methods
st.session_state.get("key", default)
st.session_state.keys()
st.session_state.values()
st.session_state.items()
```

### st.query_params

Access URL query parameters.

```python
# Read
page = st.query_params.get("page", "home")
page = st.query_params["page"]
page = st.query_params.page

# Write
st.query_params["page"] = "settings"

# All values for a key
values = st.query_params.get_all("tags")

# Convert to dict
params = st.query_params.to_dict()

# Clear
st.query_params.clear()
```

### st.secrets

Access secrets from `secrets.toml` or `.streamlit/secrets.toml`.

```python
# secrets.toml:
# [database]
# host = "localhost"
# password = "secret123"

host = st.secrets["database"]["host"]
host = st.secrets.database.host
```

### st.context

Access request context information.

```python
st.context.headers    # dict: HTTP headers
st.context.cookies    # dict: Cookies
st.context.ip_address # str: Client IP
st.context.locale     # str: Locale from Accept-Language
st.context.timezone   # str: Timezone hint
```

---

## Caching

### @st.cache_data

Cache function results with automatic invalidation.

```python
@st.cache_data(ttl=None, max_entries=1000, copy=True)
def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)
```

**Parameters:**
- `ttl`: Time-to-live in seconds (None = no expiry)
- `max_entries`: Maximum cache entries (LRU eviction)
- `copy`: Return deepcopy of cached value (default `True`). Set `copy=False` for immutable results to reduce overhead.

**Key generation:** Hash of function source + arguments

**Behavior:** Returns deep copy by default (mutation-safe). Use `copy=False` only when callers will not mutate the cached object.

**Clear cache:**
```python
load_data.clear()  # Clear this function's cache
st.cache_data.clear()  # Clear all cache_data caches
```

### @st.cache_resource

Cache resources (database connections, ML models) — singleton, no copy.

```python
@st.cache_resource
def get_database():
    return create_connection()

@st.cache_resource
def load_model():
    return load_heavy_model()
```

**Clear cache:**
```python
get_database.clear()
st.cache_resource.clear()
```

---

## Control Flow

### st.rerun()

Stop execution and rerun the script immediately.

```python
st.rerun()  # Raises RerunException
```

### st.stop()

Stop script execution (elements below won't render).

```python
if not authenticated:
    st.error("Please login")
    st.stop()

# This won't run if not authenticated
st.write("Secret content")
```

---

## Page Configuration

### st.set_page_config()

Configure page settings (must be first Streamlit command).

```python
st.set_page_config(
    page_title=None,           # str: Browser tab title
    page_icon=None,            # str: Favicon (emoji or URL)
    layout="centered",         # str: "centered", "wide", "compact"
    initial_sidebar_state="auto",  # str: "auto", "expanded", "collapsed"
    menu_items=None,           # dict: Custom menu items
)
```

**Example:**
```python
st.set_page_config(
    page_title="My App",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)
```

---

## Advanced Features

### Lifecycle Hooks

Register functions to run at server startup/shutdown.

```python
@st.on_startup
def init_resources():
    print("Server starting...")
    return create_db_pool()

@st.on_shutdown
async def cleanup_resources():
    print("Server shutting down...")
    await db_pool.close()
```

### Threading Support

Run functions in background threads with session context.

```python
def background_work():
    # st.* calls work here because session context is inherited
    result = expensive_computation()
    st.session_state.result = result

# Create thread with session context
t = st.run_in_thread(background_work)
t.start()
t.join()

# Or run directly in context
st.run_with_session_context(some_function, arg1, arg2)
```

### Real-time Widget Interpolation

Widget values can be interpolated in text without server roundtrip:

```python
n = st.slider("Value", 0, 100, 50)
st.write(f"You selected: {n}")  # Updates instantly as slider moves!
```

This works because widget values are wrapped in `WidgetValue` objects that inject markers for client-side interpolation.

---

## Architecture

```
┌─────────────────────────────┐       WebSocket        ┌─────────────────────────────┐
│     Backend (Python/ASGI)   │  ←─── events ────────→ │    Frontend (React/Vite)    │
│                             │  ←─── patches ───────→ │                             │
│  • Execute Python script    │                        │  • Render UI components     │
│  • Build UI tree            │                        │  • Apply incremental patches│
│  • Compute diff/patch       │                        │  • Emit widget events       │
│  • Manage session state     │                        │  • Virtualized rendering    │
│  • Handle caching           │                        │  • Real-time interpolation  │
└─────────────────────────────┘                        └─────────────────────────────┘
```

### How It Works

1. **Script Execution**: Your Python script runs, calling `st.*` functions
2. **UI Tree**: Each call creates a node with a stable ID (file:line:counter)
3. **Diff/Patch**: Fastlit computes the difference from the previous tree
4. **WebSocket**: Only the patch is sent (not the full tree)
5. **React Render**: Frontend applies patches with structural sharing
6. **Widget Events**: User interactions are debounced and sent back

### Performance Optimizations

- **Stable IDs**: Widgets keep identity across reruns (file:line:counter)
- **Debouncing**: Slider/input events debounced 150ms before sending
- **Event Coalescing**: Multiple rapid events merged server-side
- **Backpressure**: Bounded per-session event queue with drop-oldest policy
- **Page Caching**: Visited pages cached client-side for instant navigation
- **Virtualization**: DataFrames only render visible rows
- **Server Paging**: Large DataFrames fetch windows on demand
- **Patch Compaction**: Large render patches use compact op encoding (optional zlib)
- **Code Caching**: Compiled Python code cached by mtime

---

## CLI Reference

```bash
# Run an app
fastlit run app.py

# Development mode (hot reload)
fastlit run app.py --dev

# Basic network options
fastlit run app.py --port 8080 --host 0.0.0.0

# Production-oriented example
fastlit run app.py --host 0.0.0.0 --port 8501 --workers 4 --limit-concurrency 200 --backlog 2048 --max-sessions 300 --max-concurrent-runs 8 --run-timeout-seconds 45
```

Supported run options include:
- `--port`, `--host`, `--dev`
- `--workers`, `--limit-concurrency`, `--backlog`, `--timeout-keep-alive`
- `--max-sessions`, `--max-concurrent-runs`, `--run-timeout-seconds`

Runtime metrics endpoint:
- `GET /_fastlit/metrics`
- Disable via `FASTLIT_ENABLE_METRICS=0`

---

## Configuration

Create `fastlit.toml` in your project root:

```toml
[server]
port = 8501
host = "0.0.0.0"

[auth]
enabled = false
# provider = "oidc"
# issuer_url = "https://login.microsoftonline.com/<tenant>/v2.0"
# client_id = "..."
# client_secret = "..."
# redirect_url = "http://localhost:8501/auth/callback"
# scopes = ["openid", "profile", "email"]
```

### Secrets

Create `secrets.toml` or `.streamlit/secrets.toml`:

```toml
[database]
host = "localhost"
port = 5432
password = "secret"

[api]
key = "sk-..."
```

Access via `st.secrets.database.host` or `st.secrets["database"]["host"]`.

---

### Requirements

```
fastlit
pandas
# Add other dependencies
```

## Examples

### Basic Counter

```python
import fastlit as st

st.title("Counter App")

if "count" not in st.session_state:
    st.session_state.count = 0

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("➖ Decrement"):
        st.session_state.count -= 1

with col2:
    st.metric("Count", st.session_state.count)

with col3:
    if st.button("➕ Increment"):
        st.session_state.count += 1
```

### Data Explorer

```python
import fastlit as st
import pandas as pd

st.title("Data Explorer")

uploaded = st.file_uploader("Upload CSV", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    
    st.subheader("Data Preview")
    st.dataframe(df, height=400)
    
    st.subheader("Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        st.metric("Missing", df.isna().sum().sum())
    
    st.subheader("Column Analysis")
    column = st.selectbox("Select column", df.columns)
    st.bar_chart(df[column].value_counts())
```

### Chat Application

```python
import fastlit as st

st.title("Chat Bot")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
if prompt := st.chat_input("Type a message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Add bot response
    response = f"You said: {prompt}"
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    st.rerun()
```

### Multi-page App

```python
import fastlit as st

st.set_page_config(page_title="Multi-page App", layout="wide")

# Sidebar navigation
page = st.sidebar.navigation(["Home", "Data", "Settings"])

st.sidebar.divider()
st.sidebar.caption("v1.0.0")

# Page routing
if page == "Home":
    st.title("🏠 Home")
    st.write("Welcome to the app!")
    
elif page == "Data":
    st.title("📊 Data")
    st.dataframe({"A": [1, 2, 3], "B": [4, 5, 6]})
    
elif page == "Settings":
    st.title("⚙️ Settings")
    theme = st.selectbox("Theme", ["Light", "Dark"])
    notifications = st.toggle("Enable notifications")
```

---

## Migration from Streamlit

Most Streamlit apps work with Fastlit by changing the import:

```python
# Before
import streamlit as st

# After
import fastlit as st
```

### Differences to Note

1. **Widget Keys**: Fastlit uses file:line:counter for stable IDs. Explicit `key` parameters work the same.

2. **Rerun Behavior**: Some widgets (`slider`, `text_input`, etc.) update the UI instantly without triggering a full rerun, making the app feel more responsive.

3. **Session State**: Behaves identically to Streamlit.

4. **Caching**: Same API (`@st.cache_data`, `@st.cache_resource`) with similar behavior.

5. **Layout**: Same API with minor visual differences due to different CSS framework.

---

## Contributing

Contributions welcome! Please:

- Keep PRs focused and small
- Add tests for new features
- Follow existing code style
- Update documentation

---

**Fastlit** — Build data apps faster. ⚡
