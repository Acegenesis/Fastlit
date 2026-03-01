"""Guarded admin page."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Secure",
    "icon": "🔒",
    "hidden": True,
    "guard": {
        "roles": ["admin"],
    },
}

st.title("🔒 Admin Secure")
st.caption("You should only see this page when the current user has the `admin` role.")
