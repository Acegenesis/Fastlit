"""Fastlit multipage demo entrypoint.

Run with:
    fastlit run examples/app.py --dev
"""

import fastlit as st

st.set_page_config(
    page_title="Fastlit Complete Demo",
    page_icon="\U0001F680",
    layout="wide",
    initial_sidebar_state="auto",
)

st.sidebar.title("\U0001F680 Fastlit Demo")
st.sidebar.caption("Complete components showcase")
st.sidebar.navigation(key="demo_pages_nav")

st.sidebar.divider()
st.sidebar.subheader("Sidebar Widgets")
sidebar_toggle = st.sidebar.toggle("Enable feature", value=True)
sidebar_slider = st.sidebar.slider("Value", 0, 100, 50)
st.sidebar.caption(f"Toggle: {sidebar_toggle} | Slider: {sidebar_slider}")

st.sidebar.divider()
st.sidebar.link_button(
    "\U0001F4D6 Documentation",
    "https://github.com/fastlit/fastlit",
    use_container_width=True,
)
st.sidebar.caption("Fastlit v0.2.0")

st.divider()
st.caption(
    "Built with **Fastlit** A Streamlit-compatible, blazing fast Python UI framework \U0001F680"
)
