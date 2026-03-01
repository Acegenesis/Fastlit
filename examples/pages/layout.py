"""Layout page for the Fastlit demo."""
import fastlit as st

PAGE_CONFIG = {
    "title": "Layout",
    "icon": "📐",
    "order": 80,
}

st.title("📐 Layout Components")
st.caption("Components for organizing content")

# -------------------------------------------------------------------------
# st.columns()
# -------------------------------------------------------------------------
st.header("st.columns()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `spec` (int | list): Number of equal columns or list of widths
    - `gap` (str): "small", "medium", "large"
    - `vertical_alignment` (str): "top", "center", "bottom"
    - `border` (bool): Show border around columns
    
    **Returns:** list[Column]
    """)

st.code('''# Equal columns
col1, col2, col3 = st.columns(3)
with col1:
st.info("Column 1")
with col2:
st.success("Column 2")
with col3:
st.warning("Column 3")

# Custom widths (2:1 ratio)
left, right = st.columns([2, 1])
with left:
st.info("Wide column (2)")
with right:
st.success("Narrow (1)")

# With gap options
a, b, c = st.columns(3, gap="large")
with a:
st.metric("A", 100)
with b:
st.metric("B", 200)
with c:
st.metric("C", 300)''', language="python")

with st.container(border=True):
    st.caption("Equal columns:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("Column 1")
    with col2:
        st.success("Column 2")
    with col3:
        st.warning("Column 3")
    
    st.caption("Custom widths (2:1 ratio):")
    left, right = st.columns([2, 1])
    with left:
        st.info("Wide column (2)")
    with right:
        st.success("Narrow (1)")
    
    st.caption("With gap options:")
    a, b, c = st.columns(3, gap="large")
    with a:
        st.metric("A", 100)
    with b:
        st.metric("B", 200)
    with c:
        st.metric("C", 300)

# -------------------------------------------------------------------------
# st.tabs()
# -------------------------------------------------------------------------
st.header("st.tabs()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `tab_labels` (Sequence[str]): Tab labels
    - `default` (str | None): Default selected tab
    
    **Returns:** list[Tab]
    """)

st.code('''tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Data", "⚙️ Settings"])

with tab1:
st.write("This is the overview tab.")
st.metric("Total", 1234)

with tab2:
st.write("This is the data tab.")
st.dataframe({"A": [1, 2, 3], "B": [4, 5, 6]})

with tab3:
st.write("This is the settings tab.")
st.checkbox("Enable feature")''', language="python")

with st.container(border=True):
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Data", "⚙️ Settings"])
    
    with tab1:
        st.write("This is the overview tab.")
        st.metric("Total", 1234)
    
    with tab2:
        st.write("This is the data tab.")
        st.dataframe({"A": [1, 2, 3], "B": [4, 5, 6]})
    
    with tab3:
        st.write("This is the settings tab.")
        st.checkbox("Enable feature")

# -------------------------------------------------------------------------
# st.expander()
# -------------------------------------------------------------------------
st.header("st.expander()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Expander label
    - `expanded` (bool): Initially expanded
    - `icon` (str | None): Icon
    
    **Returns:** Expander context manager
    """)

st.code('''with st.expander("Click to see more details"):
st.write("This content is hidden by default.")
st.code("print('Hello!')", language="python")

with st.expander("Already expanded", expanded=True):
st.write("This starts open.")''', language="python")

with st.container(border=True):
    with st.expander("Click to see more details"):
        st.write("This content is hidden by default.")
        st.code("print('Hello!')", language="python")
    
    with st.expander("Already expanded", expanded=True):
        st.write("This starts open.")

# -------------------------------------------------------------------------
# st.container()
# -------------------------------------------------------------------------
st.header("st.container()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `border` (bool | None): Show border
    - `height` (int | str | None): Container height
    
    **Returns:** Container context manager
    """)

st.code('''with st.container(border=True):
st.write("Content in a bordered container")
st.button("Button inside")

with st.container(border=True, height=100):
st.write("Fixed height container (100px)")
st.write("With scrolling if needed...")''', language="python")

with st.container(border=True):
    with st.container(border=True):
        st.write("Content in a bordered container")
        st.button("Button inside")
    
    with st.container(border=True, height=100):
        st.write("Fixed height container (100px)")
        st.write("With scrolling if needed...")

# -------------------------------------------------------------------------
# st.empty()
# -------------------------------------------------------------------------
st.header("st.empty()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Usage:** Create a single-element placeholder that can be updated or cleared.
    
    **Methods:**
    - `.write()`, `.markdown()`, etc.: Update content
    - `.empty()`: Clear content
    """)

st.code('''placeholder = st.empty()

if st.button("Show info"):
placeholder.info("This is info")
if st.button("Show success"):
placeholder.success("This is success")
if st.button("Clear"):
placeholder.empty()''', language="python")

with st.container(border=True):
    placeholder = st.empty()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Show info"):
            placeholder.info("This is info")
    with col2:
        if st.button("Show success"):
            placeholder.success("This is success")
    with col3:
        if st.button("Clear"):
            placeholder.empty()

# -------------------------------------------------------------------------
# st.form()
# -------------------------------------------------------------------------
st.header("st.form()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `key` (str): Unique form key
    - `clear_on_submit` (bool): Clear values after submit
    - `enter_to_submit` (bool): Submit on Enter key
    - `border` (bool): Show border
    
    Forms batch widget interactions until submitted.
    """)

st.code('''with st.form("demo_form", clear_on_submit=True):
name = st.text_input("Name", placeholder="Your name...")
email = st.text_input("Email", placeholder="your@email.com")
age = st.slider("Age", 18, 100, 25)
newsletter = st.checkbox("Subscribe to newsletter")
submitted = st.form_submit_button("Submit", type="primary")

if submitted:
st.success(f"Form submitted! Name: {name}, Email: {email}, Age: {age}")''', language="python")

with st.container(border=True):
    with st.form("demo_form", clear_on_submit=True):
        name = st.text_input("Name", placeholder="Your name...")
        email = st.text_input("Email", placeholder="your@email.com")
        age = st.slider("Age", 18, 100, 25)
        newsletter = st.checkbox("Subscribe to newsletter")
        submitted = st.form_submit_button("Submit", type="primary")
    
    if submitted:
        st.success(f"Form submitted! Name: {name}, Email: {email}, Age: {age}")

# -------------------------------------------------------------------------
# st.popover()
# -------------------------------------------------------------------------
st.header("st.popover()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Button label
    - `type` (str): Button type
    - `help` (str | None): Tooltip
    - `disabled` (bool): Disable
    - `use_container_width` (bool): Full width
    """)

st.code('''with st.popover("⚙️ Settings"):
st.write("Configure options:")
st.toggle("Dark mode")
st.slider("Volume", 0, 100, 50)
st.selectbox("Language", ["English", "French", "German"])''', language="python")

with st.container(border=True):
    with st.popover("⚙️ Settings"):
        st.write("Configure options:")
        st.toggle("Dark mode")
        st.slider("Volume", 0, 100, 50)
        st.selectbox("Language", ["English", "French", "German"])

# -------------------------------------------------------------------------
# st.dialog()
# -------------------------------------------------------------------------
st.header("st.dialog()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Usage:** Decorator to create modal dialogs.
    
    ```python
    @st.dialog("Title", width="small")
    def my_dialog():
        st.write("Content")
        if st.button("Close"):
            st.rerun()
    ```
    
    **Parameters:**
    - `title` (str): Dialog title
    - `width` (str): "small", "medium", "large"
    """)

st.code('''@st.dialog("Confirm Delete")
def confirm_dialog():
st.write("Are you sure?")
if st.button("Yes"):
    st.session_state.deleted = True
    st.rerun()

if st.button("Delete"):
confirm_dialog()''', language="python")

with st.container(border=True):
    st.info("Dialogs are created using the @st.dialog decorator")

# -------------------------------------------------------------------------
# st.Page()
# -------------------------------------------------------------------------
st.header("st.Page()", divider="blue")
has_page_api = hasattr(st, "Page")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Purpose:** Define page metadata for `st.navigation(...)`.

    **Parameters:**
    - `path` (str): Target script path
    - `title` (str | None): Display title
    - `icon` (str | None): Icon text/emoji
    - `url_path` (str | None): URL slug
    - `default` (bool): Default page

    **Methods:**
    - `.run()`: Render the page inline inside the current layout
    """)

st.code('''page_defs = [
st.Page("pages/index.py", title="Home", icon="🏠", url_path="index", default=True),
st.Page("pages/charts.py", title="Charts", icon="📈", url_path="charts"),
st.Page("pages/state_control.py", title="State Control", icon="🔄", url_path="state_control"),
]

selected_page = st.navigation(page_defs, key="layout_page_api_demo")
st.write(f"Selected: title={selected_page.title}, url_path={selected_page.url_path}")
# In a global layout:
# selected_page.run()''', language="python")

with st.container(border=True):
    if has_page_api:
        page_defs = [
            st.Page("pages/index.py", title="Home", icon="🏠", url_path="index", default=True),
            st.Page("pages/charts.py", title="Charts", icon="📈", url_path="charts"),
            st.Page("pages/state_control.py", title="State Control", icon="🔄", url_path="state_control"),
        ]

        selected_page = st.navigation(page_defs, key="layout_page_api_demo")
        st.write(f"Selected: title={selected_page.title}, url_path={selected_page.url_path}")
        st.caption("Page objects can also be rendered inline with `selected_page.run()`.")
    else:
        st.warning(
            "This runtime does not expose `st.Page` yet. "
            "Using compatibility fallback with string navigation."
        )
        selected_page = st.navigation(["Overview", "Data", "Settings"], key="layout_page_api_demo")
        st.write(f"Selected: {selected_page}")

# -------------------------------------------------------------------------
# st.navigation()
# -------------------------------------------------------------------------
st.header("st.navigation()", divider="blue")
st.caption("Supports file-based discovery, `Sequence[str]`, and `Sequence[st.Page]`.")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `pages` (Sequence[str | st.Page] | None): Optional page names or page definitions
    
        **Returns:** `str` in string mode, `st.Page` in Page mode
        
        If omitted, Fastlit auto-discovers `pages/*.py` next to your entry script.
        """)

    st.markdown(
        "Returns `str` in string mode and `st.Page` in Page mode. "
        "With auto-discovered `pages/`, the selected page is rendered implicitly by the entry script."
    )

    st.code('''# Auto-discover pages/*.py next to app.py
    st.navigation()''', language="python")

with st.container(border=True):
        st.info(
            "File-based navigation is active in the sidebar for this app. "
            "Add a file in `pages/` and Fastlit will pick it up automatically."
        )
        st.caption(
            "With auto-discovered `pages/`, `app.py` behaves like a global layout without an explicit page outlet."
        )

st.code('''current = st.navigation(["Home", "Data", "Settings"], key="nav_string_mode")
st.write(f"Current page: {current}")''', language="python")

with st.container(border=True):
    current = st.navigation(["Home", "Data", "Settings"], key="nav_string_mode")
    st.write(f"Current page: {current}")

# -------------------------------------------------------------------------
# st.switch_page()
# -------------------------------------------------------------------------
st.header("st.switch_page()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Programmatically switch to another page.

    **Parameters:**
    - `page` (str | st.Page): Target page slug/name or `st.Page` object

    **Behavior:**
    - Raises an internal navigation exception
    - Stops current execution and reruns on target page
    """)

st.code('''if st.button("Go to Charts page"):
st.switch_page("charts")

# Or with Page objects:
# st.switch_page(my_page_def)''', language="python")

with st.container(border=True):
    st.info(
        "Real page switch is optional in this demo to avoid accidental navigation."
    )
    enable_switch = st.toggle(
        "Enable real st.switch_page() call",
        value=False,
        key="switch_page_enable",
    )
    target_slug = st.selectbox(
        "Target route",
        options=["index", "new_in_fastlit", "charts", "state_control"],
        key="switch_page_target",
    )
    if enable_switch and st.button("Switch now", key="switch_page_now"):
        st.switch_page(target_slug)

# -------------------------------------------------------------------------
# st.divider()
# -------------------------------------------------------------------------
st.header("st.divider()", divider="blue")

st.code('st.divider()', language="python")

with st.container(border=True):
    st.write("Content above")
    st.divider()
    st.write("Content below")
