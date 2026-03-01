"""Dynamic blog page."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Blog Post",
}

post_id = st.context.route_params.get("id", "unknown")

st.title("📝 Dynamic Route")
st.caption("Example: `pages/blog/[id].py -> /blog/<id>`")
st.write("Current path:", st.context.path)
st.write("Extracted params:", st.context.route_params)
st.success(f"Resolved `id` = {post_id}")
