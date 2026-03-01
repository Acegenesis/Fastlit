"""Admin layout for nested routing demos."""

import fastlit as st


st.info("Admin layout active", icon="🛡️")
st.caption("This content comes from `layouts/admin.py` before the page outlet.")

st.page_outlet()

st.caption("`layouts/admin.py` rendered this footer after the nested page.")
