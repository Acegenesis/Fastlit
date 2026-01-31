"""Fastlit Phase 1 demo: title + button + counter."""

import fastlit as st

st.title("Hello Fastlit")
st.markdown("Click the button to increment the counter.")

if "count" not in st.session_state:
    st.session_state.count = 0

if st.button("Increment"):
    st.session_state.count += 1

st.write(f"Count: {st.session_state.count}")
