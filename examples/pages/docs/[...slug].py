"""Catch-all docs page."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Docs Catch-All",
}

slug = st.context.route_params.get("slug", [])

st.title("📚 Catch-All Route")
st.caption("Example: `pages/docs/[...slug].py -> /docs/a/b/c`")
st.write("Current path:", st.context.path)
st.write("Extracted params:", st.context.route_params)
st.info(f"Resolved catch-all segments: {slug}")
