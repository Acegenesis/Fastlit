"""Fastlit — Demo of all layout & container components.

Tests: st.columns, st.container, st.tabs, st.expander,
       st.form, st.popover, st.empty, st.divider, st.dialog,
       plus all input widgets with Streamlit-compatible signatures.
"""

import fastlit as st

# ── Sidebar navigation ──────────────────────────────────────────────
st.sidebar.title("Components Demo")
page = st.sidebar.navigation(
    ["Layouts", "Containers", "Forms", "Widgets", "Dialog & Popover"],
)

st.title(f"Fastlit Components — {page}")

# =====================================================================
# LAYOUTS
# =====================================================================
if page == "Layouts":

    # ── Columns with gap & border ──
    st.header("Columns")
    st.write("3 columns with `border=True` and `gap='large'`:")
    c1, c2, c3 = st.columns(3, gap="large", border=True)
    with c1:
        st.write("**Column 1**")
        st.write("Equal width")
    with c2:
        st.write("**Column 2**")
        st.write("Equal width")
    with c3:
        st.write("**Column 3**")
        st.write("Equal width")

    st.divider()

    st.write("Weighted columns `[2, 1]` with `vertical_alignment='center'`:")
    left, right = st.columns([2, 1], vertical_alignment="center")
    with left:
        st.write("This is the wider column (2/3).")
        st.write("It has more content to show vertical alignment.")
    with right:
        st.write("Narrow (1/3), centered.")

    st.divider()

    # ── Tabs with default ──
    st.header("Tabs")
    tab_a, tab_b, tab_c = st.tabs(["Alpha", "Beta", "Gamma"], default="Beta")
    with tab_a:
        st.write("Content of **Alpha** tab.")
        st.slider("Alpha slider", 0, 100, 50)
    with tab_b:
        st.write("Content of **Beta** tab (default selected).")
        st.checkbox("Beta checkbox", value=True)
    with tab_c:
        st.write("Content of **Gamma** tab.")
        st.text_input("Gamma input", placeholder="Type here...")

    st.divider()

    # ── Expander with icon ──
    st.header("Expander")
    with st.expander("Click to expand (collapsed by default)"):
        st.write("Hidden content revealed!")
        st.slider("Hidden slider", 0, 50, 25)

    with st.expander("Already open expander", expanded=True):
        st.write("This one starts open.")
        st.number_input("Pick a number", min_value=0, max_value=100, value=42)


# =====================================================================
# CONTAINERS
# =====================================================================
elif page == "Containers":

    # ── Container with border ──
    st.header("Container")
    with st.container(border=True):
        st.write("This is inside a **bordered container**.")
        st.text_input("Name", placeholder="Your name")
        st.slider("Age", 0, 120, 25)

    st.divider()

    # ── Container with fixed height (scrollable) ──
    st.write("Container with `height=150` (scrollable):")
    with st.container(border=True, height=150):
        for i in range(20):
            st.write(f"Line {i + 1} — scrollable content")

    st.divider()

    # ── Empty placeholder ──
    st.header("Empty")
    st.write("`st.empty()` creates a single-element placeholder.")
    placeholder = st.empty()
    show = st.checkbox("Show content in placeholder")
    if show:
        placeholder.write("Now you see me!")
    else:
        placeholder.write("Toggle the checkbox above.")

    st.divider()

    # ── Divider ──
    st.header("Divider")
    st.write("Content above the divider.")
    st.divider()
    st.write("Content below the divider.")


# =====================================================================
# FORMS
# =====================================================================
elif page == "Forms":

    st.header("Form")
    st.write("Widgets inside a form don't trigger a rerun until submitted.")

    with st.form("demo_form", border=True):
        st.write("**User Registration**")
        username = st.text_input("Username", placeholder="johndoe")
        email = st.text_input("Email", placeholder="john@example.com")
        age = st.number_input("Age", min_value=1, max_value=150, value=25)
        role = st.selectbox("Role", ["Viewer", "Editor", "Admin"])
        agree = st.checkbox("I agree to the terms")
        submitted = st.form_submit_button("Register")

    if submitted:
        st.write(f"Submitted! username={username}, email={email}, age={age}, role={role}, agree={agree}")

    st.divider()

    st.header("Form with clear_on_submit")
    with st.form("clear_form", clear_on_submit=True, border=True):
        st.write("This form resets after submit.")
        message = st.text_area("Message", placeholder="Type a message...")
        sent = st.form_submit_button("Send")

    if sent:
        st.write(f"Sent: {message}")


# =====================================================================
# WIDGETS (all Streamlit-compatible signatures)
# =====================================================================
elif page == "Widgets":

    st.header("All Input Widgets")

    # ── Button variants ──
    st.subheader("Buttons")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Secondary (default)"):
            st.write("Clicked secondary!")
    with c2:
        if st.button("Primary", type="primary"):
            st.write("Clicked primary!")
    with c3:
        if st.button("Disabled", disabled=True):
            st.write("Should not appear")

    st.divider()

    # ── Slider ──
    st.subheader("Slider")
    val = st.slider("Pick a value", min_value=0, max_value=200, value=50, step=5,
                     help="Drag to select a value")
    st.write(f"Slider value: {val}")

    st.divider()

    # ── Number input ──
    st.subheader("Number Input")
    num = st.number_input("Quantity", min_value=0, max_value=1000, value=10, step=5,
                          help="Use +/- or type directly")
    st.write(f"Number: {num}")

    st.divider()

    # ── Text input with password type ──
    st.subheader("Text Input")
    name = st.text_input("Your name", placeholder="John Doe",
                         help="Enter your full name")
    pwd = st.text_input("Password", type="password", placeholder="********")
    if name:
        st.write(f"Hello, {name}!")
    if pwd:
        st.write(f"Password length: {len(pwd)} chars")

    st.divider()

    # ── Text area ──
    st.subheader("Text Area")
    bio = st.text_area("Bio", placeholder="Tell us about yourself...",
                       height=100, max_chars=500)
    if bio:
        st.write(f"Bio ({len(bio)}/500 chars): {bio}")

    st.divider()

    # ── Checkbox ──
    st.subheader("Checkbox")
    dark = st.checkbox("Dark mode", help="Enable dark theme")
    notifications = st.checkbox("Notifications", value=True)
    st.write(f"Dark mode: {dark}, Notifications: {notifications}")

    st.divider()

    # ── Selectbox ──
    st.subheader("Selectbox")
    color = st.selectbox("Favorite color", ["Red", "Green", "Blue", "Yellow"],
                         help="Pick one")
    st.write(f"Selected: {color}")

    st.divider()

    # ── Radio (vertical & horizontal) ──
    st.subheader("Radio")
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Vertical (default)**")
        size = st.radio("Size", ["S", "M", "L", "XL"])
        st.write(f"Size: {size}")
    with c2:
        st.write("**Horizontal**")
        priority = st.radio("Priority", ["Low", "Medium", "High"],
                            horizontal=True,
                            captions=["No rush", "Normal", "ASAP"])
        st.write(f"Priority: {priority}")


# =====================================================================
# DIALOG & POPOVER
# =====================================================================
elif page == "Dialog & Popover":

    st.header("Popover")
    st.write("Click the button to show a popover with content inside:")

    with st.popover("Settings"):
        st.write("**Popover content**")
        theme = st.radio("Theme", ["Light", "Dark", "System"], horizontal=True)
        lang = st.selectbox("Language", ["English", "French", "Spanish"])
        st.write(f"Theme: {theme}, Language: {lang}")

    st.divider()

    st.header("Dialog")
    st.write("Click the button below to open a modal dialog:")

    @st.dialog("Feedback Form", width="medium")
    def feedback_dialog():
        st.write("We'd love to hear from you!")
        rating = st.slider("Rating", 1, 5, 3)
        comment = st.text_area("Comment", placeholder="Your feedback...")
        if st.button("Submit Feedback"):
            st.session_state.feedback = {"rating": rating, "comment": comment}
            st.rerun()

    if "feedback" not in st.session_state:
        if st.button("Open Feedback Dialog"):
            feedback_dialog()
    else:
        fb = st.session_state.feedback
        st.write(f"Thank you! Rating: {fb['rating']}/5")
        if fb["comment"]:
            st.write(f"Comment: {fb['comment']}")
        if st.button("Clear feedback"):
            del st.session_state["feedback"]
            st.rerun()
