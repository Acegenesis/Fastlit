"""Nested admin users page."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Users",
    "icon": "🛡️",
    "order": 15,
}

st.title("🛡️ Admin / Users")
st.caption("Nested route example: `pages/admin/users.py -> /admin/users`")

st.write("Current path:", st.context.path)
st.write("Route params:", st.context.route_params)
st.write("Layouts:", st.context.layout_stack)

st.markdown("""
This page demonstrates:

- nested route discovery from subfolders
- automatic application of `layouts/admin.py`
- access to route info via `st.context`
""")
