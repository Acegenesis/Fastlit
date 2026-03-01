"""Custom forbidden page."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Forbidden",
}

st.title("403")
st.warning("You do not have access to this route.")
st.write("Requested path:", st.context.path)
st.write("Route params:", st.context.route_params)
st.write("Guard failure:", st.context.guard_failure)
st.page_link("/page_system", label="Back to Page System", icon="🗂️")
