"""Custom not-found page."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Not Found",
}

st.title("404")
st.error("No page matched this route.")
st.write("Requested path:", st.context.path)
st.page_link("/page_system", label="Back to Page System", icon="🗂️")
