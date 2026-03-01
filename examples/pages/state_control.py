"""State & Control page for the Fastlit demo."""

import fastlit as st

PAGE_CONFIG = {
    "title": "State & Control",
    "icon": "🔧",
    "order": 100,
}

st.title("🔧 State & Control")
st.caption("State management and control flow")

# -------------------------------------------------------------------------
# st.session_state
# -------------------------------------------------------------------------
st.header("st.session_state", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Session-scoped state dictionary with attribute access.
    
    **Usage:**
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
    """)

with st.container(border=True):
    if "demo_counter" not in st.session_state:
        st.session_state.demo_counter = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➖ Decrement"):
            st.session_state.demo_counter -= 1
    
    with col2:
        if st.button("➕ Increment"):
            st.session_state.demo_counter += 1
    
    with col3:
        if st.button("🔄 Reset"):
            st.session_state.demo_counter = 0
    
    with col4:
        st.metric("Counter", st.session_state.demo_counter)
    
    st.caption("Session state persists across reruns but not page refreshes.")

# -------------------------------------------------------------------------
# st.query_params
# -------------------------------------------------------------------------
st.header("st.query_params", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Access URL query parameters.
    
    **Usage:**
    ```python
    # Read
    page = st.query_params.get("page", "index")
    page = st.query_params["page"]
    
    # Write
    st.query_params["page"] = "settings"
    
    # All values for a key
    tags = st.query_params.get_all("tag")
    
    # Convert to dict
    params = st.query_params.to_dict()
    
    # Clear
    st.query_params.clear()
    ```
    """)


st.code('''# Read
page = st.query_params.get("page", "index")
page = st.query_params["page"]

# Write
st.query_params["page"] = "settings"

# All values for a key
tags = st.query_params.get_all("tag")

# Convert to dict
params = st.query_params.to_dict()

# Clear
st.query_params.clear()''', language="python")

with st.container(border=True):
    st.write("Current query params:")
    st.json(st.query_params.to_dict())
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Set ?demo=true"):
            st.query_params["demo"] = "true"
            st.rerun()
    with col2:
        if st.button("Clear params"):
            st.query_params.clear()
            st.rerun()

# -------------------------------------------------------------------------
# st.secrets
# -------------------------------------------------------------------------
st.header("st.secrets", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Access secrets from `secrets.toml` or `.streamlit/secrets.toml`.

    **New behavior:**
    - Secrets cache is reloaded automatically when the secrets file changes.
    - You can still use both dict and attribute access styles.
    
    **File format:**
    ```toml
    [database]
    host = "localhost"
    password = "secret123"
    
    [api]
    key = "sk-..."
    ```
    
    **Usage:**
    ```python
    host = st.secrets["database"]["host"]
    host = st.secrets.database.host
    ```
    """)


st.code('''# secrets.toml
[database]
host = "localhost"
password = "secret123"

[api]
key = "sk-..."

# app.py
host = st.secrets["database"]["host"]
host = st.secrets.database.host''', language="python")

with st.container(border=True):
    st.info("Create a `secrets.toml` file to use `st.secrets`")

# -------------------------------------------------------------------------
# st.context
# -------------------------------------------------------------------------
st.header("st.context", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Access request context information.
    
    **Properties:**
    - `st.context.headers` - dict: HTTP headers
    - `st.context.cookies` - dict: Cookies
    - `st.context.ip_address` - str: Client IP
    - `st.context.locale` - str: Locale from Accept-Language
    - `st.context.timezone` - str: Timezone hint
    """)

with st.container(border=True):
    st.write("Request context:")
    st.json({
        "headers": dict(st.context.headers),
        "cookies": dict(st.context.cookies),
    })

# -------------------------------------------------------------------------
# st.user / st.require_login() / st.logout()
# -------------------------------------------------------------------------
st.header("st.user / st.require_login() / st.logout()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Authentication helpers and current user proxy.

    **APIs:**
    - `st.user`: claims proxy (`is_logged_in`, `name`, `email`, custom claims)
    - `st.require_login()`: redirect to login when not authenticated
    - `st.logout()`: clear auth session and redirect to logout route
    """)

st.code('''# Protect a page
st.require_login()
st.write("Hello", st.user.name, st.user.email)

if st.button("Sign out"):
st.logout()''', language="python")

with st.container(border=True):
    st.write(f"Authenticated: `{st.user.is_logged_in}`")
    st.json(
        {
            "name": st.user.name,
            "email": st.user.email,
            "sub": st.user.sub,
        },
        expanded=True,
    )
    if st.user.is_logged_in:
        if st.button("Logout now", key="auth_logout_now"):
            st.logout()
    else:
        st.info(
            "No authenticated user in this session. Configure [auth] in secrets.toml "
            "to enable login."
        )

# -------------------------------------------------------------------------
# st.connection() / st.connections
# -------------------------------------------------------------------------
st.header("st.connection() / st.connections", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Reusable backend connections with optional TTL-based recreation.

    **APIs:**
    - `st.connection(name, type=..., ttl=..., **kwargs)`
    - `st.connections`: module with built-ins (e.g., `BaseConnection`, `SQLConnection`)
    """)

st.code('''conn = st.connection(
"demo_db",
type="sql",
url="sqlite:///demo.db",
ttl=60,
)
df = conn.query("SELECT 1 AS ok", ttl=0)
st.dataframe(df)''', language="python")

with st.container(border=True):
    visible_symbols = [n for n in dir(st.connections) if not n.startswith("_")]
    st.write("`st.connections` public symbols:", visible_symbols)

    if st.button("Run SQL smoke query", key="connection_sql_smoke"):
        try:
            conn = st.connection(
                "demo_sqlite_conn",
                type="sql",
                url="sqlite:///fastlit_demo.db",
                ttl=30,
            )
            df = conn.query("SELECT 1 AS ok", ttl=0)
            st.dataframe(df, height=120)
            st.success("Connection demo OK.")
        except Exception as exc:
            st.warning(f"Connection demo unavailable in this environment: {exc}")

# -------------------------------------------------------------------------
# st.rerun()
# -------------------------------------------------------------------------
st.header("st.rerun()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Stop execution and immediately rerun the script.
    
    **Usage:**
    ```python
    st.rerun()  # Raises RerunException
    st.rerun(scope="fragment")  # Inside @st.fragment only
    ```
    
    Useful for refreshing the UI after state changes.
    """)

with st.container(border=True):
    st.caption("Click to rerun the app:")
    st.caption("`scope=\"fragment\"` is supported inside `@st.fragment`.")
    if st.button("🔄 Rerun App"):
        st.rerun()

st.code('''if st.button("Rerun full app"):
st.rerun()

@st.fragment
def _fragment_rerun_demo():
if "fragment_scope_count" not in st.session_state:
    st.session_state.fragment_scope_count = 0

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    if st.button("+1", key="frag_scope_inc", use_container_width=True):
        st.session_state.fragment_scope_count += 1
with col2:
    if st.button("Reset fragment", key="frag_scope_reset", use_container_width=True):
        st.session_state.fragment_scope_count = 0
        st.rerun(scope="fragment")
with col3:
    st.metric("Fragment count", st.session_state.fragment_scope_count)

_fragment_rerun_demo()''', language="python")

with st.container(border=True):
    if st.button("Rerun full app"):
        st.rerun()

    @st.fragment
    def _fragment_rerun_demo():
        if "fragment_scope_count" not in st.session_state:
            st.session_state.fragment_scope_count = 0

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("+1", key="frag_scope_inc", use_container_width=True):
                st.session_state.fragment_scope_count += 1
        with col2:
            if st.button("Reset fragment", key="frag_scope_reset", use_container_width=True):
                st.session_state.fragment_scope_count = 0
                st.rerun(scope="fragment")
        with col3:
            st.metric("Fragment count", st.session_state.fragment_scope_count)

    _fragment_rerun_demo()

# -------------------------------------------------------------------------
# st.stop()
# -------------------------------------------------------------------------
st.header("st.stop()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    Stop script execution. Elements below won't render.
    
    **Usage:**
    ```python
    if not authenticated:
        st.error("Please login")
        st.stop()
    
    # This won't run if not authenticated
    st.write("Secret content")
    ```
    """)


st.code('''if not authenticated:
st.error("Please login")
st.stop()

# This runs only when authenticated
st.write("Secret content")''', language="python")

with st.container(border=True):
    show_stop = st.checkbox("Enable st.stop() demo")
    
    if show_stop:
        st.warning("Script will stop here!")
        st.stop()
        st.error("This will never be shown")
    else:
        st.success("Content continues because stop is disabled")


# -------------------------------------------------------------------------
# Caching
# -------------------------------------------------------------------------
st.header("Caching", divider="blue")

with st.expander("📖 @st.cache_data", expanded=True):
    st.markdown("""
    Cache function results with automatic invalidation.
    
    ```python
    @st.cache_data(ttl=300, max_entries=1000, copy=False)
    def load_data(path: str) -> pd.DataFrame:
        return pd.read_csv(path)
    ```
    
    **Parameters:**
    - `ttl` (int | None): Time-to-live in seconds
    - `max_entries` (int): Maximum cache entries (LRU)
    - `copy` (bool): Return deepcopy by default. Use `copy=False` for immutable results.
    
    **Clear cache:**
    ```python
    load_data.clear()           # Clear this function's cache
    st.cache_data.clear()       # Clear all cache_data caches
    ```
    """)

with st.expander("📖 @st.cache_resource", expanded=True):
    st.markdown("""
    Cache resources (DB connections, ML models) — singleton, no copy.
    
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
    """)

with st.expander("📖 New cache guarantees", expanded=False):
    st.markdown("""
    **Recent updates:**
    - `my_cached_fn.clear()` now clears only that function's entries.
    - `@st.cache_resource` initialization is thread-safe per cache key.

    ```python
    @st.cache_data
    def users():
        ...

    @st.cache_data
    def products():
        ...

    users.clear()  # does not clear products cache
    ```
    """)

with st.container(border=True):
    @st.cache_data(ttl=60)
    def expensive_computation(n):
        import time
        time.sleep(0.1)  # Simulate work
        return sum(range(n))

    @st.cache_data(ttl=60, copy=False)
    def immutable_cached_tuple(n):
        # Safe with copy=False because tuple values are immutable.
        return tuple(range(min(n, 10)))
    
    n = st.slider("Compute sum(0..n)", 1000, 100000, 10000)
    result = expensive_computation(n)
    st.write(f"Result: `{result:,}`")
    st.caption(f"Immutable cache sample (copy=False): {immutable_cached_tuple(8)}")
    st.caption("First call is slow, subsequent calls are instant (cached)!")
