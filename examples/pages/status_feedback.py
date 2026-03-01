"""Status & Feedback page for the Fastlit demo."""

import time

import fastlit as st

PAGE_CONFIG = {
    "title": "Status & Feedback",
    "icon": "⚡",
    "order": 70,
}

st.title("⚡ Status & Feedback")
st.caption("Components for showing status and feedback")

# -------------------------------------------------------------------------
# Alert Messages
# -------------------------------------------------------------------------
st.header("Alert Messages", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Functions:**
    - `st.success(body, icon=None)` - Green success message
    - `st.info(body, icon=None)` - Blue info message
    - `st.warning(body, icon=None)` - Yellow warning message
    - `st.error(body, icon=None)` - Red error message
    
    **Parameters:**
    - `body` (str): Message text (supports Markdown)
    - `icon` (str | None): Custom emoji icon
    """)

st.code('''st.success("Operation completed successfully!")
st.info("Here's some helpful information.")
st.warning("Warning: This action cannot be undone.")
st.error("Error: Something went wrong.")

# With custom icons:
st.success("Saved!", icon="💾")
st.info("Tip: Use keyboard shortcuts", icon="💡")''', language="python")

with st.container(border=True):
    st.success("Operation completed successfully!")
    st.info("Here's some helpful information.")
    st.warning("Warning: This action cannot be undone.")
    st.error("Error: Something went wrong.")
    
    st.divider()
    st.caption("With custom icons:")
    st.success("Saved!", icon="💾")
    st.info("Tip: Use keyboard shortcuts", icon="💡")

# -------------------------------------------------------------------------
# st.exception()
# -------------------------------------------------------------------------
st.header("st.exception()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `exception` (BaseException | None): Exception to display, None for current exception
    
    Displays exception with full traceback.
    """)

st.code('''try:
result = 1 / 0
except Exception as e:
st.exception(e)''', language="python")

with st.container(border=True):
    try:
        result = 1 / 0
    except Exception as e:
        st.exception(e)

# -------------------------------------------------------------------------
# st.progress()
# -------------------------------------------------------------------------
st.header("st.progress()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `value` (float | int): Progress 0-100 or 0.0-1.0
    - `text` (str | None): Text above progress bar
    """)

st.code('''st.progress(25, text="25% - Getting started")
st.progress(50, text="50% - Halfway there!")
st.progress(75, text="75% - Almost done")
st.progress(100, text="100% - Complete!")''', language="python")

with st.container(border=True):
    st.progress(25, text="25% - Getting started")
    st.progress(50, text="50% - Halfway there!")
    st.progress(75, text="75% - Almost done")
    st.progress(100, text="100% - Complete!")

# -------------------------------------------------------------------------
# st.spinner()
# -------------------------------------------------------------------------
st.header("st.spinner()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Usage:** Context manager that shows a spinner while code executes.

    **New behavior (runtime):**
    - Spinner is shown immediately while the block is running.
    - Spinner is removed automatically when the block exits.
    - Works for full reruns and fragment reruns.
    
    ```python
    with st.spinner("Loading..."):
        time.sleep(2)
    ```
    """)

st.code('''if st.button("Start spinner demo"):
with st.spinner("Processing..."):
    time.sleep(1)
st.success("Done!")''', language="python")

with st.container(border=True):
    if st.button("Start spinner demo"):
        with st.spinner("Processing..."):
            time.sleep(1)
        st.success("Done!")
    st.caption("Spinner should be visible during execution.")

# -------------------------------------------------------------------------
# st.status()
# -------------------------------------------------------------------------
st.header("st.status()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Status label
    - `expanded` (bool): Initially expanded
    - `state` (str): "running", "complete", "error"
    
    **Methods:**
    - `.update(label=None, state=None, expanded=None)`: Update status
    """)

st.code('''if st.button("Run status demo"):
with st.status("Downloading data...", expanded=True) as status:
    st.write("Connecting to server...")
    time.sleep(0.5)
    st.write("Fetching data...")
    time.sleep(0.5)
    st.write("Processing...")
    time.sleep(0.5)
    status.update(label="Download complete!", state="complete")''', language="python")

with st.container(border=True):
    if st.button("Run status demo"):
        with st.status("Downloading data...", expanded=True) as status:
            st.write("Connecting to server...")
            time.sleep(0.5)
            st.write("Fetching data...")
            time.sleep(0.5)
            st.write("Processing...")
            time.sleep(0.5)
            status.update(label="Download complete!", state="complete")

# -------------------------------------------------------------------------
# st.toast()
# -------------------------------------------------------------------------
st.header("st.toast()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `body` (str): Toast message
    - `icon` (str | None): Icon emoji
    
    Shows a temporary notification in the corner.
    """)

st.code('''if st.button("Success toast"):
st.toast("Success!", icon="✅")

if st.button("Info toast"):
st.toast("Just so you know...", icon="ℹ️")

if st.button("Warning toast"):
st.toast("Watch out!", icon="⚠️")''', language="python")

with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Success toast"):
            st.toast("Success!", icon="✅")
    
    with col2:
        if st.button("Info toast"):
            st.toast("Just so you know...", icon="ℹ️")
    
    with col3:
        if st.button("Warning toast"):
            st.toast("Watch out!", icon="⚠️")

# -------------------------------------------------------------------------
# st.balloons() & st.snow()
# -------------------------------------------------------------------------
st.header("Celebrations", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Functions:**
    - `st.balloons()` - Show celebratory balloons
    - `st.snow()` - Show snowfall animation
    
    No parameters. Single-use animation.
    """)

st.code('''if st.button("🎈 Show Balloons"):
st.balloons()

if st.button("❄️ Show Snow"):
st.snow()''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎈 Show Balloons"):
            st.balloons()
    
    with col2:
        if st.button("❄️ Show Snow"):
            st.snow()
