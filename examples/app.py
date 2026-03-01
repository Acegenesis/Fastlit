"""Fastlit multipage demo entrypoint.

Run with:
    fastlit run examples/app.py --dev
"""

from __future__ import annotations

import fastlit as st


def main() -> None:
    st.set_page_config(
        page_title="Fastlit Complete Demo",
        page_icon="\U0001F680",
        layout="wide",
        initial_sidebar_state="auto",
    )

    st.sidebar.title("\U0001F680 Fastlit Demo")
    st.sidebar.caption("Complete components showcase")
    current_page = st.sidebar.navigation(key="demo_pages_nav")

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

    if isinstance(current_page, st.Page):
        current_page.run()

    st.divider()
    st.caption(
        "Built with **Fastlit** A Streamlit-compatible, blazing fast Python UI framework \U0001F680"
    )


if __name__ == "__main__":
    main()
