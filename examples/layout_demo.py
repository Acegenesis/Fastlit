"""Fastlit Phase 3 demo: Layouts — sidebar, columns, tabs, expander."""

import fastlit as st

# --- Sidebar ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Page", ["Dashboard", "Settings", "About"])

# --- Main content ---
st.title(f"Fastlit Layout Demo — {page}")

if page == "Dashboard":
    # Columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.header("Users")
        st.write("1,234")
    with col2:
        st.header("Revenue")
        st.write("$5.6k")
    with col3:
        st.header("Growth")
        st.write("+12%")

    # Tabs
    tab1, tab2 = st.tabs(["Overview", "Details"])
    with tab1:
        st.write("This is the overview tab content.")
        st.slider("Chart zoom", 1, 100, 50)
    with tab2:
        st.write("This is the details tab with more info.")
        name = st.text_input("Search", placeholder="Filter...")
        if name:
            st.write(f"Searching for: {name}")

    # Expander
    with st.expander("Advanced options"):
        st.checkbox("Enable feature X")
        st.checkbox("Enable feature Y")
        st.number_input("Max retries", min_value=0, max_value=10, value=3)

elif page == "Settings":
    st.header("Settings")
    st.text_input("Username", "admin")
    st.text_input("Email", "admin@example.com")
    with st.expander("Danger zone", expanded=False):
        st.write("Careful with these settings!")
        if st.button("Reset all"):
            st.session_state.clear()
            st.rerun()

elif page == "About":
    st.header("About Fastlit")
    st.write("Fastlit is a Streamlit-compatible, blazing fast, Python-first UI framework.")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Version:** 0.1.0")
        st.write("**Python:** 3.11+")
    with col2:
        st.write("**Frontend:** React + Tailwind")
        st.write("**Protocol:** WebSocket patches")
