"""Parent admin page for nested routing demos."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Admin",
    "icon": "🛡️",
    "order": 5,
}

st.title("🛡️ Admin")
st.caption("Parent page example: `pages/admin/index.py -> /admin`")

st.markdown(
    """
This page is both:

- a real route at `/admin`
- the clickable parent entry for the `Admin` sidebar group
- a good place for section-level docs or dashboard content
"""
)

links = st.columns(2)
with links[0]:
    st.page_link("/admin/users", label="Users", icon="👥")
with links[1]:
    st.page_link("/admin/secure", label="Secure", icon="🔒")
