"""Home page for the Fastlit demo."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Home",
    "icon": "🏠",
    "default": True,
    "order": 0,
}

st.title("🚀 Fastlit Complete Demo")
st.markdown("""
Welcome to the **complete Fastlit components demo**! This app showcases **every component** 
with **all available parameters**.

The demo now uses Fastlit's **page system**, so each major category lives on its
own route and script. That makes it much easier to evolve the demo step by step.
""")

quick_links = st.columns(4)
with quick_links[0]:
    st.page_link("/page_system", label="Page System", icon="🗂️")
with quick_links[1]:
    st.page_link("/admin/users", label="Nested Route", icon="🛡️")
with quick_links[2]:
    st.page_link("/blog/42", label="Dynamic Route", icon="📝")
with quick_links[3]:
    st.page_link("/docs/guides/routing", label="Catch-All", icon="📚")

# Quick stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Components", "70+", delta="+5 new")
with col2:
    st.metric("Categories", "10", help="Component categories")
with col3:
    st.metric("Parameters", "200+", delta="documented")
with col4:
    st.metric("Examples", "50+", help="Code examples")

st.divider()

# Feature highlights
st.header("✨ Key Features")

features = st.columns(3)
with features[0]:
    st.subheader("⚡ Fast")
    st.markdown("""
    - Diff/patch UI updates
    - Partial reruns with fragments
    - Server-side DataFrame windows
    - WebSocket backpressure + coalescing
    - Compact patch payloads
    """)

with features[1]:
    st.subheader("🎯 Compatible")
    st.markdown("""
    - Same `st.*` API as Streamlit
    - Drop-in replacement
    - session_state works
    - Same caching decorators
    """)

with features[2]:
    st.subheader("🔧 Modern")
    st.markdown("""
    - React 18 frontend
    - Tailwind CSS styling
    - Radix UI components
    - Hot reload in dev
    """)

