"""Input Widgets page for the Fastlit demo."""

from ast import main
import datetime

import fastlit as st

PAGE_CONFIG = {
    "title": "Input Widgets",
    "icon": "🎛️",
    "order": 30,
}

st.title("🎛️ Input Widgets")
st.caption("Interactive input components")

# -------------------------------------------------------------------------
# st.button()
# -------------------------------------------------------------------------
st.header("st.button()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Button label
    - `key` (str | None): Unique widget key
    - `help` (str | None): Tooltip
    - `on_click` (Callable): Callback function
    - `args` (tuple): Callback arguments
    - `kwargs` (dict): Callback keyword arguments
    - `type` (str): "primary", "secondary", "tertiary"
    - `icon` (str | None): Emoji or icon
    - `icon_position` (str): "left" or "right"
    - `disabled` (bool): Disable the button
    - `width` (str | int): "content", "stretch", or pixels
    - `shortcut` (str | None): Keyboard shortcut (e.g., "Ctrl+K")
    
    **Returns:** bool - True if clicked
    """)

st.code('''col1, col2, col3, col4 = st.columns(4)

with col1:
if st.button("Primary", type="primary"):
    st.toast("Primary clicked!")

with col2:
if st.button("Secondary", type="secondary"):
    st.toast("Secondary clicked!")

with col3:
if st.button("With Icon", icon="🚀"):
    st.toast("Icon button clicked!")

with col4:
st.button("Disabled", disabled=True)

# Full width button
if st.button("Full Width Button", width="stretch", type="primary", icon="🎯"):
st.balloons()''', language="python")

with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Primary", type="primary"):
            st.toast("Primary clicked!")
    
    with col2:
        if st.button("Secondary", type="secondary"):
            st.toast("Secondary clicked!")
    
    with col3:
        if st.button("With Icon", icon="🚀"):
            st.toast("Icon button clicked!")
    
    with col4:
        st.button("Disabled", disabled=True)
    
    # Full width button
    if st.button("Full Width Button", width="stretch", type="primary", icon="🎯"):
        st.balloons()

# -------------------------------------------------------------------------
# st.link_button()
# -------------------------------------------------------------------------
st.header("st.link_button()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Button label
    - `url` (str): URL to open
    - `help` (str | None): Tooltip
    - `type` (str): "primary", "secondary"
    - `icon` (str | None): Icon
    - `disabled` (bool): Disable
    - `use_container_width` (bool): Full width
    """)

st.code('''col1, col2, col3 = st.columns(3)
with col1:
st.link_button("GitHub", "https://github.com", icon="🐙")
with col2:
st.link_button("Google", "https://google.com", type="primary")
with col3:
st.link_button("Disabled", "https://example.com", disabled=True)''', language="python")

with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.link_button("GitHub", "https://github.com", icon="🐙")
    with col2:
        st.link_button("Google", "https://google.com", type="primary")
    with col3:
        st.link_button("Disabled", "https://example.com", disabled=True)

# -------------------------------------------------------------------------
# st.page_link()
# -------------------------------------------------------------------------
st.header("st.page_link()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `page` (str): Target page path or URL
    - `label` (str | None): Link label (defaults to `page`)
    - `icon` (str | None): Optional icon
    - `help` (str | None): Tooltip
    - `disabled` (bool): Disable interaction
    - `use_container_width` (bool): Full-width layout
    """)

st.code('''st.page_link("/index", label="Home", icon="🏠")
st.page_link("/charts", label="Charts page")
st.page_link("https://docs.streamlit.io", label="External docs")''', language="python")

with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.page_link("/index", label="Home", icon="🏠")
    with c2:
        st.page_link("/charts", label="Charts page")
    with c3:
        st.page_link("https://docs.streamlit.io", label="External docs")

# -------------------------------------------------------------------------
# st.download_button()
# -------------------------------------------------------------------------
st.header("st.download_button()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Button label
    - `data` (str | bytes): Data to download
    - `file_name` (str | None): Downloaded file name
    - `mime` (str | None): MIME type (auto-detected if None)
    - All button parameters (type, icon, disabled, etc.)
    
    **Returns:** bool - True if clicked
    """)

st.code('''csv_data = "name,age,city\\nAlice,30,Paris\\nBob,25,London\\nCharlie,35,Berlin"
st.download_button(
"📥 Download CSV",
data=csv_data,
file_name="users.csv",
mime="text/csv"
)

json_data = \'{"users": [{"name": "Alice"}, {"name": "Bob"}]}\'
st.download_button(
"📥 Download JSON",
data=json_data,
file_name="data.json",
mime="application/json"
)''', language="python")

with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_data = "name,age,city\nAlice,30,Paris\nBob,25,London\nCharlie,35,Berlin"
        st.download_button(
            "📥 Download CSV",
            data=csv_data,
            file_name="users.csv",
            mime="text/csv"
        )
    
    with col2:
        json_data = '{"users": [{"name": "Alice"}, {"name": "Bob"}]}'
        st.download_button(
            "📥 Download JSON",
            data=json_data,
            file_name="data.json",
            mime="application/json"
        )
    
    with col3:
        st.download_button(
            "📥 Download TXT",
            data="Hello, World!\nThis is a text file.",
            file_name="hello.txt",
            mime="text/plain"
        )

# -------------------------------------------------------------------------
# st.checkbox()
# -------------------------------------------------------------------------
st.header("st.checkbox()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Checkbox label
    - `value` (bool): Initial state (default: False)
    - `column_order` (list[str] | None): Column order
    - `column_config` (dict | None): Column rendering config
    - `row_height` (int | None): Fixed row height
    - `placeholder` (str | None): Empty state message
    - `toolbar` / `downloadable` / `persist_view`: UX controls
    - `key` (str | None): Unique key
    - `help` (str | None): Tooltip
    - `on_change` (Callable): Callback when changed
    - `args`, `kwargs`: Callback arguments
    - `disabled` (bool): Disable checkbox
    - `label_visibility` (str): "visible", "hidden", "collapsed"
    - `width` (str | int): Width
    
    **Returns:** bool
    """)

st.code('''agree = st.checkbox("I agree to the terms of service")
newsletter = st.checkbox("Subscribe to newsletter", value=True)
disabled_cb = st.checkbox("Disabled checkbox", disabled=True)

st.write(f"Agree: `{agree}`")
st.write(f"Newsletter: `{newsletter}`")''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        agree = st.checkbox("I agree to the terms of service")
        newsletter = st.checkbox("Subscribe to newsletter", value=True)
        disabled_cb = st.checkbox("Disabled checkbox", disabled=True)
    
    with col2:
        st.write(f"Agree: `{agree}`")
        st.write(f"Newsletter: `{newsletter}`")
        st.write(f"Disabled: `{disabled_cb}`")

# -------------------------------------------------------------------------
# st.toggle()
# -------------------------------------------------------------------------
st.header("st.toggle()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:** Same as st.checkbox()
    
    Visual difference: Switch/toggle style instead of checkbox.
    
    **Returns:** bool
    """)

st.code('''dark_mode = st.toggle("Dark mode", value=False)
notifications = st.toggle("Notifications", value=True)
auto_save = st.toggle("Auto-save", value=True, help="Save changes automatically")

st.write(f"Dark mode: `{dark_mode}`")
st.write(f"Notifications: `{notifications}`")
st.write(f"Auto-save: `{auto_save}`")''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        dark_mode = st.toggle("Dark mode", value=False)
        notifications = st.toggle("Notifications", value=True)
        auto_save = st.toggle("Auto-save", value=True, help="Save changes automatically")
    
    with col2:
        st.write(f"Dark mode: `{dark_mode}`")
        st.write(f"Notifications: `{notifications}`")
        st.write(f"Auto-save: `{auto_save}`")

# -------------------------------------------------------------------------
# st.radio()
# -------------------------------------------------------------------------
st.header("st.radio()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `options` (Sequence): List of options
    - `index` (int | None): Default selection index (None for no selection)
    - `format_func` (Callable): Function to format option labels
    - `key`, `help`, `on_change`, `args`, `kwargs`: Standard params
    - `disabled` (bool): Disable widget
    - `horizontal` (bool): Arrange options horizontally
    - `captions` (Sequence[str]): Captions below each option
    - `label_visibility`, `width`: Layout params
    
    **Returns:** Selected option value
    """)

st.code('''lang = st.radio(
"Programming Language",
["Python", "JavaScript", "Rust", "Go"],
horizontal=True,
captions=["Dynamic typing", "Web & Node", "Memory safe", "Simple & fast"]
)

plan = st.radio(
"Select Plan",
["Free", "Pro ($10/mo)", "Enterprise ($50/mo)"],
index=1
)

st.write(f"Language: `{lang}` | Plan: `{plan}`")''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        lang = st.radio(
            "Programming Language",
            ["Python", "JavaScript", "Rust", "Go"],
            horizontal=True,
            captions=["Dynamic typing", "Web & Node", "Memory safe", "Simple & fast"]
        )
    
    with col2:
        plan = st.radio(
            "Select Plan",
            ["Free", "Pro ($10/mo)", "Enterprise ($50/mo)"],
            index=1
        )
    
    st.write(f"Language: `{lang}` | Plan: `{plan}`")

# -------------------------------------------------------------------------
# st.selectbox()
# -------------------------------------------------------------------------
st.header("st.selectbox()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `options` (Sequence): Options to select from
    - `index` (int | None): Default index (None for empty selection)
    - `format_func` (Callable): Format option labels
    - `placeholder` (str | None): Placeholder text
    - `disabled` (bool): Disable widget
    - `accept_new_options` (bool): Allow user to add new options
    - `label_visibility`, `width`: Layout params
    
    **Returns:** Selected value or None
    """)

st.code('''country = st.selectbox(
"Country",
["France", "Germany", "Italy", "Spain", "UK", "USA"],
placeholder="Choose a country..."
)

city = st.selectbox(
"City (with new options)",
["Paris", "London", "Berlin"],
accept_new_options=True,
help="You can type a new city!"
)

st.write(f"Country: `{country}` | City: `{city}`")''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        country = st.selectbox(
            "Country",
            ["France", "Germany", "Italy", "Spain", "UK", "USA"],
            placeholder="Choose a country..."
        )
    
    with col2:
        city = st.selectbox(
            "City (with new options)",
            ["Paris", "London", "Berlin"],
            accept_new_options=True,
            help="You can type a new city!"
        )
    
    st.write(f"Country: `{country}` | City: `{city}`")

# -------------------------------------------------------------------------
# st.multiselect()
# -------------------------------------------------------------------------
st.header("st.multiselect()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `options` (Sequence): Options to select from
    - `default` (Sequence | None): Default selected values
    - `format_func` (Callable): Format option labels
    - `max_selections` (int | None): Maximum selections allowed
    - `placeholder` (str): Placeholder text
    - `accept_new_options` (bool): Allow adding new options
    
    **Returns:** list of selected values
    """)

st.code('''skills = st.multiselect(
"Select your skills (max 4)",
["Python", "JavaScript", "SQL", "Docker", "Kubernetes", "AWS", "GCP", "Azure"],
default=["Python", "SQL"],
max_selections=4
)

tags = st.multiselect(
"Add tags (can create new)",
["bug", "feature", "documentation", "help wanted"],
accept_new_options=True
)

st.write(f"Skills: `{skills}`")
st.write(f"Tags: `{tags}`")''', language="python")

with st.container(border=True):
    skills = st.multiselect(
        "Select your skills (max 4)",
        ["Python", "JavaScript", "SQL", "Docker", "Kubernetes", "AWS", "GCP", "Azure"],
        default=["Python", "SQL"],
        max_selections=4
    )
    
    tags = st.multiselect(
        "Add tags (can create new)",
        ["bug", "feature", "documentation", "help wanted"],
        accept_new_options=True
    )
    
    st.write(f"Skills: `{skills}`")
    st.write(f"Tags: `{tags}`")

# -------------------------------------------------------------------------
# st.slider()
# -------------------------------------------------------------------------
st.header("st.slider()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `min_value` (float | None): Minimum value (default: 0)
    - `max_value` (float | None): Maximum value (default: 100)
    - `value` (float | tuple | None): Initial value(s) - tuple for range slider
    - `step` (float | None): Step increment
    - `format` (str | None): Printf format (e.g., "%.2f", "percent")
    - `disabled` (bool): Disable slider
    
    **Returns:** float/int or tuple for range slider
    """)

st.code('''volume = st.slider("Volume", 0, 100, 50)
temperature = st.slider("Temperature", -20.0, 40.0, 20.0, step=0.5, format="%.1f°C")
price_range = st.slider("Price Range", 0.0, 1000.0, (100.0, 500.0), format="$%.2f")
age_range = st.slider("Age Range", 18, 100, (25, 45))

st.write(f"Volume: `{volume}` | Temp: `{temperature}`")
st.write(f"Price: `{price_range}` | Age: `{age_range}`")''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        volume = st.slider("Volume", 0, 100, 50)
        temperature = st.slider("Temperature", -20.0, 40.0, 20.0, step=0.5, format="%.1f°C")
    
    with col2:
        price_range = st.slider("Price Range", 0.0, 1000.0, (100.0, 500.0), format="$%.2f")
        age_range = st.slider("Age Range", 18, 100, (25, 45))
    
    st.write(f"Volume: `{volume}` | Temp: `{temperature}`")
    st.write(f"Price: `{price_range}` | Age: `{age_range}`")

# -------------------------------------------------------------------------
# st.select_slider()
# -------------------------------------------------------------------------
st.header("st.select_slider()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `options` (Sequence): Options to select from
    - `value` (Any | tuple): Default value(s)
    - `format_func` (Callable): Format labels
    
    **Returns:** Selected value or tuple for range
    """)

st.code('''size = st.select_slider("T-Shirt Size", ["XS", "S", "M", "L", "XL", "XXL"], value="M")

quality = st.select_slider(
"Quality Range",
["Poor", "Fair", "Good", "Very Good", "Excellent"],
value=("Fair", "Very Good")
)

st.write(f"Size: `{size}` | Quality: `{quality}`")''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        size = st.select_slider("T-Shirt Size", ["XS", "S", "M", "L", "XL", "XXL"], value="M")
    
    with col2:
        quality = st.select_slider(
            "Quality Range",
            ["Poor", "Fair", "Good", "Very Good", "Excellent"],
            value=("Fair", "Very Good")
        )
    
    st.write(f"Size: `{size}` | Quality: `{quality}`")

# -------------------------------------------------------------------------
# st.number_input()
# -------------------------------------------------------------------------
st.header("st.number_input()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `min_value`, `max_value` (float | None): Range limits
    - `value` (float | int | str): Initial value ("min" for min_value)
    - `step` (float | None): Step increment (1 for int, 0.01 for float)
    - `format` (str | None): Printf format
    - `placeholder` (str | None): Placeholder text
    - `icon` (str | None): Icon before input
    
    **Returns:** int or float
    """)

st.code('''quantity = st.number_input("Quantity", min_value=1, max_value=100, value=1)
price = st.number_input("Price ($)", min_value=0.0, value=9.99, step=0.01, format="%.2f")
year = st.number_input("Year", min_value=1900, max_value=2100, value=2024)

st.write(f"Quantity: `{quantity}` | Price: `${price:.2f}` | Year: `{year}`")''', language="python")

with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        quantity = st.number_input("Quantity", min_value=1, max_value=100, value=1)
    
    with col2:
        price = st.number_input("Price ($)", min_value=0.0, value=9.99, step=0.01, format="%.2f")
    
    with col3:
        year = st.number_input("Year", min_value=1900, max_value=2100, value=2024)
    
    st.write(f"Quantity: `{quantity}` | Price: `${price:.2f}` | Year: `{year}`")

# -------------------------------------------------------------------------
# st.text_input()
# -------------------------------------------------------------------------
st.header("st.text_input()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `value` (str): Initial value
    - `max_chars` (int | None): Maximum characters
    - `type` (str): "default" or "password"
    - `placeholder` (str | None): Placeholder text
    - `autocomplete` (str | None): HTML autocomplete attribute
    - `icon` (str | None): Icon or "spinner"
    
    **Returns:** str
    """)

st.code('''name = st.text_input("Full Name", placeholder="Enter your name...")
email = st.text_input("Email", placeholder="you@example.com", autocomplete="email")
username = st.text_input("Username", max_chars=20, help="Max 20 characters")
password = st.text_input("Password", type="password", placeholder="••••••••")

st.write(f"Name: `{name}` | Email: `{email}` | Username: `{username}`")''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Full Name", placeholder="Enter your name...")
        email = st.text_input("Email", placeholder="you@example.com", autocomplete="email")
    
    with col2:
        username = st.text_input("Username", max_chars=20, help="Max 20 characters")
        password = st.text_input("Password", type="password", placeholder="••••••••")
    
    st.write(f"Name: `{name}` | Email: `{email}` | Username: `{username}`")

# -------------------------------------------------------------------------
# st.text_area()
# -------------------------------------------------------------------------
st.header("st.text_area()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `value` (str): Initial value
    - `height` (str | int | None): None (3 lines), "content", "stretch", or pixels
    - `max_chars` (int | None): Maximum characters
    - `placeholder` (str | None): Placeholder
    
    **Returns:** str
    """)

st.code('''bio = st.text_area(
"Tell us about yourself",
height=100,
placeholder="Write a short bio...",
help="Markdown is supported"
)

code = st.text_area(
"Paste your code",
height=150,
placeholder="# Your code here..."
)

st.caption(f"Bio length: {len(bio)} chars | Code length: {len(code)} chars")''', language="python")

with st.container(border=True):
    bio = st.text_area(
        "Tell us about yourself",
        height=100,
        placeholder="Write a short bio...",
        help="Markdown is supported"
    )
    
    code = st.text_area(
        "Paste your code",
        height=150,
        placeholder="# Your code here..."
    )
    
    st.caption(f"Bio length: {len(bio)} chars | Code length: {len(code)} chars")

# -------------------------------------------------------------------------
# st.date_input()
# -------------------------------------------------------------------------
st.header("st.date_input()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `value` (date | tuple | str | None): Default date(s) - "today" for current date
    - `min_value`, `max_value` (date | None): Date range limits
    - `format` (str): Display format - "YYYY/MM/DD", "DD/MM/YYYY", "MM/DD/YYYY"
    
    **Returns:** date or tuple[date, date] for range
    """)

st.code('''single_date = st.date_input(
"Select a date",
value=datetime.date.today(),
min_value=datetime.date(2020, 1, 1),
max_value=datetime.date(2030, 12, 31)
)

date_range = st.date_input(
"Select date range",
value=(datetime.date.today(), datetime.date.today() + datetime.timedelta(days=7)),
format="DD/MM/YYYY"
)

st.write(f"Single: `{single_date}` | Range: `{date_range}`")''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        single_date = st.date_input(
            "Select a date",
            value=datetime.date.today(),
            min_value=datetime.date(2020, 1, 1),
            max_value=datetime.date(2030, 12, 31)
        )
    
    with col2:
        date_range = st.date_input(
            "Select date range",
            value=(datetime.date.today(), datetime.date.today() + datetime.timedelta(days=7)),
            format="DD/MM/YYYY"
        )
    
    st.write(f"Single: `{single_date}` | Range: `{date_range}`")

# -------------------------------------------------------------------------
# st.time_input()
# -------------------------------------------------------------------------
st.header("st.time_input()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `value` (time | str | None): Default time - "now" for current time
    - `step` (int): Step in seconds (default: 900 = 15 minutes)
    
    **Returns:** datetime.time
    """)

st.code('''start_time = st.time_input("Start time", datetime.time(9, 0), step=900)
end_time = st.time_input("End time", datetime.time(17, 0), step=900)

st.write(f"Start: `{start_time}` | End: `{end_time}`")''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        start_time = st.time_input("Start time", datetime.time(9, 0), step=900)
    
    with col2:
        end_time = st.time_input("End time", datetime.time(17, 0), step=900)
    
    st.write(f"Start: `{start_time}` | End: `{end_time}`")

# -------------------------------------------------------------------------
# st.color_picker()
# -------------------------------------------------------------------------
st.header("st.color_picker()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `value` (str): Default hex color (e.g., "#FF0000")
    
    **Returns:** str (hex color)
    """)

st.code('''primary = st.color_picker("Primary", "#3B82F6")
secondary = st.color_picker("Secondary", "#10B981")
accent = st.color_picker("Accent", "#F59E0B")''', language="python")

with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        primary = st.color_picker("Primary", "#3B82F6")
    with col2:
        secondary = st.color_picker("Secondary", "#10B981")
    with col3:
        accent = st.color_picker("Accent", "#F59E0B")
    
    st.html(f"""
    <div style="display: flex; gap: 10px;">
        <div style="width: 100px; height: 50px; background: {primary}; border-radius: 8px;"></div>
        <div style="width: 100px; height: 50px; background: {secondary}; border-radius: 8px;"></div>
        <div style="width: 100px; height: 50px; background: {accent}; border-radius: 8px;"></div>
    </div>
    """)

# -------------------------------------------------------------------------
# st.file_uploader()
# -------------------------------------------------------------------------
st.header("st.file_uploader()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `type` (str | list | None): Allowed file extensions (e.g., ["csv", "txt"])
    - `accept_multiple_files` (bool): Allow multiple file uploads
    
    **Returns:** UploadedFile | list[UploadedFile] | None
    
    **UploadedFile properties:**
    - `name`: File name
    - `type`: MIME type
    - `size`: Size in bytes
    - `read()`: Read content as bytes
    - `getvalue()`: Get all bytes
    """)

st.code('''single_file = st.file_uploader(
"Upload a single file",
type=["csv", "txt", "json"],
help="Supported: CSV, TXT, JSON"
)

if single_file:
st.success(f"Uploaded: {single_file.name} ({single_file.size} bytes)")

multi_files = st.file_uploader(
"Upload multiple files",
type=["png", "jpg", "jpeg", "gif"],
accept_multiple_files=True
)

if multi_files:
for f in multi_files:
    st.info(f"📄 {f.name} ({f.size} bytes)")''', language="python")

with st.container(border=True):
    st.caption(f"Uploaded file object type: `{st.UploadedFile.__name__}`")

    single_file = st.file_uploader(
        "Upload a single file",
        type=["csv", "txt", "json"],
        help="Supported: CSV, TXT, JSON"
    )
    
    if single_file:
        st.success(f"Uploaded: {single_file.name} ({single_file.size} bytes)")
    
    multi_files = st.file_uploader(
        "Upload multiple files",
        type=["png", "jpg", "jpeg", "gif"],
        accept_multiple_files=True
    )
    
    if multi_files:
        for f in multi_files:
            st.info(f"📄 {f.name} ({f.size} bytes)")

# -------------------------------------------------------------------------
# st.camera_input()
# -------------------------------------------------------------------------
st.header("st.camera_input()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `key` (str | None): Unique widget key
    - `help` (str | None): Tooltip text
    - `disabled` (bool): Disable capture
    - `label_visibility` (str): "visible", "hidden", "collapsed"

    **Returns:** `UploadedFile | None`

    **Notes:**
    - Uses browser camera permission.
    - Upload size guardrails are enforced server-side.
    """)

st.code('''photo = st.camera_input("Take a picture")

if photo:
data = photo.read()
st.success(f"Captured: {photo.name} ({photo.size} bytes)")
st.image(data, caption="Camera snapshot")
else:
st.info("Allow camera access then capture an image.")''', language="python")

with st.container(border=True):
    photo = st.camera_input("Take a picture")
    if photo:
        data = photo.read()
        st.success(f"Captured: {photo.name} ({photo.size} bytes)")
        st.image(data, caption="Camera snapshot")
    else:
        st.info("Allow camera access then capture an image.")

# -------------------------------------------------------------------------
# st.audio_input()
# -------------------------------------------------------------------------
st.header("st.audio_input()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `key` (str | None): Unique widget key
    - `help` (str | None): Tooltip text
    - `disabled` (bool): Disable recorder
    - `label_visibility` (str): "visible", "hidden", "collapsed"

    **Returns:** `UploadedFile | None`

    **Notes:**
    - Uses browser microphone permission.
    - Upload size guardrails are enforced server-side.
    """)

st.code('''audio = st.audio_input("Record audio")

if audio:
data = audio.read()
st.success(f"Recorded: {audio.name} ({audio.size} bytes)")
st.audio(data, format=audio.type)
else:
st.info("Allow microphone access then record audio.")''', language="python")

with st.container(border=True):
    audio = st.audio_input("Record audio")
    if audio:
        data = audio.read()
        st.success(f"Recorded: {audio.name} ({audio.size} bytes)")
        st.audio(data, format=audio.type)
    else:
        st.info("Allow microphone access then record audio.")

# -------------------------------------------------------------------------
# st.feedback()
# -------------------------------------------------------------------------
st.header("st.feedback()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `sentiment_mapping` (dict | str | None): Feedback style:
        - "thumbs": 👍/👎
        - "stars": ⭐ rating
        - "faces": 😀/😐/😞
        - dict: Custom mapping
    
    **Returns:** int | None (selected index)
    """)

st.code('''thumbs = st.feedback("thumbs")
stars = st.feedback("stars")
faces = st.feedback("faces")

st.write(f"Thumbs: `{thumbs}` | Stars: `{stars}` | Faces: `{faces}`")''', language="python")

with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("Thumbs")
        thumbs = st.feedback("thumbs")
        st.write(f"Value: `{thumbs}`")
    
    with col2:
        st.caption("Stars")
        stars = st.feedback("stars")
        st.write(f"Value: `{stars}`")
    
    with col3:
        st.caption("Faces")
        faces = st.feedback("faces")
        st.write(f"Value: `{faces}`")

# -------------------------------------------------------------------------
# st.pills()
# -------------------------------------------------------------------------
st.header("st.pills()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `label` (str): Widget label
    - `options` (Sequence): Options
    - `selection_mode` (str): "single" or "multi"
    - `default` (Any): Default selection
    - `format_func` (Callable): Format labels
    
    **Returns:** value (single) or list (multi)
    """)

st.code('''category = st.pills(
"Filter by category",
["All", "Technology", "Design", "Marketing", "Finance"],
default="All"
)

features = st.pills(
"Select features",
["Fast", "Secure", "Scalable", "Modern", "Easy"],
selection_mode="multi",
default=["Fast", "Modern"]
)

st.write(f"Category: `{category}`")
st.write(f"Features: `{features}`")''', language="python")

with st.container(border=True):
    category = st.pills(
        "Filter by category",
        ["All", "Technology", "Design", "Marketing", "Finance"],
        default="All"
    )
    
    features = st.pills(
        "Select features",
        ["Fast", "Secure", "Scalable", "Modern", "Easy"],
        selection_mode="multi",
        default=["Fast", "Modern"]
    )
    
    st.write(f"Category: `{category}`")
    st.write(f"Features: `{features}`")

# -------------------------------------------------------------------------
# st.segmented_control()
# -------------------------------------------------------------------------
st.header("st.segmented_control()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:** Same as st.pills()
    
    Visual difference: Button group style instead of pills.
    """)

st.code('''view = st.segmented_control(
"View mode",
["📋 List", "📊 Grid", "📈 Chart"],
default="📋 List"
)

theme = st.segmented_control(
"Theme",
["Light", "Dark", "System"],
default="System"
)

st.write(f"View: `{view}` | Theme: `{theme}`")''', language="python")

with st.container(border=True):
    view = st.segmented_control(
        "View mode",
        ["📋 List", "📊 Grid", "📈 Chart"],
        default="📋 List"
    )
    
    theme = st.segmented_control(
        "Theme",
        ["Light", "Dark", "System"],
        default="System"
    )
    
    st.write(f"View: `{view}` | Theme: `{theme}`")
