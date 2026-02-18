"""
Fastlit Components Documentation Demo
=====================================
A comprehensive demo showcasing all available components.
Run with: fastlit run examples/all_components_docs.py --dev
"""

import fastlit as st
import datetime

# Page configuration
st.set_page_config(
    page_title="Fastlit Components Demo",
    page_icon="🚀",
    layout="wide",
)

# Sidebar navigation
st.sidebar.title("Components Demo")
st.sidebar.markdown("Navigate through all Fastlit components")

sections = [
    "🆕 Phase 5 Demo",
    "Text Elements",
    "Input Widgets",
    "Layout",
    "Data Display",
    "Charts",
    "Media",
    "Status Elements",
    "State & Control",
]

selected_section = st.sidebar.navigation(sections)

st.sidebar.divider()
st.sidebar.caption("Fastlit v0.1.0")
st.sidebar.link_button("View Documentation", "https://github.com/fastlit/fastlit")

# =============================================================================
# PHASE 5 DEMO — Test all Phase 5 modifications
# =============================================================================
if selected_section == "🆕 Phase 5 Demo":
    st.title("Phase 5 — New Features & Bug Fixes")
    st.markdown(
        "This section lets you test every change introduced in Phase 5. "
        "Open each sub-section to see the feature in action."
    )

    # ---- A1: layout wide ------------------------------------------------
    st.header("A1 — layout='wide' (was a no-op)", divider="blue")
    st.code("""st.set_page_config(layout="wide")   # now actually works""", language="python")
    with st.container(border=True):
        st.caption("The page is currently using `layout='wide'` — content fills the full viewport width. "
                   "Before the fix, `max-w-4xl` was always applied regardless of the layout setting.")
        col1, col2, col3, col4 = st.columns(4)
        for i, (col, label) in enumerate(zip([col1, col2, col3, col4],
                                              ["Column 1", "Column 2", "Column 3", "Column 4"])):
            with col:
                st.metric(label, i + 1)

    # ---- A2: hot reload -------------------------------------------------
    st.header("A2 — Hot reload (--dev)", divider="blue")
    st.code("""fastlit run examples/all_components_docs.py --dev
# Uvicorn now uses factory=True so reload actually works""", language="bash")
    with st.container(border=True):
        st.success("Fix: CLI now passes `factory=True` + module string to uvicorn. "
                   "Edit any .py file and the server reloads automatically.")

    # ---- A3: data_editor on_change --------------------------------------
    st.header("A3 — data_editor(on_change=...) callback", divider="blue")
    st.code("""def on_edit():
    st.toast("Data changed!")

df = st.data_editor(data, on_change=on_edit)""", language="python")

    if "edit_count" not in st.session_state:
        st.session_state.edit_count = 0

    def _on_edit():
        st.session_state.edit_count += 1
        st.toast(f"on_change called! ({st.session_state.edit_count} edits)")

    import datetime
    with st.container(border=True):
        st.caption("Edit a cell — the callback fires immediately after the change.")
        test_data = {
            "name": ["Alice", "Bob", "Charlie"],
            "score": [95, 87, 92],
            "active": [True, False, True],
            "joined": ["2024-01-15", "2024-03-22", "2023-11-08"],
        }
        edited = st.data_editor(test_data, on_change=_on_edit, key="phase5_editor")
        st.metric("Callbacks fired", st.session_state.edit_count)

    # ---- A4 + C2: initial_sidebar_state + set_sidebar_state ------------
    st.header("A4 + C2 — initial_sidebar_state & sidebar toggle", divider="blue")
    st.code("""# A4: set_page_config now applies initial sidebar state
st.set_page_config(initial_sidebar_state="collapsed")

# C2: toggle sidebar programmatically
st.set_sidebar_state("collapsed")
st.set_sidebar_state("expanded")""", language="python")
    with st.container(border=True):
        st.caption("The chevron button in the top-left corner toggles the sidebar. "
                   "You can also control it from Python:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Collapse sidebar", type="secondary"):
                st.set_sidebar_state("collapsed")
        with col2:
            if st.button("Expand sidebar", type="primary"):
                st.set_sidebar_state("expanded")

    # ---- B1: WS exponential backoff ------------------------------------
    st.header("B1 — WebSocket reconnect with exponential backoff", divider="blue")
    st.code("""# frontend/src/runtime/ws.ts
# reconnect delay: 2s → 4s → 8s → 16s → 30s (capped)
const delay = Math.min(BASE_DELAY * Math.pow(2, reconnectAttempts), MAX_DELAY);""", language="typescript")
    with st.container(border=True):
        st.info("Disconnect your network and reconnect — the UI will show 'Disconnected. Reconnecting...' "
                "with increasing delays between attempts (2s, 4s, 8s, 16s, 30s max).")

    # ---- B2: run_in_thread ---------------------------------------------
    st.header("B2 — Thread safety: st.run_in_thread()", divider="blue")
    st.code("""import threading

def background_task():
    # st.* calls work because the session context is copied
    st.session_state.result = expensive_computation()

t = st.run_in_thread(background_task)
t.start()
t.join()""", language="python")

    if "thread_result" not in st.session_state:
        st.session_state.thread_result = None

    def _thread_work():
        import time
        time.sleep(0.1)
        st.session_state.thread_result = "✅ Thread completed — st.session_state works from background thread!"

    with st.container(border=True):
        if st.button("Run background thread"):
            t = st.run_in_thread(_thread_work)
            t.start()
            t.join()
        if st.session_state.thread_result:
            st.success(st.session_state.thread_result)

    # ---- B3: lifecycle hooks -------------------------------------------
    st.header("B3 — ASGI lifecycle hooks", divider="blue")
    st.code("""@st.on_startup
def init_resources():
    st.session_state  # called once when the server starts
    print("Server started!")

@st.on_shutdown
async def cleanup():
    print("Server shutting down — closing connections...")""", language="python")
    with st.container(border=True):
        st.info("Lifecycle hooks are registered via `@st.on_startup` / `@st.on_shutdown` "
                "and called automatically by the Starlette ASGI lifespan manager.")

    # ---- C1: compact mode ---------------------------------------------
    st.header("C1 — Compact mode layout", divider="blue")
    st.code("""st.set_page_config(layout="compact")  # tighter padding""", language="python")
    with st.container(border=True):
        st.caption("Switch the layout in `set_page_config`. "
                   "Available modes: `'centered'` (default), `'wide'`, `'compact'`.")
        st.json({"centered": "max-w-4xl, padding 2rem", "wide": "no max-width", "compact": "padding 0.75rem"})

    # ---- D1 + D2: Plotly zoom preservation + cross-filtering ----------
    st.header("D1 — Plotly: zoom/pan preserved between reruns", divider="blue")
    st.header("D2 — Plotly: cross-filtering with on_select", divider="blue")

    try:
        import plotly.express as px
        import pandas as pd

        st.code("""# D1: zoom is preserved — rerun the app and zoom stays
selected = st.plotly_chart(fig, on_select=lambda pts: st.write(pts))""", language="python")

        df_scatter = pd.DataFrame({
            "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "y": [4, 7, 3, 9, 2, 8, 5, 6, 1, 10],
            "label": [f"Point {i}" for i in range(10)],
        })

        if "selected_points" not in st.session_state:
            st.session_state.selected_points = []

        def _on_select(indices):
            st.session_state.selected_points = indices

        fig = px.scatter(df_scatter, x="x", y="y", text="label",
                         title="Zoom/pan me (D1) — lasso/box select points (D2)")

        with st.container(border=True):
            col_chart, col_info = st.columns([3, 1])
            with col_chart:
                st.plotly_chart(fig, on_select=_on_select, key="phase5_plotly")
            with col_info:
                st.markdown("**Instructions**")
                st.markdown("- Zoom in → trigger a rerun via a widget below → zoom stays")
                st.markdown("- Use box/lasso select to pick points")
                if st.session_state.selected_points:
                    st.success(f"Selected indices:\n{st.session_state.selected_points}")
                else:
                    st.info("No points selected yet")
            # A widget to trigger rerun (to test zoom preservation)
            _ = st.slider("Trigger rerun (zoom should be preserved)", 0, 10, 5, key="zoom_test")

    except ImportError:
        st.warning("Install plotly (`pip install plotly pandas`) to see D1/D2 demos.")

    # ---- E1 + E2: DataEditor boolean + date --------------------------
    st.header("E1 — DataEditor: native checkbox for boolean columns", divider="blue")
    st.header("E2 — DataEditor: date picker for date/datetime columns", divider="blue")
    st.code("""# E1: boolean columns now show a native checkbox
# E2: date/datetime columns now show a native date picker
df = pd.DataFrame({"name": [...], "active": [True, False], "joined": ["2024-01-01", ...]})
st.data_editor(df)""", language="python")

    with st.container(border=True):
        rich_data = {
            "employee": ["Alice Martin", "Bob Dupont", "Charlie Lee", "Diana Chen"],
            "department": ["Engineering", "Marketing", "Design", "Engineering"],
            "active": [True, True, False, True],
            "start_date": ["2022-03-15", "2021-07-01", "2023-11-20", "2024-01-08"],
            "score": [92.5, 78.3, 85.0, 96.1],
        }
        st.data_editor(
            rich_data,
            key="phase5_rich_editor",
            num_rows="dynamic",
        )
        st.caption("✅ `active` column → checkbox | `start_date` column → date picker | `score` → number input")

# =============================================================================
# TEXT ELEMENTS
# =============================================================================
elif selected_section == "Text Elements":
    st.title("Text Elements", help="Components for displaying text content")

    # --- st.title ---
    st.header("st.title()", divider="blue")
    st.code('st.title("Main Title", anchor="custom-anchor", help="Tooltip text")', language="python")
    with st.container(border=True):
        st.title("Main Title")

    # --- st.header ---
    st.header("st.header()", divider="blue")
    st.code('st.header("Section Header", divider=True, help="Help text") \n' \
    'st.header("Colored Divider", divider="rainbow")', language="python")
    with st.container(border=True):
        st.header("Section Header", divider=True)
        st.header("Colored Divider", divider="rainbow")

    # --- st.subheader ---
    st.header("st.subheader()", divider="blue")
    st.code('st.subheader("Subsection", divider="green")', language="python")
    with st.container(border=True):
        st.subheader("Subsection Title", divider="green")

    # --- st.text ---
    st.header("st.text()", divider="blue")
    st.code('st.text("Fixed-width monospace text")', language="python")
    with st.container(border=True):
        st.text("This is fixed-width monospace text.")

    # --- st.markdown ---
    st.header("st.markdown()", divider="blue")
    st.code('''st.markdown("""
**Bold**, *italic*, `code`, and [links](https://example.com)
- List item 1
- List item 2
""")''', language="python")
    with st.container(border=True):
        st.markdown("""
**Bold**, *italic*, `code`, and [links](https://example.com)
- List item 1
- List item 2
""")

    # --- st.write ---
    st.header("st.write()", divider="blue")
    st.caption("Smart content renderer - automatically detects type")
    st.code('st.write("String", {"key": "value"}, [1, 2, 3])', language="python")
    with st.container(border=True):
        st.write("This is a string")
        st.write({"name": "Fastlit", "version": "0.1.0"})

    # --- st.code ---
    st.header("st.code()", divider="blue")
    st.code('''st.code("""
def hello():
    return "Hello, World!"
""", language="python", line_numbers=True)''', language="python")
    with st.container(border=True):
        st.code("""
def hello():
    return "Hello, World!"
""", language="python", line_numbers=True)

    # --- st.caption ---
    st.header("st.caption()", divider="blue")
    st.code('st.caption("Small text for captions and footnotes")', language="python")
    with st.container(border=True):
        st.caption("Small text for captions and footnotes")

    # --- st.latex ---
    st.header("st.latex()", divider="blue")
    st.code('st.latex(r"E = mc^2")', language="python")
    with st.container(border=True):
        st.latex(r"E = mc^2")
        st.latex(r"\sum_{i=1}^{n} x_i = x_1 + x_2 + ... + x_n")

    # --- st.divider ---
    st.header("st.divider()", divider="blue")
    st.code('st.divider()', language="python")
    with st.container(border=True):
        st.write("Content above")
        st.divider()
        st.write("Content below")

# =============================================================================
# INPUT WIDGETS
# =============================================================================
elif selected_section == "Input Widgets":
    st.title("Input Widgets", help="Interactive input components")

    # --- st.button ---
    st.header("st.button()", divider="blue")
    st.code('clicked = st.button("Click me", type="primary")', language="python")
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            btn_primary = st.button("Primary", type="primary")
        with col2:
            btn_secondary = st.button("Secondary")
        with col3:
            btn_disabled = st.button("Disabled", disabled=True)
        st.write(f"Primary: `{btn_primary}` | Secondary: `{btn_secondary}` | Disabled: `{btn_disabled}`")

    # --- st.link_button ---
    st.header("st.link_button()", divider="blue")
    st.code('st.link_button("Open Google", "https://google.com")', language="python")
    with st.container(border=True):
        st.link_button("Open Google", "https://google.com")
        st.link_button("Primary Style", "https://github.com", type="primary")

    # --- st.download_button ---
    st.header("st.download_button()", divider="blue")
    st.code('st.download_button("Download CSV", data, "file.csv", mime="text/csv")', language="python")
    with st.container(border=True):
        csv_data = "name,age\nAlice,30\nBob,25"
        st.download_button(
            "Download Sample CSV",
            data=csv_data,
            file_name="sample.csv",
            mime="text/csv",
        )

    # --- st.checkbox ---
    st.header("st.checkbox()", divider="blue")
    st.code('checked = st.checkbox("I agree to the terms")', language="python")
    with st.container(border=True):
        agree = st.checkbox("I agree to the terms", value=True)
        st.write(f"Value: `{agree}`")

    # --- st.toggle ---
    st.header("st.toggle()", divider="blue")
    st.code('enabled = st.toggle("Enable feature")', language="python")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            dark_mode = st.toggle("Dark mode", value=False)
        with col2:
            notifications = st.toggle("Notifications", value=True)
        st.write(f"Dark mode: `{dark_mode}` | Notifications: `{notifications}`")

    # --- st.radio ---
    st.header("st.radio()", divider="blue")
    st.code('choice = st.radio("Pick one", ["A", "B", "C"], horizontal=True)', language="python")
    with st.container(border=True):
        choice = st.radio(
            "Select your favorite",
            ["Python", "JavaScript", "Rust", "Go"],
            horizontal=True,
            captions=["Dynamic", "Web", "Fast", "Simple"],
        )
        st.write(f"Selected: `{choice}`")

    # --- st.selectbox ---
    st.header("st.selectbox()", divider="blue")
    st.code('option = st.selectbox("Choose", ["A", "B", "C"])', language="python")
    with st.container(border=True):
        option = st.selectbox(
            "Select a country",
            ["France", "Germany", "Italy", "Spain", "UK"],
            placeholder="Choose a country...",
        )
        st.write(f"Selected: `{option}`")

    # --- st.multiselect ---
    st.header("st.multiselect()", divider="blue")
    st.code('items = st.multiselect("Select multiple", ["A", "B", "C"])', language="python")
    with st.container(border=True):
        selected = st.multiselect(
            "Select your skills",
            ["Python", "JavaScript", "SQL", "Docker", "Kubernetes", "AWS"],
            default=["Python"],
            max_selections=4,
        )
        st.write(f"Selected: `{selected}`")

    # --- st.slider ---
    st.header("st.slider()", divider="blue")
    st.code('value = st.slider("Select a value", 0, 100, 50)', language="python")
    with st.container(border=True):
        value = st.slider("Volume", 0, 100, 50)
        float_val = st.slider("Temperature", 0.0, 100.0, 37.5, step=0.5)
        st.write(f"Volume: `{value}` | Temperature: `{float_val}`")

    # --- st.select_slider ---
    st.header("st.select_slider()", divider="blue")
    st.code('size = st.select_slider("Size", ["S", "M", "L", "XL"])', language="python")
    with st.container(border=True):
        size = st.select_slider(
            "Select size",
            options=["XS", "S", "M", "L", "XL", "XXL"],
            value="M",
        )
        st.write(f"Size: `{size}`")

    # --- st.number_input ---
    st.header("st.number_input()", divider="blue")
    st.code('num = st.number_input("Enter a number", min_value=0, max_value=100)', language="python")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            integer = st.number_input("Quantity", min_value=0, max_value=100, value=1)
        with col2:
            decimal = st.number_input("Price", min_value=0.0, value=9.99, step=0.01)
        st.write(f"Quantity: `{integer}` | Price: `{decimal}`")

    # --- st.text_input ---
    st.header("st.text_input()", divider="blue")
    st.code('name = st.text_input("Your name", placeholder="Enter name...")', language="python")
    with st.container(border=True):
        name = st.text_input("Your name", placeholder="Enter your name...")
        password = st.text_input("Password", type="password")
        st.caption("*Character count updates live in React (no rerun needed)*")

    # --- st.text_area ---
    st.header("st.text_area()", divider="blue")
    st.code('bio = st.text_area("Bio", height=150)', language="python")
    with st.container(border=True):
        bio = st.text_area(
            "Tell us about yourself",
            placeholder="Write a short bio...",
            height=100,
        )
        st.caption("*Character count updates live in React (no rerun needed)*")

    # --- st.date_input ---
    st.header("st.date_input()", divider="blue")
    st.code('date = st.date_input("Pick a date")', language="python")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            single_date = st.date_input("Select a date", value=datetime.date.today())
        with col2:
            date_range = st.date_input(
                "Select date range",
                value=(datetime.date.today(), datetime.date.today() + datetime.timedelta(days=7)),
            )
        st.write(f"Single: `{single_date}` | Range: `{date_range}`")

    # --- st.time_input ---
    st.header("st.time_input()", divider="blue")
    st.code('time = st.time_input("Pick a time")', language="python")
    with st.container(border=True):
        alarm = st.time_input("Set alarm", value=datetime.time(8, 0))
        st.write(f"Alarm: `{alarm}`")

    # --- st.color_picker ---
    st.header("st.color_picker()", divider="blue")
    st.code('color = st.color_picker("Pick a color", "#00FF00")', language="python")
    with st.container(border=True):
        color = st.color_picker("Choose theme color", "#3B82F6")
        st.write(f"Color: `{color}`")

    # --- st.file_uploader ---
    st.header("st.file_uploader()", divider="blue")
    st.code('file = st.file_uploader("Upload a file", type=["csv", "txt"])', language="python")
    with st.container(border=True):
        uploaded = st.file_uploader(
            "Upload files",
            type=["csv", "txt", "json"],
            accept_multiple_files=True,
        )
        if uploaded:
            for f in uploaded:
                st.write(f"Uploaded: {f.name} ({f.size} bytes)")

# =============================================================================
# LAYOUT
# =============================================================================
elif selected_section == "Layout":
    st.title("Layout Components", help="Components for organizing content")

    # --- st.columns ---
    st.header("st.columns()", divider="blue")
    st.code('col1, col2, col3 = st.columns(3)', language="python")
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("Column 1")
        with col2:
            st.success("Column 2")
        with col3:
            st.warning("Column 3")

        st.caption("Columns with custom widths:")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.info("Wide column (2)")
        with c2:
            st.success("Narrow (1)")

    # --- st.tabs ---
    st.header("st.tabs()", divider="blue")
    st.code('tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])', language="python")
    with st.container(border=True):
        tab1, tab2, tab3 = st.tabs(["Overview", "Data", "Settings"])
        with tab1:
            st.write("This is the overview tab")
        with tab2:
            st.write("This is the data tab")
        with tab3:
            st.write("This is the settings tab")

    # --- st.expander ---
    st.header("st.expander()", divider="blue")
    st.code('with st.expander("Click to expand"):\n    st.write("Hidden content")', language="python")
    with st.container(border=True):
        with st.expander("Click to see more details", expanded=False):
            st.write("This content is hidden by default.")
            st.code("print('Hello from expander!')", language="python")

        with st.expander("Already expanded", expanded=True):
            st.write("This expander starts open.")

    # --- st.container ---
    st.header("st.container()", divider="blue")
    st.code('with st.container(border=True):\n    st.write("Bordered content")', language="python")
    with st.container(border=True):
        with st.container(border=True):
            st.write("Content inside a bordered container")
            st.button("Button inside container")

    # --- st.empty ---
    st.header("st.empty()", divider="blue")
    st.code('placeholder = st.empty()\nplaceholder.write("Updated content")', language="python")
    with st.container(border=True):
        placeholder = st.empty()
        placeholder.info("This is a placeholder that can be updated")

    # --- st.form ---
    st.header("st.form()", divider="blue")
    st.code('''with st.form("my_form"):
    name = st.text_input("Name")
    submitted = st.form_submit_button("Submit")''', language="python")
    with st.container(border=True):
        with st.form("demo_form"):
            form_name = st.text_input("Enter your name")
            form_email = st.text_input("Enter your email")
            form_age = st.slider("Your age", 18, 100, 25)
            submitted = st.form_submit_button("Submit Form")
        st.write(f"Submitted: `{submitted}` | Name: `{form_name}` | Email: `{form_email}` | Age: `{form_age}`")

    # --- st.popover ---
    st.header("st.popover()", divider="blue")
    st.code('with st.popover("Open popover"):\n    st.write("Popover content")', language="python")
    with st.container(border=True):
        with st.popover("Click for options"):
            st.write("Choose an action:")
            if st.button("Option A"):
                st.toast("Option A selected!")
            if st.button("Option B"):
                st.toast("Option B selected!")

    # --- st.divider ---
    st.header("st.divider()", divider="blue")
    st.code('st.divider()', language="python")
    with st.container(border=True):
        st.write("Section 1")
        st.divider()
        st.write("Section 2")

# =============================================================================
# DATA DISPLAY
# =============================================================================
elif selected_section == "Data Display":
    st.title("Data Display", help="Components for displaying data")

    # Sample data
    sample_data = {
        "Name": ["Alice", "Bob", "Charlie", "Diana"],
        "Age": [25, 30, 35, 28],
        "City": ["Paris", "London", "Berlin", "Madrid"],
        "Score": [85.5, 92.0, 78.5, 95.0],
    }

    # --- st.dataframe ---
    st.header("st.dataframe()", divider="blue")
    st.code('st.dataframe(df, height=300)', language="python")
    with st.container(border=True):
        st.dataframe(sample_data, height=200)

    # --- st.data_editor ---
    st.header("st.data_editor()", divider="blue")
    st.code('edited = st.data_editor(df)', language="python")
    with st.container(border=True):
        edited = st.data_editor(sample_data, height=200)
        st.write(f"Edited data type: `{type(edited).__name__}` | Rows: `{len(edited.get('Name', []))}`")

    # --- st.table ---
    st.header("st.table()", divider="blue")
    st.code('st.table(df)  # Static table', language="python")
    with st.container(border=True):
        st.table(sample_data)

    # --- st.metric ---
    st.header("st.metric()", divider="blue")
    st.code('st.metric("Revenue", "$1,234", delta="+12%")', language="python")
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Revenue", "$1,234", delta="+12%")
        with col2:
            st.metric("Users", "1,234", delta="+5%")
        with col3:
            st.metric("Errors", "23", delta="-8%", delta_color="inverse")
        with col4:
            st.metric("Uptime", "99.9%", delta="0%", delta_color="off")

    # --- st.json ---
    st.header("st.json()", divider="blue")
    st.code('st.json({"key": "value", "nested": {"a": 1}})', language="python")
    with st.container(border=True):
        st.json({
            "name": "Fastlit",
            "version": "0.1.0",
            "features": ["fast", "reactive", "streamlit-compatible"],
            "config": {
                "debug": True,
                "port": 8501,
            },
        })

# =============================================================================
# CHARTS
# =============================================================================
elif selected_section == "Charts":
    st.title("Charts", help="Data visualization components")

    # Sample chart data
    chart_data = {
        "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "sales": [100, 120, 140, 160, 180, 200],
        "profit": [20, 25, 30, 35, 40, 45],
        "costs": [80, 95, 110, 125, 140, 155],
    }

    # --- st.line_chart ---
    st.header("st.line_chart()", divider="blue")
    st.code('st.line_chart(df, x="month", y=["sales", "profit"])', language="python")
    with st.container(border=True):
        st.line_chart(chart_data, x="month", y=["sales", "profit"])

    # --- st.bar_chart ---
    st.header("st.bar_chart()", divider="blue")
    st.code('st.bar_chart(df, x="month", y="sales")', language="python")
    with st.container(border=True):
        st.bar_chart(chart_data, x="month", y="sales")

    # --- st.area_chart ---
    st.header("st.area_chart()", divider="blue")
    st.code('st.area_chart(df, x="month", y=["sales", "costs"])', language="python")
    with st.container(border=True):
        st.area_chart(chart_data, x="month", y=["sales", "costs"])

    # --- st.scatter_chart ---
    st.header("st.scatter_chart()", divider="blue")
    st.code('st.scatter_chart(df, x="sales", y="profit")', language="python")
    with st.container(border=True):
        scatter_data = {
            "x": [10, 20, 30, 40, 50, 60, 70, 80],
            "y": [15, 25, 20, 45, 35, 55, 50, 70],
        }
        st.scatter_chart(scatter_data, x="x", y="y")

    # --- st.map ---
    st.header("st.map()", divider="blue")
    st.code('st.map(df)  # with lat/lon columns', language="python")
    with st.container(border=True):
        map_data = [
            {"lat": 48.8566, "lon": 2.3522},  # Paris
            {"lat": 51.5074, "lon": -0.1278},  # London
            {"lat": 52.5200, "lon": 13.4050},  # Berlin
            {"lat": 40.4168, "lon": -3.7038},  # Madrid
        ]
        st.map(map_data, zoom=4)

# =============================================================================
# MEDIA
# =============================================================================
elif selected_section == "Media":
    st.title("Media Components", help="Components for displaying media")

    # --- st.image ---
    st.header("st.image()", divider="blue")
    st.code('st.image("https://example.com/image.png", caption="Image")', language="python")
    with st.container(border=True):
        st.image(
            "https://via.placeholder.com/400x200/3B82F6/FFFFFF?text=Fastlit+Demo",
            caption="Sample image with caption",
            width=400,
        )

    # --- st.audio ---
    st.header("st.audio()", divider="blue")
    st.code('st.audio("audio.mp3")', language="python")
    with st.container(border=True):
        st.caption("Audio player (provide an audio file URL)")
        st.info("Use st.audio() with a valid audio file path or URL")

    # --- st.video ---
    st.header("st.video()", divider="blue")
    st.code('st.video("video.mp4")', language="python")
    with st.container(border=True):
        st.caption("Video player (provide a video file URL)")
        st.info("Use st.video() with a valid video file path or URL")

# =============================================================================
# STATUS ELEMENTS
# =============================================================================
elif selected_section == "Status Elements":
    st.title("Status Elements", help="Components for showing status and feedback")

    # --- Alert messages ---
    st.header("Alert Messages", divider="blue")
    st.code('''st.success("Operation successful!")
st.info("Here's some information.")
st.warning("Be careful!")
st.error("Something went wrong.")''', language="python")
    with st.container(border=True):
        st.success("Operation completed successfully!")
        st.info("Here's some helpful information.")
        st.warning("Warning: This action cannot be undone.")
        st.error("Error: Something went wrong.")

    # --- st.progress ---
    st.header("st.progress()", divider="blue")
    st.code('st.progress(75, text="Loading...")', language="python")
    with st.container(border=True):
        st.progress(25, text="25% complete")
        st.progress(50, text="50% complete")
        st.progress(75, text="75% complete")
        st.progress(100, text="Complete!")

    # --- st.spinner ---
    st.header("st.spinner()", divider="blue")
    st.code('with st.spinner("Loading..."):\n    # do work', language="python")
    with st.container(border=True):
        with st.spinner("Processing..."):
            st.write("Content is loading...")

    # --- st.status ---
    st.header("st.status()", divider="blue")
    st.code('with st.status("Running task...") as status:\n    status.update(state="complete")', language="python")
    with st.container(border=True):
        with st.status("Downloading data...", expanded=True) as status:
            st.write("Fetching resources...")
            status.update(label="Download complete!", state="complete")

    # --- st.toast ---
    st.header("st.toast()", divider="blue")
    st.code('st.toast("Message sent!")', language="python")
    with st.container(border=True):
        if st.button("Show Toast Notification"):
            st.toast("This is a toast notification!")

    # --- st.balloons & st.snow ---
    st.header("Celebrations", divider="blue")
    st.code('st.balloons()  # or st.snow()', language="python")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Show Balloons"):
                st.balloons()
        with col2:
            if st.button("Show Snow"):
                st.snow()

# =============================================================================
# STATE & CONTROL
# =============================================================================
elif selected_section == "State & Control":
    st.title("State & Control", help="State management and control flow")

    # --- st.session_state ---
    st.header("st.session_state", divider="blue")
    st.code('''if "counter" not in st.session_state:
    st.session_state.counter = 0
st.session_state.counter += 1''', language="python")
    with st.container(border=True):
        if "demo_counter" not in st.session_state:
            st.session_state.demo_counter = 0

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Increment"):
                st.session_state.demo_counter += 1
        with col2:
            if st.button("Decrement"):
                st.session_state.demo_counter -= 1
        with col3:
            if st.button("Reset"):
                st.session_state.demo_counter = 0

        st.metric("Counter", st.session_state.demo_counter)

    # --- st.rerun ---
    st.header("st.rerun()", divider="blue")
    st.code('st.rerun()  # Triggers a script rerun', language="python")
    with st.container(border=True):
        st.caption("st.rerun() immediately stops execution and reruns the script")
        if st.button("Rerun App"):
            st.rerun()

    # --- st.stop ---
    st.header("st.stop()", divider="blue")
    st.code('st.stop()  # Stops script execution', language="python")
    with st.container(border=True):
        st.caption("st.stop() halts script execution - nothing below it will render")
        show_stop = st.checkbox("Enable st.stop() demo")
        st.write(f"Checkbox: `{show_stop}`")
        if show_stop:
            st.warning("Script will stop here!")
            st.stop()
            st.error("This will never be shown")

    # --- st.set_page_config ---
    st.header("st.set_page_config()", divider="blue")
    st.code('''st.set_page_config(
    page_title="My App",
    page_icon="🚀",
    layout="wide",
)''', language="python")
    with st.container(border=True):
        st.caption("Must be called at the very beginning of the script")
        st.json({
            "page_title": "Fastlit Components Demo",
            "page_icon": "rocket",
            "layout": "wide",
        })

# Footer
st.divider()
st.caption("Built with Fastlit - A Streamlit-compatible, blazing fast Python UI framework")
