"""Advanced Features page for the Fastlit demo."""

import time

import fastlit as st

PAGE_CONFIG = {
    "title": "Advanced Features",
    "icon": "🎨",
    "order": 110,
}

st.title("🎨 Advanced Features")
st.caption("Advanced functionality and patterns")

# -------------------------------------------------------------------------
# Page Configuration
# -------------------------------------------------------------------------
st.header("Page Configuration", divider="blue")
st.caption("Test all `st.set_page_config()` options live — changes apply instantly!")

with st.expander("📖 API Reference", expanded=False):
    st.markdown("""
    **Must be the first Streamlit command in your script.**""")
    st.markdown("""
    | Layout | Description |
    |--------|-------------|
    | `"centered"` | Max-width 896px, centered — good for text-heavy apps |
    | `"wide"` | Full viewport width — good for dashboards |
    | `"compact"` | Full width + minimal padding — maximum data density |
    """)
st.code('''st.set_page_config(
        page_title="My App",             # Browser tab title
        page_icon="🚀",                  # Favicon: emoji or URL
        layout="centered",               # "centered" | "wide" | "compact"
        initial_sidebar_state="auto",    # "auto" | "expanded" | "collapsed"
        menu_items={...},                # Custom menu items (optional)
    )
    ''', language="python")

# -------------------------------------------------------------------------
# Threading Support
# -------------------------------------------------------------------------
st.header("Threading Support", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Run functions in background threads with session context.
    """)

    st.code('''def background_work():
    # st.* calls work here
    result = expensive_computation()
    st.session_state.result = result
    
    # Create thread with session context
    t = st.run_in_thread(background_work)
    t.start()
    t.join()
    
    # Or run directly
    st.run_with_session_context(some_function, arg1, arg2)
    ''', language="python")
    

with st.container(border=True):
    if "thread_result" not in st.session_state:
        st.session_state.thread_result = None
    
    def _background_work():
        time.sleep(0.2)
        st.session_state.thread_result = "✅ Thread completed!"
    
    if st.button("Run background thread"):
        t = st.run_in_thread(_background_work)
        t.start()
        t.join()
    
    if st.session_state.thread_result:
        st.success(st.session_state.thread_result)

# -------------------------------------------------------------------------
# st.on_startup() / st.on_shutdown()
# -------------------------------------------------------------------------
st.header("st.on_startup() / st.on_shutdown()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Register lifecycle hooks on ASGI server startup/shutdown.

    **Best practice:**
    - Declare hooks at module import time (top-level app code).
    - Keep startup/shutdown handlers idempotent and fast.
    """)

st.code('''@st.on_startup
def init_resources():
print("Server startup hook")

@st.on_shutdown
def close_resources():
print("Server shutdown hook")''', language="python")

with st.container(border=True):
    st.info(
        "Lifecycle hooks are intentionally shown as code-only in this demo. "
        "Declare them in your app module to run at server start/stop."
    )

# -------------------------------------------------------------------------
# Sidebar Control
# -------------------------------------------------------------------------
st.header("Programmatic Sidebar Control", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Control sidebar state programmatically.
    
    ```python
    st.set_sidebar_state("collapsed")
    st.set_sidebar_state("expanded")
    ```
    """)

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Collapse sidebar"):
            st.set_sidebar_state("collapsed")
    with col2:
        if st.button("Expand sidebar"):
            st.set_sidebar_state("expanded")

# -------------------------------------------------------------------------
# Scalability & Observability
# -------------------------------------------------------------------------
st.header("Scalability & Observability", divider="blue")

with st.container(border=True):
    st.markdown("""
    This project now includes runtime guardrails and observability endpoints.

    **Production command**
    ```bash
    fastlit run examples/all_components_demo.py --host 0.0.0.0 --port 8501 --workers 4 --limit-concurrency 200 --backlog 2048 --max-sessions 300 --max-concurrent-runs 8 --run-timeout-seconds 45
    ```

    **Metrics endpoint**
    - `GET /_fastlit/metrics`
    - Includes sessions, run latency stats (avg/p50/p95/p99), payload stats, dropped events.

    **DataFrame server paging**
    - Large dataframes use windowed fetch via `/_fastlit/dataframe/{source_id}`.

    **Useful env vars**
    - `FASTLIT_WS_EVENT_QUEUE_SIZE`
    - `FASTLIT_WS_COALESCE_WINDOW_MS`
    - `FASTLIT_MAX_SESSION_STATE_BYTES`
    - `FASTLIT_MAX_WIDGET_STORE_BYTES`
    - `FASTLIT_MAX_UPLOAD_MB`
    """)
