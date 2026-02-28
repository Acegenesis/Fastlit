"""
Fastlit Complete Components Demo
================================
A comprehensive test of ALL Fastlit components with all parameters.

Run with: fastlit run examples/all_components_demo.py --dev
Prod profile: fastlit run examples/all_components_demo.py --host 0.0.0.0 --port 8501 --workers 4 --limit-concurrency 200 --backlog 2048 --max-sessions 300 --max-concurrent-runs 8 --run-timeout-seconds 45
"""

import fastlit as st
import datetime
import inspect
import time

# =============================================================================
# PAGE CONFIGURATION (must be first!)
# =============================================================================
st.set_page_config(
    page_title="Fastlit Complete Demo",
    page_icon="🚀",
    layout="wide",  # "centered", "wide", "compact"
    initial_sidebar_state="auto",  # "auto", "expanded", "collapsed"
)

# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
st.sidebar.title("🚀 Fastlit Demo")
st.sidebar.caption("Complete components showcase")

sections = [
    "🏠 Home",
    "New in Fastlit",
    "📝 Text Elements",
    "🎛️ Input Widgets",
    "📊 Data Display",
    "📈 Charts",
    "🖼️ Media",
    "⚡ Status & Feedback",
    "📐 Layout",
    "💬 Chat Components",
    "🔧 State & Control",
    "🎨 Advanced Features",
    "🔄 Streaming & Fragments",
    "🧩 Custom Components",
    "🔐 Auth (Beta)",
]

selected = st.sidebar.navigation(sections)

st.sidebar.divider()

# Sidebar widgets demo
st.sidebar.subheader("Sidebar Widgets")
sidebar_toggle = st.sidebar.toggle("Enable feature", value=True)
sidebar_slider = st.sidebar.slider("Value", 0, 100, 50)
st.sidebar.caption(f"Toggle: {sidebar_toggle} | Slider: {sidebar_slider}")

st.sidebar.divider()
st.sidebar.link_button("📖 Documentation", "https://github.com/fastlit/fastlit", use_container_width=True)
st.sidebar.caption("Fastlit v0.2.0")



# =============================================================================
# 🏠 HOME
# =============================================================================
if selected == "🏠 Home":
    st.title("🚀 Fastlit Complete Demo")
    st.markdown("""
    Welcome to the **complete Fastlit components demo**! This app showcases **every component** 
    with **all available parameters**.
    
    Use the **sidebar navigation** to explore different component categories.
    """)
    
    st.divider()
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Components", "70+", delta="+5 new")
    with col2:
        st.metric("Categories", "10", help="Component categories")
    with col3:
        st.metric("Parameters", "200+", delta="documented")
    with col4:
        st.metric("Examples", "50+", help="Code examples")
    
    st.divider()
    
    # Feature highlights
    st.header("✨ Key Features")
    
    features = st.columns(3)
    with features[0]:
        st.subheader("⚡ Fast")
        st.markdown("""
        - Diff/patch UI updates
        - Partial reruns with fragments
        - Server-side DataFrame windows
        - WebSocket backpressure + coalescing
        - Compact patch payloads
        """)
    
    with features[1]:
        st.subheader("🎯 Compatible")
        st.markdown("""
        - Same `st.*` API as Streamlit
        - Drop-in replacement
        - session_state works
        - Same caching decorators
        """)
    
    with features[2]:
        st.subheader("🔧 Modern")
        st.markdown("""
        - React 18 frontend
        - Tailwind CSS styling
        - Radix UI components
        - Hot reload in dev
        """)


# =============================================================================
# NEW IN FASTLIT
# =============================================================================
elif selected == "New in Fastlit":
    st.title("New in Fastlit")
    st.caption("Dedicated overview of recently added runtime and API features")

    st.header("1) Media Inputs", divider="blue")
    st.markdown("""
    New widgets now available with dedicated demo sections:
    - `st.camera_input()`
    - `st.audio_input()`
    """)
    st.code('''photo = st.camera_input("Take a picture")
if photo:
    st.image(photo.read(), caption=f"{photo.name} ({photo.size} bytes)")

audio = st.audio_input("Record audio")
if audio:
    st.audio(audio.read(), format=audio.type)''', language="python")

    st.header("2) Streaming + Fragments", divider="blue")
    st.markdown("""
    Runtime now focuses on patch streaming and partial reruns:
    - WebSocket patch streaming
    - Fragment-local reruns when possible
    - Reduced full-script reruns
    """)
    st.code('''st.markdown("Main page content remains stable")

with st.fragment("demo_fragment"):
    if st.button("Refresh only this fragment"):
        st.rerun(scope="fragment")
    st.write("This block reruns independently when possible.")''', language="python")

    st.header("3) Spinner Runtime Behavior", divider="blue")
    st.markdown("""
    `st.spinner()` now appears immediately during execution, then disappears automatically.
    """)
    st.code('''if st.button("Run task"):
    with st.spinner("Processing..."):
        time.sleep(1.5)
    st.success("Done")''', language="python")

    st.header("4) Cache Guarantees", divider="blue")
    st.markdown("""
    Cache behavior has been hardened:
    - `my_cached_fn.clear()` clears only that function cache
    - `@st.cache_resource` creation is synchronized per key
    """)
    st.code('''@st.cache_data
def users():
    return fetch_users()

@st.cache_data
def products():
    return fetch_products()

users.clear()  # does not clear products cache''', language="python")

    st.header("5) Secrets Hot Reload", divider="blue")
    st.markdown("""
    `st.secrets` now reloads when the active `secrets.toml` file changes.
    """)
    st.code('''db_host = st.secrets["database"]["host"]
api_key = st.secrets.api.key''', language="python")


# =============================================================================
# 📝 TEXT ELEMENTS
# =============================================================================
elif selected == "📝 Text Elements":
    st.title("📝 Text Elements")
    st.caption("Components for displaying text content")
    
    # -------------------------------------------------------------------------
    # st.title()
    # -------------------------------------------------------------------------
    st.header("st.title()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `body` (str): Title text (supports Markdown)
        - `anchor` (str | bool | None): Custom anchor ID, False to disable
        - `help` (str | None): Tooltip text
        - `width` (str | int): "stretch", "content", or pixel value
        - `text_alignment` (str): "left", "center", "right", "justify"
        """)
    
    st.code('''st.title("Main Title")
st.title("With Help Tooltip", help="This is helpful tooltip text!")
st.title("Centered Title", text_alignment="center")''', language="python")
    
    with st.container(border=True):
        st.title("Main Title")
        st.title("With Help Tooltip", help="This is helpful tooltip text!")
        st.title("Centered Title", text_alignment="center")
    
    # -------------------------------------------------------------------------
    # st.header()
    # -------------------------------------------------------------------------
    st.header("st.header()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `body` (str): Header text
        - `anchor` (str | bool | None): Custom anchor ID
        - `divider` (bool | str): Show divider - True, False, or color ("blue", "green", "orange", "red", "violet", "rainbow")
        - `help` (str | None): Tooltip text
        - `width`, `text_alignment`: Same as title
        """)
    
    st.code('''st.header("With Default Divider", divider=True)
st.header("Blue Divider", divider="blue")
st.header("Green Divider", divider="green")
st.header("Orange Divider", divider="orange")
st.header("Rainbow Divider", divider="rainbow")''', language="python")
    
    with st.container(border=True):
        st.header("With Default Divider", divider=True)
        st.header("Blue Divider", divider="blue")
        st.header("Green Divider", divider="green")
        st.header("Orange Divider", divider="orange")
        st.header("Rainbow Divider", divider="rainbow")
    
    # -------------------------------------------------------------------------
    # st.subheader()
    # -------------------------------------------------------------------------
    st.header("st.subheader()", divider="blue")
    
    st.code('''st.subheader("Default Subheader")
st.subheader("With Divider", divider="violet")
st.subheader("With Help", help="Subheader tooltip")''', language="python")
    
    with st.container(border=True):
        st.subheader("Default Subheader")
        st.subheader("With Divider", divider="violet")
        st.subheader("With Help", help="Subheader tooltip")
    
    # -------------------------------------------------------------------------
    # st.markdown()
    # -------------------------------------------------------------------------
    st.header("st.markdown()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `body` (str): Markdown text
        - `unsafe_allow_html` (bool): Allow raw HTML (use with caution!)
        - `help` (str | None): Tooltip
        - `width`, `text_alignment`: Layout options
        
        **Special syntax:**
        - `:emoji_name:` for emoji shortcodes
        - `:color[text]` for colored text (blue, green, red, orange, violet)
        - `:color-background[text]` for highlighted background
        - `$math$` for inline LaTeX
        - `$$math$$` for block LaTeX
        """)
    
    st.code('''st.markdown("**Bold**, *italic*, ~~strikethrough~~, `code`")
st.markdown(":blue[Blue text] :green[Green] :red[Red] :orange[Orange] :violet[Violet]")
st.markdown(":blue-background[Blue bg] :red-background[Red bg] :green-background[Green bg]")
st.markdown("Emoji shortcodes: :rocket: :fire: :heart: :star: :+1:")
st.markdown("Inline math: $E = mc^2$ and $\\sum_{i=1}^n x_i$")
st.markdown("[Link text](https://example.com)")''', language="python")
    
    with st.container(border=True):
        st.markdown("**Bold**, *italic*, ~~strikethrough~~, `code`")
        st.markdown(":blue[Blue text] :green[Green] :red[Red] :orange[Orange] :violet[Violet]")
        st.markdown(":blue-background[Blue bg] :red-background[Red bg] :green-background[Green bg]")
        st.markdown("Emoji shortcodes: :rocket: :fire: :heart: :star: :+1:")
        st.markdown("Inline math: $E = mc^2$ and $\\sum_{i=1}^n x_i$")
        st.markdown("[Link text](https://example.com)")
        st.markdown("""
        - Bullet list item 1
        - Bullet list item 2
          - Nested item
        
        1. Numbered item 1
        2. Numbered item 2
        """)
    
    # -------------------------------------------------------------------------
    # st.write()
    # -------------------------------------------------------------------------
    st.header("st.write()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Smart content renderer** - automatically detects type:
        - `str` → Markdown
        - `dict`, `list` → JSON viewer
        - `pd.DataFrame` → Interactive dataframe
        - `Exception` → Error with traceback
        - Plotly/Altair figures → Charts
        
        **Parameters:**
        - `*args`: Any number of objects to display
        - `unsafe_allow_html` (bool): Allow HTML in strings
        """)
    
    st.code('''st.write("Simple string becomes markdown")
st.write("Multiple", "arguments", "work!")
st.write({"name": "Fastlit", "version": "0.1.0", "features": ["fast", "compatible"]})
st.write([1, 2, 3, "four", {"five": 5}])''', language="python")
    
    with st.container(border=True):
        st.write("Simple string becomes markdown")
        st.write("Multiple", "arguments", "work!")
        st.write({"name": "Fastlit", "version": "0.1.0", "features": ["fast", "compatible"]})
        st.write([1, 2, 3, "four", {"five": 5}])
    
    # -------------------------------------------------------------------------
    # st.text()
    # -------------------------------------------------------------------------
    st.header("st.text()", divider="blue")
    
    st.code('''st.text("This is fixed-width monospace text.")
st.text("Useful for preformatted output.")''', language="python")
    
    with st.container(border=True):
        st.text("This is fixed-width monospace text.")
        st.text("Useful for preformatted output.")
    
    # -------------------------------------------------------------------------
    # st.code()
    # -------------------------------------------------------------------------
    st.header("st.code()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `body` (str): Code to display
        - `language` (str | None): Language for syntax highlighting
        - `line_numbers` (bool): Show line numbers
        - `wrap_lines` (bool): Wrap long lines
        - `height` (str | int): "content", "stretch", or pixels
        - `width` (str | int): Width
        """)
    
    st.code('''st.code(\'''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate first 10 numbers
for i in range(10):
    print(fibonacci(i))\''', language="python", line_numbers=True)

st.code('SELECT * FROM users WHERE active = true;', language="sql")
st.code('const hello = () => console.log("Hello!");', language="javascript")''', language="python")
    
    with st.container(border=True):
        st.code('''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate first 10 numbers
for i in range(10):
    print(fibonacci(i))''', language="python", line_numbers=True)
        
        st.code('SELECT * FROM users WHERE active = true;', language="sql")
        st.code('const hello = () => console.log("Hello!");', language="javascript")
    
    # -------------------------------------------------------------------------
    # st.caption()
    # -------------------------------------------------------------------------
    st.header("st.caption()", divider="blue")
    
    st.code('''st.caption("This is a small caption for footnotes and metadata.")
st.caption("Supports **markdown** and :blue[colors] too!")''', language="python")
    
    with st.container(border=True):
        st.caption("This is a small caption for footnotes and metadata.")
        st.caption("Supports **markdown** and :blue[colors] too!")
    
    # -------------------------------------------------------------------------
    # st.latex()
    # -------------------------------------------------------------------------
    st.header("st.latex()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `body` (str): LaTeX expression (no delimiters needed)
        - `help` (str | None): Tooltip
        - `width` (str | int): Width
        """)
    
    st.code('''st.latex(r"E = mc^2")
st.latex(r"\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}")
st.latex(r"\\sum_{i=1}^{n} x_i = x_1 + x_2 + \\cdots + x_n")
st.latex(r"\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}")''', language="python")
    
    with st.container(border=True):
        st.latex(r"E = mc^2")
        st.latex(r"\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}")
        st.latex(r"\sum_{i=1}^{n} x_i = x_1 + x_2 + \cdots + x_n")
        st.latex(r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}")
    
    # -------------------------------------------------------------------------
    # st.html()
    # -------------------------------------------------------------------------
    st.header("st.html()", divider="blue")
    
    st.code('st.html("<div style=\'padding: 10px; background: linear-gradient(90deg, #3b82f6, #8b5cf6); color: white; border-radius: 8px; text-align: center;\'><b>Custom HTML Content</b></div>")', language="python")
    
    with st.container(border=True):
        st.html("<div style='padding: 10px; background: linear-gradient(90deg, #3b82f6, #8b5cf6); color: white; border-radius: 8px; text-align: center;'><b>Custom HTML Content</b></div>")
    
    # -------------------------------------------------------------------------
    # st.json()
    # -------------------------------------------------------------------------
    st.header("st.json()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `body` (dict | list | str): JSON data
        - `expanded` (bool | int): Expand all (True), collapse all (False), or expand to depth (int)
        """)
    
    st.code('st.json({"key": "value"}, expanded=2)', language="python")
    
    with st.container(border=True):
        st.json({
            "user": {
                "name": "Alice",
                "email": "alice@example.com",
                "settings": {
                    "theme": "dark",
                    "notifications": True,
                    "language": "en"
                }
            },
            "permissions": ["read", "write", "admin"]
        }, expanded=2)
    
    # -------------------------------------------------------------------------
    # st.metric()
    # -------------------------------------------------------------------------
    st.header("st.metric()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `label` (str): Metric label
        - `value` (Any): Metric value
        - `delta` (Any): Delta value (shows +/- indicator)
        - `delta_color` (str): "normal" (green=up), "inverse" (red=up), "off" (no color)
        - `help` (str | None): Tooltip
        - `label_visibility` (str): "visible", "hidden", "collapsed"
        - `border` (bool): Show border around metric
        """)
    
    st.code('''col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Revenue", "$12,345", delta="+5.2%")
with col2:
    st.metric("Users", "1,234", delta="+120", help="Active users this month")
with col3:
    st.metric("Errors", 23, delta="-8%", delta_color="inverse")
with col4:
    st.metric("Uptime", "99.9%", delta="0%", delta_color="off", border=True)''', language="python")
    
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Revenue", "$12,345", delta="+5.2%")
        with col2:
            st.metric("Users", "1,234", delta="+120", help="Active users this month")
        with col3:
            st.metric("Errors", 23, delta="-8%", delta_color="inverse")
        with col4:
            st.metric("Uptime", "99.9%", delta="0%", delta_color="off", border=True)
    
    # -------------------------------------------------------------------------
    # st.badge()
    # -------------------------------------------------------------------------
    st.header("st.badge()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `label` (str): Badge text
        - `color` (str): "blue", "green", "red", "orange", "violet", "yellow", "gray"
        - `icon` (str | None): Optional emoji icon
        """)
    
    st.code('''cols = st.columns(7)
colors = ["blue", "green", "red", "orange", "violet", "yellow", "gray"]
for col, color in zip(cols, colors):
    with col:
        st.badge(color.title(), color=color)

st.badge("New Feature", color="green", icon="🆕")
st.badge("Deprecated", color="red", icon="⚠️")
st.badge("In Progress", color="orange", icon="🔄")''', language="python")
    
    with st.container(border=True):
        cols = st.columns(7)
        colors = ["blue", "green", "red", "orange", "violet", "yellow", "gray"]
        for col, color in zip(cols, colors):
            with col:
                st.badge(color.title(), color=color)
        
        st.badge("New Feature", color="green", icon="🆕")
        st.badge("Deprecated", color="red", icon="⚠️")
        st.badge("In Progress", color="orange", icon="🔄")
    
    # -------------------------------------------------------------------------
    # st.echo()
    # -------------------------------------------------------------------------
    st.header("st.echo()", divider="blue")
    
    st.code('''with st.echo():
    # This code is displayed AND executed
    result = 2 + 2
    st.write(f"2 + 2 = {result}")''', language="python")
    
    with st.container(border=True):
        with st.echo():
            # This code is displayed AND executed
            result = 2 + 2
            st.write(f"2 + 2 = {result}")

    # -------------------------------------------------------------------------
    # st.help()
    # -------------------------------------------------------------------------
    st.header("st.help()", divider="blue")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `obj` (Any): Python object to introspect

        **Behavior:**
        - Displays object name + type
        - Shows callable signature when available
        - Renders docstring content
        """)

    st.code('''st.help(st.slider)

class Demo:
    """Small object for st.help demo."""
    def run(self, x: int) -> int:
        return x * 2

st.help(Demo)''', language="python")

    with st.container(border=True):
        st.help(st.slider)
    
    # -------------------------------------------------------------------------
    # st.divider()
    # -------------------------------------------------------------------------
    st.header("st.divider()", divider="blue")
    
    st.code('st.divider()', language="python")
    
    with st.container(border=True):
        st.write("Content above")
        st.divider()
        st.write("Content below")


# =============================================================================
# 🎛️ INPUT WIDGETS
# =============================================================================
elif selected == "🎛️ Input Widgets":
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

    st.code('''st.page_link("/", label="Home", icon="🏠")
st.page_link("/charts", label="Charts page")
st.page_link("https://docs.streamlit.io", label="External docs")''', language="python")

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.page_link("/", label="Home", icon="🏠")
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


# =============================================================================
# 📊 DATA DISPLAY
# =============================================================================
elif selected == "📊 Data Display":
    st.title("📊 Data Display")
    st.caption("Components for displaying data")
    
    # Sample data
    sample_data = {
        "Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
        "Age": [25, 30, 35, 28, 32],
        "City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
        "Score": [85.5, 92.0, 78.5, 95.0, 88.5],
        "Active": [True, False, True, True, False],
        "Joined": ["2024-01-15", "2023-06-20", "2024-03-01", "2023-11-10", "2024-02-28"],
    }
    
    # -------------------------------------------------------------------------
    # st.dataframe()
    # -------------------------------------------------------------------------
    st.header("st.dataframe()", divider="blue")
    st.caption("New in Fastlit: `on_select` + `selection_mode` for interactive row selection.")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `data` (DataFrame | dict | list): Data to display
        - `height` (int | None): Height in pixels (auto-sizes up to 400px)
        - `use_container_width` (bool): Stretch to container width
        - `hide_index` (bool): Hide row index
        - `on_select` ("rerun" | Callable | None): Selection callback behavior
        - `selection_mode` ("single-row" | "multi-row"): Row selection mode
        - `key` (str | None): Unique key
        
        **Features:**
        - Virtualized rendering (handles millions of rows)
        - Column sorting (click headers)
        - Column resizing
        - Smooth scrolling

        **Returns:** Selection object with `.rows` when `on_select` is set, else `None`
        """)
    
    st.code('''sample_data = {
    "Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
    "Age": [25, 30, 35, 28, 32],
    "City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
    "Score": [85.5, 92.0, 78.5, 95.0, 88.5],
    "Active": [True, False, True, True, False],
}
st.dataframe(sample_data, height=400)

# With hidden index:
st.dataframe(sample_data, height=300, hide_index=True)

# With column_config and sticky column:
st.dataframe(
    sample_data,
    height=400,
    column_config={
        "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
        "Score": st.column_config.NumberColumn("Score", format="%.1f", resizable=True),
        "Active": st.column_config.CheckboxColumn("Active"),
    },
)''', language="python")
    
    with st.container(border=True):
        st.dataframe(sample_data, height=300)
        
        st.caption("With hidden index:")
        st.dataframe(sample_data, height=300, hide_index=True)
        
        st.caption("With column_config, sticky `Name` column and resize:")
        st.dataframe(
            sample_data,
            height=400,
            column_config={
                "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
                "Score": st.column_config.NumberColumn("Score", format="%.1f", resizable=True),
                "Active": st.column_config.CheckboxColumn("Active"),
            },
        )

    dataframe_params = inspect.signature(st.dataframe).parameters
    supports_df_selection = {"on_select", "selection_mode"}.issubset(dataframe_params.keys())

    if supports_df_selection:
        st.code('''selection_demo_data = {
    "Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
    "Age": [25, 30, 35, 28, 32],
    "City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
    "Score": [85.5, 92.0, 78.5, 95.0, 88.5],
    "Active": [True, False, True, True, False],
}

selection = st.dataframe(
    selection_demo_data,
    on_select="rerun",
    selection_mode="multi-row",
    height=180,
    key="df_selection_demo",
)

st.write(f"Selected rows: {selection.rows if selection is not None else []}")''', language="python")

        with st.container(border=True):
            selection_demo_data = {
                "Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
                "Age": [25, 30, 35, 28, 32],
                "City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
                "Score": [85.5, 92.0, 78.5, 95.0, 88.5],
                "Active": [True, False, True, True, False],
            }

            selection = st.dataframe(
                selection_demo_data,
                on_select="rerun",
                selection_mode="multi-row",
                height=300,
                key="df_selection_demo",
            )

            st.write(f"Selected rows: {selection.rows if selection is not None else []}")
    else:
        st.warning(
            "This runtime does not expose `st.dataframe(on_select=..., selection_mode=...)` yet. "
            "Using compatibility fallback."
        )
        st.code('''selection_demo_data = {
    "Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
    "Age": [25, 30, 35, 28, 32],
    "City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
    "Score": [85.5, 92.0, 78.5, 95.0, 88.5],
    "Active": [True, False, True, True, False],
}

st.dataframe(selection_demo_data, height=180, key="df_selection_demo")''', language="python")

        with st.container(border=True):
            selection_demo_data = {
                "Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
                "Age": [25, 30, 35, 28, 32],
                "City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
                "Score": [85.5, 92.0, 78.5, 95.0, 88.5],
                "Active": [True, False, True, True, False],
            }
            st.dataframe(selection_demo_data, height=300, key="df_selection_demo")
    
    # -------------------------------------------------------------------------
    # st.data_editor()
    # -------------------------------------------------------------------------
    st.header("st.data_editor()", divider="blue")
    st.caption("Editing with toolbar, persisted view state, column resize and sticky columns.")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `data`: Data to edit
        - `height`, `width`: Dimensions
        - `use_container_width` (bool): Full width
        - `hide_index` (bool): Hide index
        - `column_order` (list[str]): Column display order
        - `column_config` (dict): Column configurations
        - `num_rows` (str): "fixed" or "dynamic" (allow add/remove rows)
        - `disabled` (bool | list[str]): Disable all or specific columns
        - `row_height` (int | None): Fixed row height
        - `placeholder` (str | None): Empty state message
        - `toolbar` / `downloadable` / `persist_view`: UX controls
        - `on_change` (Callable): Callback when data changes
        
        **Returns:** Edited data
        """)
    
    st.code('''import pandas as pd

editor_demo_df = pd.DataFrame(sample_data)

edited = st.data_editor(
    editor_demo_df,
    height=250,
    num_rows="dynamic",
    persist_view=True,
    column_config={
        "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
        "Score": st.column_config.NumberColumn("Score", min_value=0, max_value=100, format="%.1f", resizable=True),
        "Active": st.column_config.CheckboxColumn("Active"),
        "Joined": st.column_config.DateColumn("Joined", format="YYYY-MM-DD", resizable=True),
    }
)

st.caption(f"Returned type: {type(edited).__name__}")
st.json(edited.to_dict(orient="records"))''', language="python")
    
    with st.container(border=True):
        import pandas as _pd_editor

        edited = st.data_editor(
            _pd_editor.DataFrame(sample_data),
            height=400,
            num_rows="dynamic",
            persist_view=True,
            column_config={
                "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
                "Score": st.column_config.NumberColumn("Score", min_value=0, max_value=100, format="%.1f", resizable=True),
                "Active": st.column_config.CheckboxColumn("Active"),
                "Joined": st.column_config.DateColumn("Joined", format="YYYY-MM-DD", resizable=True),
            }
        )
        
        st.caption(f"Returned type: `{type(edited).__name__}`")
        st.caption("Astuce: teste la recherche, les filtres, le resize des colonnes et la colonne `Name` sticky.")
        st.json(edited.to_dict(orient="records"))
    
    # -------------------------------------------------------------------------
    # Column Configuration
    # -------------------------------------------------------------------------
    st.header("Column Configuration", divider="blue")
    
    with st.expander("📖 All Column Types", expanded=True):
        st.markdown("""
        | Type | Usage |
        |------|-------|
        | `TextColumn` | Text with validation |
        | `NumberColumn` | Numeric with min/max/step |
        | `CheckboxColumn` | Boolean checkbox |
        | `SelectboxColumn` | Dropdown select |
        | `DateColumn` | Date picker |
        | `TimeColumn` | Time picker |
        | `DatetimeColumn` | Date + time |
        | `ProgressColumn` | Progress bar |
        | `LinkColumn` | Clickable URL |
        | `ImageColumn` | Image preview |
        | `LineChartColumn` | Sparkline chart |
        | `BarChartColumn` | Sparkbar chart |
        | `AreaChartColumn` | Spark area chart |
        | `ListColumn` | Array display |
        | `MultiselectColumn` | Editable chips |
        | `JSONColumn` | Expandable JSON cell |
        """)
    
    st.code('''st.column_config.NumberColumn("Price", min_value=0, max_value=1000, format="$%.2f", resizable=True)
st.column_config.ProgressColumn("Progress", min_value=0, max_value=100)
st.column_config.MultiselectColumn("Tags", options=["ops", "beta"])
st.column_config.JSONColumn("Payload")''', language="python")

    st.subheader("Live demo - all column_config types")
    st.caption("Text, numbers, booleans, select, chips, JSON, images, links and spark area columns.")

    import pandas as _pd_cc

    _cc_df = _pd_cc.DataFrame({
        "Name": ["Alice", "Bob", "Charlie", "Diana"],
        "Score": [87.5, 92.0, 78.3, 95.1],
        "Active": [True, False, True, True],
        "Role": ["admin", "user", "user", "viewer"],
        "Progress": [75, 45, 90, 60],
        "Tags": [["ops", "admin"], ["sales"], ["ml", "viz"], ["viewer", "beta"]],
        "Segments": [["ops", "admin"], ["sales"], ["ml", "viz"], ["viewer", "beta"]],
        "Payload": [
            {"tier": "gold", "quota": 12},
            {"tier": "silver", "quota": 8},
            {"tier": "bronze", "quota": 5},
            {"tier": "beta", "quota": 2},
        ],
        "Trend": [[3, 4, 5, 6], [4, 4, 5, 7], [2, 3, 3, 4], [1, 2, 4, 6]],
        "Avatar": [
            "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=120&q=80",
            "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&q=80",
            "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=120&q=80",
            "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=120&q=80",
        ],
        "Link": [
            "https://fastlit.dev",
            "https://streamlit.io",
            "https://github.com",
            "",
        ],
    })

    st.code('''result = st.data_editor(
    df,
    column_config={
        "Name":     st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
        "Score":    st.column_config.NumberColumn("Score /100", min_value=0, max_value=100, step=0.5, resizable=True),
        "Active":   st.column_config.CheckboxColumn("Active ?"),
        "Role":     st.column_config.SelectboxColumn("Role", options=["admin", "user", "viewer"]),
        "Progress": st.column_config.ProgressColumn("Progress %", min_value=0, max_value=100),
        "Tags":     st.column_config.ListColumn("Tags", resizable=True),
        "Segments": st.column_config.MultiselectColumn("Segments", options=["ops", "admin", "sales", "ml", "viz", "viewer", "beta"]),
        "Payload":  st.column_config.JSONColumn("Payload", width="large"),
        "Trend":    st.column_config.AreaChartColumn("Trend", y_min=0, y_max=8),
        "Avatar":   st.column_config.ImageColumn("Avatar"),
        "Link":     st.column_config.LinkColumn("URL", display_text="Open", resizable=True),
    },
    num_rows="dynamic",
)''', language="python")

    with st.container(border=True):
        _cc_result = st.data_editor(
            _cc_df,
            column_config={
                "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
                "Score": st.column_config.NumberColumn(
                    "Score /100", min_value=0, max_value=100, step=0.5, resizable=True
                ),
                "Active": st.column_config.CheckboxColumn("Active ?"),
                "Role": st.column_config.SelectboxColumn(
                    "Role", options=["admin", "user", "viewer"]
                ),
                "Progress": st.column_config.ProgressColumn(
                    "Progress %", min_value=0, max_value=100
                ),
                "Tags": st.column_config.ListColumn("Tags", resizable=True),
                "Segments": st.column_config.MultiselectColumn(
                    "Segments",
                    options=["ops", "admin", "sales", "ml", "viz", "viewer", "beta"],
                ),
                "Payload": st.column_config.JSONColumn("Payload", width="large"),
                "Trend": st.column_config.AreaChartColumn("Trend", y_min=0, y_max=8),
                "Avatar": st.column_config.ImageColumn("Avatar"),
                "Link": st.column_config.LinkColumn("URL", display_text="Open", resizable=True),
            },
            num_rows="dynamic",
            key="cc_demo_editor",
        )
        st.caption("Edited data:")
        st.caption("Resize `Name`, `Score`, `Tags` or `Link`, then try `Segments`, `Payload` and `Trend`.")
        if hasattr(_cc_result, "to_dict"):
            st.json(_cc_result.to_dict(orient="records"))
        else:
            st.json(_cc_result)
    
    # -------------------------------------------------------------------------
    # st.table()
    # -------------------------------------------------------------------------
    st.header("st.table()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `data` (DataFrame | dict | list): Data to display
        - `key` (str | None): Unique key
        
        **Note:** Static table - use for small data only. For large data, use st.dataframe().
        """)
    
    st.code('''small_data = {
    "Feature": ["Fast", "Compatible", "Modern"],
    "Status": ["✅", "✅", "✅"],
}
st.table(small_data)''', language="python")
    
    with st.container(border=True):
        import pandas as _pd_table

        small_data = _pd_table.DataFrame({
            "Feature": ["Fast", "Compatible", "Modern"],
            "Status": ["Ready", "Ready", "Ready"],
        })
        st.table(small_data)
    
    # -------------------------------------------------------------------------
    # st.metric()
    # -------------------------------------------------------------------------
    st.header("st.metric()", divider="blue")
    
    st.code('''cols = st.columns(4)

with cols[0]:
    st.metric("Revenue", 12345, delta=5.2, format="$,.0f", chart_data=[9, 10, 12, 11, 14, 16], chart_type="area", border=True)
with cols[1]:
    st.metric("Users", 1234, delta=120, chart_data=[980, 1010, 1100, 1130, 1200, 1234], chart_type="line")
with cols[2]:
    st.metric("Errors", 23, delta=-8, delta_color="inverse", delta_arrow="down", chart_data=[40, 33, 28, 26, 25, 23], chart_type="bar")
with cols[3]:
    st.metric("Status", "OK", delta="Stable", delta_arrow="off", border=True)''', language="python")
    
    with st.container(border=True):
        cols = st.columns(4)
        
        with cols[0]:
            st.metric(
                "Revenue",
                12345,
                delta=5.2,
                format="$,.0f",
                chart_data=[9, 10, 12, 11, 14, 16],
                chart_type="area",
                border=True,
            )
        with cols[1]:
            st.metric(
                "Users",
                1234,
                delta=120,
                chart_data=[980, 1010, 1100, 1130, 1200, 1234],
                chart_type="line",
            )
        with cols[2]:
            st.metric(
                "Errors",
                23,
                delta=-8,
                delta_color="inverse",
                delta_arrow="down",
                chart_data=[40, 33, 28, 26, 25, 23],
                chart_type="bar",
            )
        with cols[3]:
            st.metric("Status", "OK", delta="Stable", delta_arrow="off", border=True)
    
    # -------------------------------------------------------------------------
    # st.json()
    # -------------------------------------------------------------------------
    st.header("st.json()", divider="blue")
    
    st.code('''st.json({
    "app": "Fastlit",
    "version": "0.2.0",
    "config": {
        "debug": True,
        "port": 8501,
        "features": {
            "caching": True,
            "hot_reload": True,
            "copy_path": True
        }
    },
    "authors": ["Developer 1", "Developer 2"]
}, expanded=2)

# Search, global expand/collapse and copy path/value''', language="python")
    
    with st.container(border=True):
        st.json({
            "app": "Fastlit",
            "version": "0.2.0",
            "config": {
                "debug": True,
                "port": 8501,
                "features": {
                    "caching": True,
                    "hot_reload": True,
                    "copy_path": True
                }
            },
            "authors": ["Developer 1", "Developer 2"]
        }, expanded=2)


# =============================================================================
# 📈 CHARTS
# =============================================================================
elif selected == "📈 Charts":
    st.title("📈 Charts")
    st.caption("Data visualization components")
    
    # Sample data for charts
    chart_data = {
        "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "sales": [100, 120, 140, 130, 180, 200],
        "profit": [20, 25, 30, 22, 40, 45],
        "costs": [80, 95, 110, 108, 140, 155],
    }
    
    # -------------------------------------------------------------------------
    # st.line_chart()
    # -------------------------------------------------------------------------
    st.header("st.line_chart()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `data` (DataFrame | dict | list): Chart data
        - `x` (str | None): X-axis column (default: index)
        - `y` (str | list[str] | None): Y-axis column(s)
        - `color` (str | list[str] | None): Line color(s)
        - `width`, `height` (int | None): Dimensions
        - `use_container_width` (bool): Full width
        """)
    
    st.code('''chart_data = {
    "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "sales": [100, 120, 140, 130, 180, 200],
    "profit": [20, 25, 30, 22, 40, 45],
}
st.line_chart(chart_data, x="month", y=["sales", "profit"], height=300)''', language="python")
    
    with st.container(border=True):
        st.line_chart(chart_data, x="month", y=["sales", "profit"], height=300)
    
    # -------------------------------------------------------------------------
    # st.bar_chart()
    # -------------------------------------------------------------------------
    st.header("st.bar_chart()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:** Same as st.line_chart() plus:
        - `horizontal` (bool): Horizontal bars
        """)
    
    st.code('''# Vertical bars
st.bar_chart(chart_data, x="month", y="sales", height=250)

# Horizontal bars
st.bar_chart(chart_data, x="month", y="sales", height=250, horizontal=True)''', language="python")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.caption("Vertical bars")
            st.bar_chart(chart_data, x="month", y="sales", height=250)
        
        with col2:
            st.caption("Horizontal bars")
            st.bar_chart(chart_data, x="month", y="sales", height=250, horizontal=True)
    
    # -------------------------------------------------------------------------
    # st.area_chart()
    # -------------------------------------------------------------------------
    st.header("st.area_chart()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:** Same as st.line_chart() plus:
        - `stack` (bool): Stack areas
        """)
    
    st.code('''st.area_chart(chart_data, x="month", y=["sales", "costs"], height=300, stack=True)''', language="python")
    
    with st.container(border=True):
        st.area_chart(chart_data, x="month", y=["sales", "costs"], height=300, stack=True)
    
    # -------------------------------------------------------------------------
    # st.scatter_chart()
    # -------------------------------------------------------------------------
    st.header("st.scatter_chart()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `data`: Chart data
        - `x`, `y` (str): X and Y columns
        - `color` (str | None): Color column for encoding
        - `size` (str | None): Size column for point sizing
        """)
    
    st.code('''scatter_data = {
    "x": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    "y": [15, 25, 35, 20, 55, 45, 70, 85, 75, 95],
    "size": [10, 20, 15, 30, 25, 35, 40, 45, 50, 55],
}
st.scatter_chart(scatter_data, x="x", y="y", height=300)''', language="python")
    
    with st.container(border=True):
        scatter_data = {
            "x": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            "y": [15, 25, 35, 20, 55, 45, 70, 85, 75, 95],
            "size": [10, 20, 15, 30, 25, 35, 40, 45, 50, 55],
        }
        st.scatter_chart(scatter_data, x="x", y="y", height=300)
    
    # -------------------------------------------------------------------------
    # st.map()
    # -------------------------------------------------------------------------
    st.header("st.map()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `data` (DataFrame | list | None): Data with lat/lon columns
        - `latitude` (str | None): Latitude column name
        - `longitude` (str | None): Longitude column name
        - `color` (str | None): Marker color
        - `size` (str | None): Size column for markers
        - `zoom` (int | None): Initial zoom level
        - `height` (int | None): Map height
        - `use_container_width` (bool): Full width
        """)
    
    st.code('''map_data = [
    {"lat": 48.8566, "lon": 2.3522},   # Paris
    {"lat": 51.5074, "lon": -0.1278},  # London
    {"lat": 52.5200, "lon": 13.4050},  # Berlin
    {"lat": 40.4168, "lon": -3.7038},  # Madrid
    {"lat": 41.9028, "lon": 12.4964},  # Rome
]
st.map(map_data, zoom=4, height=400)''', language="python")
    
    with st.container(border=True):
        map_data = [
            {"lat": 48.8566, "lon": 2.3522},   # Paris
            {"lat": 51.5074, "lon": -0.1278},  # London
            {"lat": 52.5200, "lon": 13.4050},  # Berlin
            {"lat": 40.4168, "lon": -3.7038},  # Madrid
            {"lat": 41.9028, "lon": 12.4964},  # Rome
        ]
        st.map(map_data, zoom=4, height=400)
    
    # -------------------------------------------------------------------------
    # Advanced Charts (Plotly, Altair, etc.)
    # -------------------------------------------------------------------------
    st.header("Advanced Charts", divider="blue")
    st.caption("Integration with popular Python visualization libraries.")

    # -------------------------------------------------------------------------
    # st.plotly_chart()
    # -------------------------------------------------------------------------
    st.subheader("st.plotly_chart()")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `figure_or_data`: Plotly Figure or dict of traces
        - `use_container_width` (bool): Fill container width
        - `theme` (str | None): `"streamlit"` or `None`
        - `on_select` (callable | None): Callback with selected point indices
        - `key` (str | None): Stable widget key

        **Returns:** `list[int]` of selected indices when `on_select` is set, else `None`.
        """)

    st.code(
        "import plotly.graph_objects as go\n\n"
        "fig = go.Figure()\n"
        "fig.add_trace(go.Scatter(x=[1,2,3,4,5], y=[2,4,3,5,4],\n"
        "                         mode='lines+markers', name='Series A'))\n"
        "fig.add_trace(go.Bar(x=[1,2,3,4,5], y=[1,3,2,4,3], name='Series B'))\n"
        "fig.update_layout(title='Plotly Mixed Chart', height=350)\n"
        "st.plotly_chart(fig)\n\n"
        "# With cross-filtering (on_select):\n"
        "def on_sel(indices):\n"
        "    st.write('Selected:', indices)\n"
        "st.plotly_chart(fig, on_select=on_sel)",
        language="python",
    )

    with st.container(border=True):
        try:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[1, 2, 3, 4, 5],
                y=[2, 4, 3, 5, 4],
                mode="lines+markers",
                name="Series A",
                line=dict(color="#6366f1", width=2),
                marker=dict(size=8),
            ))
            fig.add_trace(go.Bar(
                x=[1, 2, 3, 4, 5],
                y=[1, 3, 2, 4, 3],
                name="Series B",
                marker_color="#22d3ee",
                opacity=0.7,
            ))
            fig.update_layout(
                title="Plotly Mixed Chart (Scatter + Bar)",
                height=350,
                legend=dict(orientation="h"),
            )
            st.plotly_chart(fig)
        except ImportError:
            st.warning("Install plotly to see this demo: `pip install plotly`")

    # -------------------------------------------------------------------------
    # st.altair_chart()
    # -------------------------------------------------------------------------
    st.subheader("st.altair_chart()")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `altair_chart`: An Altair Chart object
        - `use_container_width` (bool): Fill container width
        - `theme` (str | None): `"streamlit"` or `None`
        - `key` (str | None): Stable widget key
        """)

    st.code(
        "import altair as alt\n"
        "import pandas as pd\n\n"
        "df = pd.DataFrame({\n"
        "    'month': ['Jan','Feb','Mar','Apr','May','Jun'],\n"
        "    'sales': [120, 145, 132, 178, 165, 190],\n"
        "})\n\n"
        "chart = alt.Chart(df).mark_bar().encode(\n"
        "    x='month',\n"
        "    y='sales',\n"
        "    color=alt.value('#6366f1'),\n"
        ").properties(title='Monthly Sales', height=300)\n\n"
        "st.altair_chart(chart)",
        language="python",
    )

    with st.container(border=True):
        try:
            import altair as alt
            import pandas as pd
            df_alt = pd.DataFrame({
                "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "sales": [120, 145, 132, 178, 165, 190],
                "profit": [40, 55, 48, 72, 60, 85],
            })
            chart = alt.Chart(df_alt).mark_bar().encode(
                x=alt.X("month", sort=None),
                y="sales",
                color=alt.value("#6366f1"),
                tooltip=["month", "sales", "profit"],
            ).properties(title="Monthly Sales (Altair)", height=300)
            st.altair_chart(chart)
        except ImportError:
            st.warning("Install altair to see this demo: `pip install altair`")

    # -------------------------------------------------------------------------
    # st.vega_lite_chart()
    # -------------------------------------------------------------------------
    st.subheader("st.vega_lite_chart()")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `data`: Data (DataFrame, dict, list) — injected as `data.values` in the spec
        - `spec` (dict): Vega-Lite specification
        - `use_container_width` (bool): Fill container width
        - `theme` (str | None): `"streamlit"` or `None`
        - `key` (str | None): Stable widget key
        """)

    st.code(
        "data = [\n"
        "    {'x': 1, 'y': 5}, {'x': 2, 'y': 3},\n"
        "    {'x': 3, 'y': 8}, {'x': 4, 'y': 6},\n"
        "]\n"
        "spec = {\n"
        "    'mark': {'type': 'point', 'filled': True},\n"
        "    'encoding': {\n"
        "        'x': {'field': 'x', 'type': 'quantitative'},\n"
        "        'y': {'field': 'y', 'type': 'quantitative'},\n"
        "        'size': {'value': 100},\n"
        "    },\n"
        "    'height': 300,\n"
        "}\n"
        "st.vega_lite_chart(data, spec)",
        language="python",
    )

    with st.container(border=True):
        vl_data = [
            {"x": i, "y": (i * 13 % 17) + 2, "cat": "A" if i % 2 == 0 else "B"}
            for i in range(1, 13)
        ]
        vl_spec = {
            "mark": {"type": "point", "filled": True, "size": 80},
            "encoding": {
                "x": {"field": "x", "type": "quantitative", "title": "X value"},
                "y": {"field": "y", "type": "quantitative", "title": "Y value"},
                "color": {"field": "cat", "type": "nominal"},
                "tooltip": [
                    {"field": "x", "type": "quantitative"},
                    {"field": "y", "type": "quantitative"},
                    {"field": "cat", "type": "nominal"},
                ],
            },
            "height": 300,
            "title": "Vega-Lite Scatter (no extra dependencies)",
        }
        st.vega_lite_chart(vl_data, vl_spec)

    # -------------------------------------------------------------------------
    # st.pyplot()
    # -------------------------------------------------------------------------
    st.subheader("st.pyplot()")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `fig`: Matplotlib figure. If `None`, uses `plt.gcf()`
        - `clear_figure` (bool): Clear the figure after rendering (default `True`)
        - `use_container_width` (bool): Fill container width
        - `key` (str | None): Stable widget key

        Rendered server-side as PNG — no client dependency on Matplotlib.
        """)

    st.code(
        "import matplotlib.pyplot as plt\n"
        "import numpy as np\n\n"
        "fig, ax = plt.subplots(figsize=(8, 4))\n"
        "x = np.linspace(0, 2 * np.pi, 200)\n"
        "ax.plot(x, np.sin(x), label='sin(x)', color='#6366f1')\n"
        "ax.plot(x, np.cos(x), label='cos(x)', color='#22d3ee')\n"
        "ax.set_title('Matplotlib: sin & cos')\n"
        "ax.legend()\n"
        "st.pyplot(fig)",
        language="python",
    )

    with st.container(border=True):
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import numpy as np
            fig, ax = plt.subplots(figsize=(8, 4))
            x = np.linspace(0, 2 * np.pi, 200)
            ax.plot(x, np.sin(x), label="sin(x)", color="#6366f1", linewidth=2)
            ax.plot(x, np.cos(x), label="cos(x)", color="#22d3ee", linewidth=2)
            ax.fill_between(x, np.sin(x), alpha=0.1, color="#6366f1")
            ax.set_title("Matplotlib: sin & cos")
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
        except ImportError:
            st.warning("Install matplotlib to see this demo: `pip install matplotlib`")

    # -------------------------------------------------------------------------
    # st.bokeh_chart()
    # -------------------------------------------------------------------------
    st.subheader("st.bokeh_chart()")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `figure`: Bokeh figure object
        - `use_container_width` (bool): Fill container width
        - `key` (str | None): Stable widget key

        Bokeh renders client-side via BokehJS — interactive zoom/pan included.
        """)

    st.code(
        "from bokeh.plotting import figure\n\n"
        "p = figure(title='Bokeh Line Chart', height=300, width=600)\n"
        "p.line([1,2,3,4,5], [6,7,2,4,5],\n"
        "       line_width=2, color='#6366f1', legend_label='Data')\n"
        "p.circle([1,2,3,4,5], [6,7,2,4,5],\n"
        "         size=8, color='#22d3ee', fill_color='white')\n"
        "st.bokeh_chart(p)",
        language="python",
    )

    with st.container(border=True):
        try:
            from bokeh.plotting import figure as bokeh_figure
            p = bokeh_figure(title="Bokeh Line Chart", height=300, sizing_mode="stretch_width")
            x_vals = [1, 2, 3, 4, 5, 6]
            y_vals = [6, 7, 2, 4, 5, 8]
            p.line(x_vals, y_vals, line_width=2, color="#6366f1", legend_label="Series A")
            p.scatter(x_vals, y_vals, size=8, color="#22d3ee", fill_color="white", line_width=2)
            p.legend.location = "top_left"
            st.bokeh_chart(p)
        except ImportError:
            st.warning("Install bokeh to see this demo: `pip install bokeh`")

    # -------------------------------------------------------------------------
    # st.graphviz_chart()
    # -------------------------------------------------------------------------
    st.subheader("st.graphviz_chart()")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `figure_or_dot`: DOT language string or a `graphviz.Graph` / `graphviz.Digraph` object
        - `use_container_width` (bool): Fill container width
        - `key` (str | None): Stable widget key

        Rendered via `@hpcc-js/wasm` — no server-side Graphviz install needed.
        """)

    st.code(
        'st.graphviz_chart("""\n'
        "    digraph Pipeline {\n"
        "        rankdir=LR\n"
        '        node [shape=box style=filled fillcolor="#e0e7ff"]\n'
        "        Input -> Preprocess -> Model -> Postprocess -> Output\n"
        "        Preprocess -> Cache\n"
        "        Cache -> Model\n"
        "    }\n"
        '""")',
        language="python",
    )

    with st.container(border=True):
        st.graphviz_chart("""
            digraph Pipeline {
                rankdir=LR
                node [shape=box style=filled fillcolor="#e0e7ff" fontname="Arial"]
                edge [color="#6366f1"]
                Input -> Preprocess -> Model -> Postprocess -> Output
                Preprocess -> Cache [style=dashed]
                Cache -> Model [style=dashed label="hit"]
            }
        """)

    # -------------------------------------------------------------------------
    # st.pydeck_chart()
    # -------------------------------------------------------------------------
    st.subheader("st.pydeck_chart()")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `pydeck_obj`: A `pydeck.Deck` object
        - `use_container_width` (bool): Fill container width
        - `key` (str | None): Stable widget key

        Renders 3D maps and geospatial visualizations via deck.gl.
        """)

    st.code(
        "import pydeck as pdk\n\n"
        "layer = pdk.Layer(\n"
        "    'ScatterplotLayer',\n"
        "    data=[{'lat': 48.8566, 'lon': 2.3522, 'name': 'Paris'},\n"
        "          {'lat': 51.5074, 'lon': -0.1278, 'name': 'London'},\n"
        "          {'lat': 52.5200, 'lon': 13.4050, 'name': 'Berlin'}],\n"
        "    get_position='[lon, lat]',\n"
        "    get_radius=50000,\n"
        "    get_fill_color=[99, 102, 241, 180],\n"
        "    pickable=True,\n"
        ")\n"
        "deck = pdk.Deck(\n"
        "    layers=[layer],\n"
        "    initial_view_state=pdk.ViewState(latitude=50, longitude=6,\n"
        "                                      zoom=4, pitch=30),\n"
        "    tooltip={'text': '{name}'},\n"
        ")\n"
        "st.pydeck_chart(deck)",
        language="python",
    )

    with st.container(border=True):
        try:
            import pydeck as pdk
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=[
                    {"lat": 48.8566, "lon": 2.3522, "name": "Paris"},
                    {"lat": 51.5074, "lon": -0.1278, "name": "London"},
                    {"lat": 52.5200, "lon": 13.4050, "name": "Berlin"},
                    {"lat": 40.4168, "lon": -3.7038, "name": "Madrid"},
                    {"lat": 41.9028, "lon": 12.4964, "name": "Rome"},
                ],
                get_position="[lon, lat]",
                get_radius=50000,
                get_fill_color=[99, 102, 241, 180],
                pickable=True,
            )
            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=pdk.ViewState(
                    latitude=48, longitude=8, zoom=4, pitch=30
                ),
                tooltip={"text": "{name}"},
                map_style="light",
            )
            st.pydeck_chart(deck)
        except ImportError:
            st.warning("Install pydeck to see this demo: `pip install pydeck`")


# =============================================================================
# 🖼️ MEDIA
# =============================================================================
elif selected == "🖼️ Media":
    st.title("🖼️ Media Components")
    st.caption("Components for displaying media content")
    
    # -------------------------------------------------------------------------
    # st.image()
    # -------------------------------------------------------------------------
    st.header("st.image()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `image` (str | bytes | PIL.Image | np.ndarray): Image source
        - `caption` (str | None): Caption below image
        - `width` (int | None): Width in pixels
        - `use_container_width` (str | bool): "auto", "always", "never"
        - `clamp` (bool): Clamp pixel values
        - `channels` (str): "RGB" or "BGR"
        - `output_format` (str): "auto", "PNG", "JPEG"
        """)
    
    st.code('''st.image(
    "path/to/image.jpg",
    caption="Sample image with caption",
    width=400
)''', language="python")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(
                "https://images.unsplash.com/photo-1769968065332-77ff2c6cf199?q=80&w=688&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                caption="Sample image with caption",
                width=400
            )
        
        with col2:
            st.image(
                "https://images.unsplash.com/photo-1770034285769-4a5a3f410346?q=80&w=880&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
                caption="Another image",
                width=600
            )
    
    # -------------------------------------------------------------------------
    # st.audio()
    # -------------------------------------------------------------------------
    st.header("st.audio()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `data` (str | bytes | np.ndarray): Audio source
        - `format` (str): MIME type (default: "audio/wav")
        - `start_time` (int): Start time in seconds
        - `end_time` (int | None): End time in seconds
        - `sample_rate` (int | None): For numpy arrays
        - `loop` (bool): Loop playback
        - `autoplay` (bool): Auto-start playback
        """)
    
    st.code('''st.audio("path/to/audio.mp3")
st.audio(audio_bytes, format="audio/mp3", autoplay=True)''', language="python")
    
    with st.container(border=True):
        st.info("Provide an audio file URL or bytes to use st.audio()")
        st.audio("https://file-examples.com/storage/fe28eab7b0699747a9dded4/2017/11/file_example_MP3_700KB.mp3")
    
    # -------------------------------------------------------------------------
    # st.video()
    # -------------------------------------------------------------------------
    st.header("st.video()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `data` (str | bytes): Video source (URL or bytes)
        - `format` (str): MIME type (default: "video/mp4")
        - `start_time`, `end_time` (int): Playback range
        - `subtitles` (dict | None): Subtitle tracks {label: file}
        - `loop` (bool): Loop playback
        - `autoplay` (bool): Auto-start
        - `muted` (bool): Start muted
        """)
    
    st.code('''st.video("https://example.com/video.mp4", start_time=10)
st.video(video_bytes, subtitles={"English": "en.vtt"})''', language="python")
    
    with st.container(border=True):
        st.info("Provide a video file URL or bytes to use st.video()")
        st.video("https://www.pexels.com/download/video/855936/")

    # -------------------------------------------------------------------------
    # st.logo()
    # -------------------------------------------------------------------------
    st.header("st.logo()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `image`: Logo image source
        - `size` (str): "small", "medium", "large"
        - `link` (str | None): URL to link to
        - `icon_image`: Smaller icon version
        """)
    
    st.code('st.logo("logo.png", size="medium", link="https://example.com")', language="python")
    
    with st.container(border=True):
        st.caption("Logo is typically placed in the sidebar:")
        st.info("Use `st.sidebar.logo()` to add a logo to your sidebar")
    
    # -------------------------------------------------------------------------
    # st.pdf()
    # -------------------------------------------------------------------------
    st.header("st.pdf()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `data` (str | bytes): PDF source (URL or bytes)
        - `width` (int | None): Display width
        - `height` (int | None): Display height (default: 600)
        """)
    
    st.code('st.pdf("document.pdf", height=500)', language="python")
    
    with st.container(border=True):
        st.info("Provide a PDF file URL or bytes to use st.pdf()")
        st.pdf("https://arxiv.org/pdf/2106.14881.pdf", height=500)


# =============================================================================
# ⚡ STATUS & FEEDBACK
# =============================================================================
elif selected == "⚡ Status & Feedback":
    st.title("⚡ Status & Feedback")
    st.caption("Components for showing status and feedback")
    
    # -------------------------------------------------------------------------
    # Alert Messages
    # -------------------------------------------------------------------------
    st.header("Alert Messages", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Functions:**
        - `st.success(body, icon=None)` - Green success message
        - `st.info(body, icon=None)` - Blue info message
        - `st.warning(body, icon=None)` - Yellow warning message
        - `st.error(body, icon=None)` - Red error message
        
        **Parameters:**
        - `body` (str): Message text (supports Markdown)
        - `icon` (str | None): Custom emoji icon
        """)
    
    st.code('''st.success("Operation completed successfully!")
st.info("Here's some helpful information.")
st.warning("Warning: This action cannot be undone.")
st.error("Error: Something went wrong.")

# With custom icons:
st.success("Saved!", icon="💾")
st.info("Tip: Use keyboard shortcuts", icon="💡")''', language="python")
    
    with st.container(border=True):
        st.success("Operation completed successfully!")
        st.info("Here's some helpful information.")
        st.warning("Warning: This action cannot be undone.")
        st.error("Error: Something went wrong.")
        
        st.divider()
        st.caption("With custom icons:")
        st.success("Saved!", icon="💾")
        st.info("Tip: Use keyboard shortcuts", icon="💡")
    
    # -------------------------------------------------------------------------
    # st.exception()
    # -------------------------------------------------------------------------
    st.header("st.exception()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `exception` (BaseException | None): Exception to display, None for current exception
        
        Displays exception with full traceback.
        """)
    
    st.code('''try:
    result = 1 / 0
except Exception as e:
    st.exception(e)''', language="python")
    
    with st.container(border=True):
        try:
            result = 1 / 0
        except Exception as e:
            st.exception(e)
    
    # -------------------------------------------------------------------------
    # st.progress()
    # -------------------------------------------------------------------------
    st.header("st.progress()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `value` (float | int): Progress 0-100 or 0.0-1.0
        - `text` (str | None): Text above progress bar
        """)
    
    st.code('''st.progress(25, text="25% - Getting started")
st.progress(50, text="50% - Halfway there!")
st.progress(75, text="75% - Almost done")
st.progress(100, text="100% - Complete!")''', language="python")
    
    with st.container(border=True):
        st.progress(25, text="25% - Getting started")
        st.progress(50, text="50% - Halfway there!")
        st.progress(75, text="75% - Almost done")
        st.progress(100, text="100% - Complete!")
    
    # -------------------------------------------------------------------------
    # st.spinner()
    # -------------------------------------------------------------------------
    st.header("st.spinner()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Usage:** Context manager that shows a spinner while code executes.

        **New behavior (runtime):**
        - Spinner is shown immediately while the block is running.
        - Spinner is removed automatically when the block exits.
        - Works for full reruns and fragment reruns.
        
        ```python
        with st.spinner("Loading..."):
            time.sleep(2)
        ```
        """)
    
    st.code('''if st.button("Start spinner demo"):
    with st.spinner("Processing..."):
        time.sleep(1)
    st.success("Done!")''', language="python")
    
    with st.container(border=True):
        if st.button("Start spinner demo"):
            with st.spinner("Processing..."):
                time.sleep(1)
            st.success("Done!")
        st.caption("Spinner should be visible during execution.")
    
    # -------------------------------------------------------------------------
    # st.status()
    # -------------------------------------------------------------------------
    st.header("st.status()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `label` (str): Status label
        - `expanded` (bool): Initially expanded
        - `state` (str): "running", "complete", "error"
        
        **Methods:**
        - `.update(label=None, state=None, expanded=None)`: Update status
        """)
    
    st.code('''if st.button("Run status demo"):
    with st.status("Downloading data...", expanded=True) as status:
        st.write("Connecting to server...")
        time.sleep(0.5)
        st.write("Fetching data...")
        time.sleep(0.5)
        st.write("Processing...")
        time.sleep(0.5)
        status.update(label="Download complete!", state="complete")''', language="python")
    
    with st.container(border=True):
        if st.button("Run status demo"):
            with st.status("Downloading data...", expanded=True) as status:
                st.write("Connecting to server...")
                time.sleep(0.5)
                st.write("Fetching data...")
                time.sleep(0.5)
                st.write("Processing...")
                time.sleep(0.5)
                status.update(label="Download complete!", state="complete")
    
    # -------------------------------------------------------------------------
    # st.toast()
    # -------------------------------------------------------------------------
    st.header("st.toast()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `body` (str): Toast message
        - `icon` (str | None): Icon emoji
        
        Shows a temporary notification in the corner.
        """)
    
    st.code('''if st.button("Success toast"):
    st.toast("Success!", icon="✅")

if st.button("Info toast"):
    st.toast("Just so you know...", icon="ℹ️")

if st.button("Warning toast"):
    st.toast("Watch out!", icon="⚠️")''', language="python")
    
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Success toast"):
                st.toast("Success!", icon="✅")
        
        with col2:
            if st.button("Info toast"):
                st.toast("Just so you know...", icon="ℹ️")
        
        with col3:
            if st.button("Warning toast"):
                st.toast("Watch out!", icon="⚠️")
    
    # -------------------------------------------------------------------------
    # st.balloons() & st.snow()
    # -------------------------------------------------------------------------
    st.header("Celebrations", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Functions:**
        - `st.balloons()` - Show celebratory balloons
        - `st.snow()` - Show snowfall animation
        
        No parameters. Single-use animation.
        """)
    
    st.code('''if st.button("🎈 Show Balloons"):
    st.balloons()

if st.button("❄️ Show Snow"):
    st.snow()''', language="python")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎈 Show Balloons"):
                st.balloons()
        
        with col2:
            if st.button("❄️ Show Snow"):
                st.snow()


# =============================================================================
# 📐 LAYOUT
# =============================================================================
elif selected == "📐 Layout":
    st.title("📐 Layout Components")
    st.caption("Components for organizing content")
    
    # -------------------------------------------------------------------------
    # st.columns()
    # -------------------------------------------------------------------------
    st.header("st.columns()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `spec` (int | list): Number of equal columns or list of widths
        - `gap` (str): "small", "medium", "large"
        - `vertical_alignment` (str): "top", "center", "bottom"
        - `border` (bool): Show border around columns
        
        **Returns:** list[Column]
        """)
    
    st.code('''# Equal columns
col1, col2, col3 = st.columns(3)
with col1:
    st.info("Column 1")
with col2:
    st.success("Column 2")
with col3:
    st.warning("Column 3")

# Custom widths (2:1 ratio)
left, right = st.columns([2, 1])
with left:
    st.info("Wide column (2)")
with right:
    st.success("Narrow (1)")

# With gap options
a, b, c = st.columns(3, gap="large")
with a:
    st.metric("A", 100)
with b:
    st.metric("B", 200)
with c:
    st.metric("C", 300)''', language="python")
    
    with st.container(border=True):
        st.caption("Equal columns:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("Column 1")
        with col2:
            st.success("Column 2")
        with col3:
            st.warning("Column 3")
        
        st.caption("Custom widths (2:1 ratio):")
        left, right = st.columns([2, 1])
        with left:
            st.info("Wide column (2)")
        with right:
            st.success("Narrow (1)")
        
        st.caption("With gap options:")
        a, b, c = st.columns(3, gap="large")
        with a:
            st.metric("A", 100)
        with b:
            st.metric("B", 200)
        with c:
            st.metric("C", 300)
    
    # -------------------------------------------------------------------------
    # st.tabs()
    # -------------------------------------------------------------------------
    st.header("st.tabs()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `tab_labels` (Sequence[str]): Tab labels
        - `default` (str | None): Default selected tab
        
        **Returns:** list[Tab]
        """)
    
    st.code('''tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Data", "⚙️ Settings"])

with tab1:
    st.write("This is the overview tab.")
    st.metric("Total", 1234)

with tab2:
    st.write("This is the data tab.")
    st.dataframe({"A": [1, 2, 3], "B": [4, 5, 6]})

with tab3:
    st.write("This is the settings tab.")
    st.checkbox("Enable feature")''', language="python")
    
    with st.container(border=True):
        tab1, tab2, tab3 = st.tabs(["📊 Overview", "📋 Data", "⚙️ Settings"])
        
        with tab1:
            st.write("This is the overview tab.")
            st.metric("Total", 1234)
        
        with tab2:
            st.write("This is the data tab.")
            st.dataframe({"A": [1, 2, 3], "B": [4, 5, 6]})
        
        with tab3:
            st.write("This is the settings tab.")
            st.checkbox("Enable feature")
    
    # -------------------------------------------------------------------------
    # st.expander()
    # -------------------------------------------------------------------------
    st.header("st.expander()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `label` (str): Expander label
        - `expanded` (bool): Initially expanded
        - `icon` (str | None): Icon
        
        **Returns:** Expander context manager
        """)
    
    st.code('''with st.expander("Click to see more details"):
    st.write("This content is hidden by default.")
    st.code("print('Hello!')", language="python")

with st.expander("Already expanded", expanded=True):
    st.write("This starts open.")''', language="python")
    
    with st.container(border=True):
        with st.expander("Click to see more details"):
            st.write("This content is hidden by default.")
            st.code("print('Hello!')", language="python")
        
        with st.expander("Already expanded", expanded=True):
            st.write("This starts open.")
    
    # -------------------------------------------------------------------------
    # st.container()
    # -------------------------------------------------------------------------
    st.header("st.container()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `border` (bool | None): Show border
        - `height` (int | str | None): Container height
        
        **Returns:** Container context manager
        """)
    
    st.code('''with st.container(border=True):
    st.write("Content in a bordered container")
    st.button("Button inside")

with st.container(border=True, height=100):
    st.write("Fixed height container (100px)")
    st.write("With scrolling if needed...")''', language="python")
    
    with st.container(border=True):
        with st.container(border=True):
            st.write("Content in a bordered container")
            st.button("Button inside")
        
        with st.container(border=True, height=100):
            st.write("Fixed height container (100px)")
            st.write("With scrolling if needed...")
    
    # -------------------------------------------------------------------------
    # st.empty()
    # -------------------------------------------------------------------------
    st.header("st.empty()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Usage:** Create a single-element placeholder that can be updated or cleared.
        
        **Methods:**
        - `.write()`, `.markdown()`, etc.: Update content
        - `.empty()`: Clear content
        """)
    
    st.code('''placeholder = st.empty()

if st.button("Show info"):
    placeholder.info("This is info")
if st.button("Show success"):
    placeholder.success("This is success")
if st.button("Clear"):
    placeholder.empty()''', language="python")
    
    with st.container(border=True):
        placeholder = st.empty()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Show info"):
                placeholder.info("This is info")
        with col2:
            if st.button("Show success"):
                placeholder.success("This is success")
        with col3:
            if st.button("Clear"):
                placeholder.empty()
    
    # -------------------------------------------------------------------------
    # st.form()
    # -------------------------------------------------------------------------
    st.header("st.form()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `key` (str): Unique form key
        - `clear_on_submit` (bool): Clear values after submit
        - `enter_to_submit` (bool): Submit on Enter key
        - `border` (bool): Show border
        
        Forms batch widget interactions until submitted.
        """)
    
    st.code('''with st.form("demo_form", clear_on_submit=True):
    name = st.text_input("Name", placeholder="Your name...")
    email = st.text_input("Email", placeholder="your@email.com")
    age = st.slider("Age", 18, 100, 25)
    newsletter = st.checkbox("Subscribe to newsletter")
    submitted = st.form_submit_button("Submit", type="primary")

if submitted:
    st.success(f"Form submitted! Name: {name}, Email: {email}, Age: {age}")''', language="python")
    
    with st.container(border=True):
        with st.form("demo_form", clear_on_submit=True):
            name = st.text_input("Name", placeholder="Your name...")
            email = st.text_input("Email", placeholder="your@email.com")
            age = st.slider("Age", 18, 100, 25)
            newsletter = st.checkbox("Subscribe to newsletter")
            submitted = st.form_submit_button("Submit", type="primary")
        
        if submitted:
            st.success(f"Form submitted! Name: {name}, Email: {email}, Age: {age}")
    
    # -------------------------------------------------------------------------
    # st.popover()
    # -------------------------------------------------------------------------
    st.header("st.popover()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `label` (str): Button label
        - `type` (str): Button type
        - `help` (str | None): Tooltip
        - `disabled` (bool): Disable
        - `use_container_width` (bool): Full width
        """)
    
    st.code('''with st.popover("⚙️ Settings"):
    st.write("Configure options:")
    st.toggle("Dark mode")
    st.slider("Volume", 0, 100, 50)
    st.selectbox("Language", ["English", "French", "German"])''', language="python")
    
    with st.container(border=True):
        with st.popover("⚙️ Settings"):
            st.write("Configure options:")
            st.toggle("Dark mode")
            st.slider("Volume", 0, 100, 50)
            st.selectbox("Language", ["English", "French", "German"])
    
    # -------------------------------------------------------------------------
    # st.dialog()
    # -------------------------------------------------------------------------
    st.header("st.dialog()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Usage:** Decorator to create modal dialogs.
        
        ```python
        @st.dialog("Title", width="small")
        def my_dialog():
            st.write("Content")
            if st.button("Close"):
                st.rerun()
        ```
        
        **Parameters:**
        - `title` (str): Dialog title
        - `width` (str): "small", "medium", "large"
        """)
    
    st.code('''@st.dialog("Confirm Delete")
def confirm_dialog():
    st.write("Are you sure?")
    if st.button("Yes"):
        st.session_state.deleted = True
        st.rerun()

if st.button("Delete"):
    confirm_dialog()''', language="python")
    
    with st.container(border=True):
        st.info("Dialogs are created using the @st.dialog decorator")

    # -------------------------------------------------------------------------
    # st.Page()
    # -------------------------------------------------------------------------
    st.header("st.Page()", divider="blue")
    has_page_api = hasattr(st, "Page")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Purpose:** Define page metadata for `st.navigation(...)`.

        **Parameters:**
        - `path` (str): Target script path
        - `title` (str | None): Display title
        - `icon` (str | None): Icon text/emoji
        - `url_path` (str | None): URL slug
        - `default` (bool): Default page
        """)

    st.code('''page_defs = [
    st.Page(__file__, title="Overview", icon="H", url_path="overview", default=True),
    st.Page(__file__, title="Data", icon="D", url_path="data"),
    st.Page(__file__, title="Settings", icon="S", url_path="settings"),
]

selected_page = st.navigation(page_defs, key="layout_page_api_demo")
st.write(f"Selected: title={selected_page.title}, url_path={selected_page.url_path}")''', language="python")

    with st.container(border=True):
        if has_page_api:
            page_defs = [
                st.Page(__file__, title="Overview", icon="H", url_path="overview", default=True),
                st.Page(__file__, title="Data", icon="D", url_path="data"),
                st.Page(__file__, title="Settings", icon="S", url_path="settings"),
            ]

            selected_page = st.navigation(page_defs, key="layout_page_api_demo")
            st.write(f"Selected: title={selected_page.title}, url_path={selected_page.url_path}")
        else:
            st.warning(
                "This runtime does not expose `st.Page` yet. "
                "Using compatibility fallback with string navigation."
            )
            selected_page = st.navigation(["Overview", "Data", "Settings"], key="layout_page_api_demo")
            st.write(f"Selected: {selected_page}")
    
    # -------------------------------------------------------------------------
    # st.navigation()
    # -------------------------------------------------------------------------
    st.header("st.navigation()", divider="blue")
    st.caption("Supports both `Sequence[str]` and `Sequence[st.Page]`.")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `pages` (Sequence[str | st.Page]): Page names or page definitions
        
        **Returns:** `str` in string mode, `st.Page` in Page mode
        
        Typically used in sidebar for multi-page navigation.
        """)
    
    st.markdown("Returns `str` in string mode and `st.Page` in Page mode.")

    st.code('''current = st.navigation(["Home", "Data", "Settings"], key="nav_string_mode")
st.write(f"Current page: {current}")''', language="python")
    
    with st.container(border=True):
        current = st.navigation(["Home", "Data", "Settings"], key="nav_string_mode")
        st.write(f"Current page: {current}")

    # -------------------------------------------------------------------------
    # st.switch_page()
    # -------------------------------------------------------------------------
    st.header("st.switch_page()", divider="blue")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Programmatically switch to another page.

        **Parameters:**
        - `page` (str | st.Page): Target page slug/name or `st.Page` object

        **Behavior:**
        - Raises an internal navigation exception
        - Stops current execution and reruns on target page
        """)

    st.code('''if st.button("Go to Data page"):
    st.switch_page("data")

# Or with Page objects:
# st.switch_page(my_page_def)''', language="python")

    with st.container(border=True):
        st.info(
            "Real page switch is optional in this demo to avoid accidental navigation."
        )
        enable_switch = st.toggle(
            "Enable real st.switch_page() call",
            value=False,
            key="switch_page_enable",
        )
        target_slug = st.selectbox(
            "Target slug",
            options=["home", "new-in-fastlit", "charts", "state-control"],
            key="switch_page_target",
        )
        if enable_switch and st.button("Switch now", key="switch_page_now"):
            st.switch_page(target_slug)
    
    # -------------------------------------------------------------------------
    # st.divider()
    # -------------------------------------------------------------------------
    st.header("st.divider()", divider="blue")
    
    st.code('st.divider()', language="python")
    
    with st.container(border=True):
        st.write("Content above")
        st.divider()
        st.write("Content below")


# =============================================================================
# 💬 CHAT COMPONENTS
# =============================================================================
elif selected == "💬 Chat Components":
    st.title("💬 Chat Components")
    st.caption("Components for building chat interfaces")
    
    # -------------------------------------------------------------------------
    # st.chat_message()
    # -------------------------------------------------------------------------
    st.header("st.chat_message()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `name` (str): Message role - "user", "assistant", "ai", "human", or custom
        - `avatar` (str | None): Avatar emoji, URL, or None for default
        
        **Returns:** Context manager for message content
        """)
    
    st.code('''with st.chat_message("user"):
    st.write("Hello! Can you help me with Python?")

with st.chat_message("assistant", avatar="🤖"):
    st.write("Of course! What would you like to know about Python?")''', language="python")
    
    with st.container(border=True):
        with st.chat_message("user"):
            st.write("Hello! Can you help me with Python?")
        
        with st.chat_message("assistant", avatar="🤖"):
            st.write("Of course! What would you like to know about Python?")
        
        with st.chat_message("user"):
            st.write("How do I read a CSV file?")
        
        with st.chat_message("assistant", avatar="🤖"):
            st.write("Here's how to read a CSV file:")
            st.code('''import pandas as pd
df = pd.read_csv("data.csv")
print(df.head())''', language="python")
    
    # -------------------------------------------------------------------------
    # st.chat_input()
    # -------------------------------------------------------------------------
    st.header("st.chat_input()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Parameters:**
        - `placeholder` (str): Placeholder text
        - `max_chars` (int | None): Maximum characters
        - `disabled` (bool): Disable input
        - `on_submit` (Callable): Callback on submit
        
        **Returns:** str | None (one-shot, not persisted in session_state)
        
        **Note:** Chat input is pinned to the bottom of the page.
        """)
    
    st.code('''if prompt := st.chat_input("Ask me anything..."):
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        st.write(f"You said: {prompt}")''', language="python")
    
    with st.container(border=True):
        st.info("""
        `st.chat_input()` is pinned to the bottom of the page.
        
        Try it! Type a message in the input at the bottom.
        """)
    
    # Demo chat functionality
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hi! I'm a demo chatbot. Ask me anything!"}
        ]
    
    # Display chat history
    st.header("Live Chat Demo", divider="blue")
    
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Chat input (will be at bottom of page)
    if prompt := st.chat_input("Type a message..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Generate response
        response = f"You said: '{prompt}'. This is a demo response!"
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
        st.rerun()


# =============================================================================
# 🔧 STATE & CONTROL
# =============================================================================
elif selected == "🔧 State & Control":
    st.title("🔧 State & Control")
    st.caption("State management and control flow")
    
    # -------------------------------------------------------------------------
    # st.session_state
    # -------------------------------------------------------------------------
    st.header("st.session_state", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Session-scoped state dictionary with attribute access.
        
        **Usage:**
        ```python
        # Initialize
        if "counter" not in st.session_state:
            st.session_state.counter = 0
        
        # Read
        value = st.session_state.counter
        value = st.session_state["counter"]
        
        # Write
        st.session_state.counter = 10
        st.session_state["counter"] = 10
        
        # Delete
        del st.session_state.counter
        
        # Clear all
        st.session_state.clear()
        
        # Dict methods
        st.session_state.get("key", default)
        st.session_state.keys()
        st.session_state.values()
        st.session_state.items()
        ```
        """)
    
    with st.container(border=True):
        if "demo_counter" not in st.session_state:
            st.session_state.demo_counter = 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("➖ Decrement"):
                st.session_state.demo_counter -= 1
        
        with col2:
            if st.button("➕ Increment"):
                st.session_state.demo_counter += 1
        
        with col3:
            if st.button("🔄 Reset"):
                st.session_state.demo_counter = 0
        
        with col4:
            st.metric("Counter", st.session_state.demo_counter)
        
        st.caption("Session state persists across reruns but not page refreshes.")
    
    # -------------------------------------------------------------------------
    # st.query_params
    # -------------------------------------------------------------------------
    st.header("st.query_params", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Access URL query parameters.
        
        **Usage:**
        ```python
        # Read
        page = st.query_params.get("page", "home")
        page = st.query_params["page"]
        
        # Write
        st.query_params["page"] = "settings"
        
        # All values for a key
        tags = st.query_params.get_all("tag")
        
        # Convert to dict
        params = st.query_params.to_dict()
        
        # Clear
        st.query_params.clear()
        ```
        """)
    

    st.code('''# Read
page = st.query_params.get("page", "home")
page = st.query_params["page"]

# Write
st.query_params["page"] = "settings"

# All values for a key
tags = st.query_params.get_all("tag")

# Convert to dict
params = st.query_params.to_dict()

# Clear
st.query_params.clear()''', language="python")

    with st.container(border=True):
        st.write("Current query params:")
        st.json(st.query_params.to_dict())
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Set ?demo=true"):
                st.query_params["demo"] = "true"
                st.rerun()
        with col2:
            if st.button("Clear params"):
                st.query_params.clear()
                st.rerun()
    
    # -------------------------------------------------------------------------
    # st.secrets
    # -------------------------------------------------------------------------
    st.header("st.secrets", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Access secrets from `secrets.toml` or `.streamlit/secrets.toml`.

        **New behavior:**
        - Secrets cache is reloaded automatically when the secrets file changes.
        - You can still use both dict and attribute access styles.
        
        **File format:**
        ```toml
        [database]
        host = "localhost"
        password = "secret123"
        
        [api]
        key = "sk-..."
        ```
        
        **Usage:**
        ```python
        host = st.secrets["database"]["host"]
        host = st.secrets.database.host
        ```
        """)
    

    st.code('''# secrets.toml
[database]
host = "localhost"
password = "secret123"

[api]
key = "sk-..."

# app.py
host = st.secrets["database"]["host"]
host = st.secrets.database.host''', language="python")

    with st.container(border=True):
        st.info("Create a `secrets.toml` file to use `st.secrets`")
    
    # -------------------------------------------------------------------------
    # st.context
    # -------------------------------------------------------------------------
    st.header("st.context", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Access request context information.
        
        **Properties:**
        - `st.context.headers` - dict: HTTP headers
        - `st.context.cookies` - dict: Cookies
        - `st.context.ip_address` - str: Client IP
        - `st.context.locale` - str: Locale from Accept-Language
        - `st.context.timezone` - str: Timezone hint
        """)
    
    with st.container(border=True):
        st.write("Request context:")
        st.json({
            "headers": dict(st.context.headers),
            "cookies": dict(st.context.cookies),
        })

    # -------------------------------------------------------------------------
    # st.user / st.require_login() / st.logout()
    # -------------------------------------------------------------------------
    st.header("st.user / st.require_login() / st.logout()", divider="blue")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Authentication helpers and current user proxy.

        **APIs:**
        - `st.user`: claims proxy (`is_logged_in`, `name`, `email`, custom claims)
        - `st.require_login()`: redirect to login when not authenticated
        - `st.logout()`: clear auth session and redirect to logout route
        """)

    st.code('''# Protect a page
st.require_login()
st.write("Hello", st.user.name, st.user.email)

if st.button("Sign out"):
    st.logout()''', language="python")

    with st.container(border=True):
        st.write(f"Authenticated: `{st.user.is_logged_in}`")
        st.json(
            {
                "name": st.user.name,
                "email": st.user.email,
                "sub": st.user.sub,
            },
            expanded=True,
        )
        if st.user.is_logged_in:
            if st.button("Logout now", key="auth_logout_now"):
                st.logout()
        else:
            st.info(
                "No authenticated user in this session. Configure [auth] in secrets.toml "
                "to enable login."
            )

    # -------------------------------------------------------------------------
    # st.connection() / st.connections
    # -------------------------------------------------------------------------
    st.header("st.connection() / st.connections", divider="blue")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Reusable backend connections with optional TTL-based recreation.

        **APIs:**
        - `st.connection(name, type=..., ttl=..., **kwargs)`
        - `st.connections`: module with built-ins (e.g., `BaseConnection`, `SQLConnection`)
        """)

    st.code('''conn = st.connection(
    "demo_db",
    type="sql",
    url="sqlite:///demo.db",
    ttl=60,
)
df = conn.query("SELECT 1 AS ok", ttl=0)
st.dataframe(df)''', language="python")

    with st.container(border=True):
        visible_symbols = [n for n in dir(st.connections) if not n.startswith("_")]
        st.write("`st.connections` public symbols:", visible_symbols)

        if st.button("Run SQL smoke query", key="connection_sql_smoke"):
            try:
                conn = st.connection(
                    "demo_sqlite_conn",
                    type="sql",
                    url="sqlite:///fastlit_demo.db",
                    ttl=30,
                )
                df = conn.query("SELECT 1 AS ok", ttl=0)
                st.dataframe(df, height=120)
                st.success("Connection demo OK.")
            except Exception as exc:
                st.warning(f"Connection demo unavailable in this environment: {exc}")
    
    # -------------------------------------------------------------------------
    # st.rerun()
    # -------------------------------------------------------------------------
    st.header("st.rerun()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Stop execution and immediately rerun the script.
        
        **Usage:**
        ```python
        st.rerun()  # Raises RerunException
        st.rerun(scope="fragment")  # Inside @st.fragment only
        ```
        
        Useful for refreshing the UI after state changes.
        """)
    
    with st.container(border=True):
        st.caption("Click to rerun the app:")
        st.caption("`scope=\"fragment\"` is supported inside `@st.fragment`.")
        if st.button("🔄 Rerun App"):
            st.rerun()
    
    st.code('''if st.button("Rerun full app"):
    st.rerun()

@st.fragment
def _fragment_rerun_demo():
    if "fragment_scope_count" not in st.session_state:
        st.session_state.fragment_scope_count = 0

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("+1", key="frag_scope_inc", use_container_width=True):
            st.session_state.fragment_scope_count += 1
    with col2:
        if st.button("Reset fragment", key="frag_scope_reset", use_container_width=True):
            st.session_state.fragment_scope_count = 0
            st.rerun(scope="fragment")
    with col3:
        st.metric("Fragment count", st.session_state.fragment_scope_count)

_fragment_rerun_demo()''', language="python")

    with st.container(border=True):
        if st.button("Rerun full app"):
            st.rerun()

        @st.fragment
        def _fragment_rerun_demo():
            if "fragment_scope_count" not in st.session_state:
                st.session_state.fragment_scope_count = 0

            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("+1", key="frag_scope_inc", use_container_width=True):
                    st.session_state.fragment_scope_count += 1
            with col2:
                if st.button("Reset fragment", key="frag_scope_reset", use_container_width=True):
                    st.session_state.fragment_scope_count = 0
                    st.rerun(scope="fragment")
            with col3:
                st.metric("Fragment count", st.session_state.fragment_scope_count)

        _fragment_rerun_demo()

    # -------------------------------------------------------------------------
    # st.stop()
    # -------------------------------------------------------------------------
    st.header("st.stop()", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Stop script execution. Elements below won't render.
        
        **Usage:**
        ```python
        if not authenticated:
            st.error("Please login")
            st.stop()
        
        # This won't run if not authenticated
        st.write("Secret content")
        ```
        """)
    

    st.code('''if not authenticated:
    st.error("Please login")
    st.stop()

# This runs only when authenticated
st.write("Secret content")''', language="python")

    with st.container(border=True):
        show_stop = st.checkbox("Enable st.stop() demo")
        
        if show_stop:
            st.warning("Script will stop here!")
            st.stop()
            st.error("This will never be shown")
        else:
            st.success("Content continues because stop is disabled")
    

    # -------------------------------------------------------------------------
    # Caching
    # -------------------------------------------------------------------------
    st.header("Caching", divider="blue")
    
    with st.expander("📖 @st.cache_data", expanded=True):
        st.markdown("""
        Cache function results with automatic invalidation.
        
        ```python
        @st.cache_data(ttl=300, max_entries=1000, copy=False)
        def load_data(path: str) -> pd.DataFrame:
            return pd.read_csv(path)
        ```
        
        **Parameters:**
        - `ttl` (int | None): Time-to-live in seconds
        - `max_entries` (int): Maximum cache entries (LRU)
        - `copy` (bool): Return deepcopy by default. Use `copy=False` for immutable results.
        
        **Clear cache:**
        ```python
        load_data.clear()           # Clear this function's cache
        st.cache_data.clear()       # Clear all cache_data caches
        ```
        """)
    
    with st.expander("📖 @st.cache_resource", expanded=True):
        st.markdown("""
        Cache resources (DB connections, ML models) — singleton, no copy.
        
        ```python
        @st.cache_resource
        def get_database():
            return create_connection()
        
        @st.cache_resource
        def load_model():
            return load_heavy_model()
        ```
        
        **Clear cache:**
        ```python
        get_database.clear()
        st.cache_resource.clear()
        ```
        """)

    with st.expander("📖 New cache guarantees", expanded=False):
        st.markdown("""
        **Recent updates:**
        - `my_cached_fn.clear()` now clears only that function's entries.
        - `@st.cache_resource` initialization is thread-safe per cache key.

        ```python
        @st.cache_data
        def users():
            ...

        @st.cache_data
        def products():
            ...

        users.clear()  # does not clear products cache
        ```
        """)
    
    with st.container(border=True):
        @st.cache_data(ttl=60)
        def expensive_computation(n):
            import time
            time.sleep(0.1)  # Simulate work
            return sum(range(n))

        @st.cache_data(ttl=60, copy=False)
        def immutable_cached_tuple(n):
            # Safe with copy=False because tuple values are immutable.
            return tuple(range(min(n, 10)))
        
        n = st.slider("Compute sum(0..n)", 1000, 100000, 10000)
        result = expensive_computation(n)
        st.write(f"Result: `{result:,}`")
        st.caption(f"Immutable cache sample (copy=False): {immutable_cached_tuple(8)}")
        st.caption("First call is slow, subsequent calls are instant (cached)!")


# =============================================================================
# 🎨 ADVANCED FEATURES
# =============================================================================
elif selected == "🎨 Advanced Features":
    st.title("🎨 Advanced Features")
    st.caption("Advanced functionality and patterns")

    # -------------------------------------------------------------------------
    # Page Configuration
    # -------------------------------------------------------------------------
    st.header("Page Configuration", divider="blue")
    st.caption("Test all `st.set_page_config()` options live — changes apply instantly!")

    with st.expander("📖 API Reference", expanded=False):
        st.markdown("""
        **Must be the first Streamlit command in your script.**""")
        st.markdown("""
        | Layout | Description |
        |--------|-------------|
        | `"centered"` | Max-width 896px, centered — good for text-heavy apps |
        | `"wide"` | Full viewport width — good for dashboards |
        | `"compact"` | Full width + minimal padding — maximum data density |
        """)
    st.code('''st.set_page_config(
            page_title="My App",             # Browser tab title
            page_icon="🚀",                  # Favicon: emoji or URL
            layout="centered",               # "centered" | "wide" | "compact"
            initial_sidebar_state="auto",    # "auto" | "expanded" | "collapsed"
            menu_items={...},                # Custom menu items (optional)
        )
        ''', language="python")

    # -------------------------------------------------------------------------
    # Threading Support
    # -------------------------------------------------------------------------
    st.header("Threading Support", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Run functions in background threads with session context.
        """)

        st.code('''def background_work():
        # st.* calls work here
        result = expensive_computation()
        st.session_state.result = result
        
        # Create thread with session context
        t = st.run_in_thread(background_work)
        t.start()
        t.join()
        
        # Or run directly
        st.run_with_session_context(some_function, arg1, arg2)
        ''', language="python")
        
    
    with st.container(border=True):
        if "thread_result" not in st.session_state:
            st.session_state.thread_result = None
        
        def _background_work():
            time.sleep(0.2)
            st.session_state.thread_result = "✅ Thread completed!"
        
        if st.button("Run background thread"):
            t = st.run_in_thread(_background_work)
            t.start()
            t.join()
        
        if st.session_state.thread_result:
            st.success(st.session_state.thread_result)

    # -------------------------------------------------------------------------
    # st.on_startup() / st.on_shutdown()
    # -------------------------------------------------------------------------
    st.header("st.on_startup() / st.on_shutdown()", divider="blue")

    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Register lifecycle hooks on ASGI server startup/shutdown.

        **Best practice:**
        - Declare hooks at module import time (top-level app code).
        - Keep startup/shutdown handlers idempotent and fast.
        """)

    st.code('''@st.on_startup
def init_resources():
    print("Server startup hook")

@st.on_shutdown
def close_resources():
    print("Server shutdown hook")''', language="python")

    with st.container(border=True):
        st.info(
            "Lifecycle hooks are intentionally shown as code-only in this demo. "
            "Declare them in your app module to run at server start/stop."
        )
    
    # -------------------------------------------------------------------------
    # Sidebar Control
    # -------------------------------------------------------------------------
    st.header("Programmatic Sidebar Control", divider="blue")
    
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        Control sidebar state programmatically.
        
        ```python
        st.set_sidebar_state("collapsed")
        st.set_sidebar_state("expanded")
        ```
        """)
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Collapse sidebar"):
                st.set_sidebar_state("collapsed")
        with col2:
            if st.button("Expand sidebar"):
                st.set_sidebar_state("expanded")

    # -------------------------------------------------------------------------
    # Scalability & Observability
    # -------------------------------------------------------------------------
    st.header("Scalability & Observability", divider="blue")

    with st.container(border=True):
        st.markdown("""
        This project now includes runtime guardrails and observability endpoints.

        **Production command**
        ```bash
        fastlit run examples/all_components_demo.py --host 0.0.0.0 --port 8501 --workers 4 --limit-concurrency 200 --backlog 2048 --max-sessions 300 --max-concurrent-runs 8 --run-timeout-seconds 45
        ```

        **Metrics endpoint**
        - `GET /_fastlit/metrics`
        - Includes sessions, run latency stats (avg/p50/p95/p99), payload stats, dropped events.

        **DataFrame server paging**
        - Large dataframes use windowed fetch via `/_fastlit/dataframe/{source_id}`.

        **Useful env vars**
        - `FASTLIT_WS_EVENT_QUEUE_SIZE`
        - `FASTLIT_WS_COALESCE_WINDOW_MS`
        - `FASTLIT_MAX_SESSION_STATE_BYTES`
        - `FASTLIT_MAX_WIDGET_STORE_BYTES`
        - `FASTLIT_MAX_UPLOAD_MB`
        """)

# =============================================================================
# 🔄 STREAMING & FRAGMENTS
# =============================================================================
elif selected == "🔄 Streaming & Fragments":
    import random

    st.title("🔄 Streaming & Fragments")
    st.caption("Real-time streaming output and isolated fragment reruns")

    # -------------------------------------------------------------------------
    # st.write_stream
    # -------------------------------------------------------------------------
    st.header("st.write_stream()", divider="blue")

    with st.expander("📖 API documentation", expanded=False):
        st.markdown("""
        **Signature**
        ```python
        st.write_stream(stream) -> str
        ```

        **Parameters**
        - `stream`: sync iterable / iterator / generator yielding text chunks (`str` or castable to `str`).

        **Returns**
        - Returns `""` immediately. The content is rendered progressively in the UI.

        **How it behaves**
        - A placeholder is created first.
        - The backend consumes your generator after the initial render patch.
        - Each chunk updates the same node (`updateProps`) until streaming completes.

        **Important notes**
        - Async generators are not supported directly.
        - Avoid yielding `None` (interpreted as end of stream by the backend loop).
        - If you need the final text in later reruns, store it manually in `st.session_state`.

        **Minimal example**
        ```python
        def fake_llm():
            for word in "Hello world".split():
                time.sleep(0.1)
                yield word + " "

        st.write_stream(fake_llm())  # returns ""
        ```
        """)

    st.code('''stream_sentences = [
    "Fastlit streams patches over WebSocket instead of full page reruns.",
    "write_stream renders progressively and shows output as chunks arrive.",
    "Fragments keep the rest of the app stable while local parts update.",
    "You can stream tokens, logs, query rows, or any custom generator.",
]

speed_col, btn_col = st.columns([3, 1])
with speed_col:
    delay_ms = st.slider(
        "Token delay (ms)",
        20,
        300,
        80,
        step=10,
        help="Simulates provider token latency",
    )
with btn_col:
    st.write("")
    run_stream = st.button("Stream", use_container_width=True)

if run_stream:
    sentence = random.choice(stream_sentences)

    def _fake_llm_gen(text: str, delay: float):
        words = text.split()
        for i, word in enumerate(words):
            time.sleep(delay)
            yield word + (" " if i < len(words) - 1 else "")

    st.markdown("**Response**")
    st.write_stream(_fake_llm_gen(sentence, delay_ms / 1000.0))
else:
    st.info("Click **Stream** to see progressive rendering.")''', language="python")

    with st.container(border=True):
        st.subheader("Live demo: fake LLM stream")

        stream_sentences = [
            "Fastlit streams patches over WebSocket instead of full page reruns.",
            "write_stream renders progressively and shows output as chunks arrive.",
            "Fragments keep the rest of the app stable while local parts update.",
            "You can stream tokens, logs, query rows, or any custom generator.",
        ]

        speed_col, btn_col = st.columns([3, 1])
        with speed_col:
            delay_ms = st.slider(
                "Token delay (ms)",
                20,
                300,
                80,
                step=10,
                help="Simulates provider token latency",
            )
        with btn_col:
            st.write("")
            run_stream = st.button("Stream", use_container_width=True)

        if run_stream:
            sentence = random.choice(stream_sentences)

            def _fake_llm_gen(text: str, delay: float):
                words = text.split()
                for i, word in enumerate(words):
                    time.sleep(delay)
                    yield word + (" " if i < len(words) - 1 else "")

            st.markdown("**Response**")
            st.write_stream(_fake_llm_gen(sentence, delay_ms / 1000.0))
        else:
            st.info("Click **Stream** to see progressive rendering.")

    st.divider()

    with st.container(border=True):
        st.subheader("Two streams in sequence")
        st.caption("Each call creates an independent streaming node.")
        st.code('''if st.button("Run 2 streams"):
    def _s1():
        for ch in "First paragraph streams here. ":
            time.sleep(0.03)
            yield ch

    def _s2():
        for ch in "Second paragraph starts right after. ":
            time.sleep(0.03)
            yield ch

    st.markdown("**Paragraph 1**")
    st.write_stream(_s1())
    st.markdown("**Paragraph 2**")
    st.write_stream(_s2())''', language="python")

        if st.button("Run 2 streams"):
            def _s1():
                for ch in "First paragraph streams here. ":
                    time.sleep(0.03)
                    yield ch

            def _s2():
                for ch in "Second paragraph starts right after. ":
                    time.sleep(0.03)
                    yield ch

            st.markdown("**Paragraph 1**")
            st.write_stream(_s1())
            st.markdown("**Paragraph 2**")
            st.write_stream(_s2())

    st.divider()

    # -------------------------------------------------------------------------
    # st.fragment
    # -------------------------------------------------------------------------
    st.header("@st.fragment", divider="blue")

    with st.expander("📖 API documentation", expanded=False):
        st.markdown("""
        **Signatures**
        ```python
        @st.fragment
        def my_fragment(): ...

        @st.fragment(run_every="3s")
        def auto_fragment(): ...
        ```

        **Parameters**
        - `run_every` (optional): auto-refresh interval.
        - Accepted values: `int`, `float`, `datetime.timedelta`, `"500ms"`, `"3s"`, `"2m"`, `"1h"`.

        **Behavior**
        - Widgets inside the fragment trigger reruns of only that fragment subtree.
        - The rest of the page does not rerender.
        - With `run_every`, the backend schedules periodic reruns for that fragment.

        **Best practices**
        - Keep heavy calls cached (`@st.cache_data`, `@st.cache_resource`).
        - Use realistic refresh intervals (commonly >= `500ms`).
        - Store business state in `st.session_state`.
        """)

    st.code('''@st.fragment
def _demo_counter():
    if "demo_count" not in st.session_state:
        st.session_state.demo_count = 0

    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        if st.button("+1", use_container_width=True):
            st.session_state.demo_count += 1
    with col_b:
        if st.button("Reset", use_container_width=True):
            st.session_state.demo_count = 0
    with col_c:
        st.metric("Count", st.session_state.demo_count)

_demo_counter()''', language="python")

    with st.container(border=True):
        st.subheader("Basic fragment counter")
        st.caption("Buttons rerun only this fragment.")

        @st.fragment
        def _demo_counter():
            if "demo_count" not in st.session_state:
                st.session_state.demo_count = 0

            col_a, col_b, col_c = st.columns([1, 1, 2])
            with col_a:
                if st.button("+1", use_container_width=True):
                    st.session_state.demo_count += 1
            with col_b:
                if st.button("Reset", use_container_width=True):
                    st.session_state.demo_count = 0
            with col_c:
                st.metric("Count", st.session_state.demo_count)

        _demo_counter()
        st.caption("This caption remains stable while the fragment reruns.")

    st.divider()

    st.header("@st.fragment(run_every=...)", divider="blue")

    with st.expander("📖 run_every formats", expanded=False):
        st.markdown("""
        | Format | Example | Meaning |
        |--------|---------|---------|
        | `int` / `float` | `5` | 5 seconds |
        | `str` | `"500ms"` | 500 milliseconds |
        | `str` | `"2m"` | 2 minutes |
        | `str` | `"1h"` | 1 hour |
        | `timedelta` | `datetime.timedelta(seconds=10)` | 10 seconds |

        Timer tasks are scoped to the WebSocket session and cancelled on disconnect.
        """)

    st.code('''@st.fragment(run_every="2s")
def _live_metrics():
    cpu = random.uniform(10, 95)
    mem = random.uniform(40, 85)
    rps = random.randint(50, 500)
    latency = random.uniform(2, 120)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("CPU", f"{cpu:.1f}%", delta=f"{random.uniform(-5, 5):.1f}%", delta_color="inverse")
    with c2:
        st.metric("Memory", f"{mem:.1f}%", delta=f"{random.uniform(-3, 3):.1f}%", delta_color="inverse")
    with c3:
        st.metric("Req/s", f"{rps}", delta=f"{random.randint(-20, 20)}")
    with c4:
        st.metric("Latency", f"{latency:.0f} ms", delta=f"{random.uniform(-10, 10):.0f} ms", delta_color="inverse")

    st.caption(f"Last update: {datetime.datetime.now().strftime('%H:%M:%S')} (every 2s)")

_live_metrics()''', language="python")

    with st.container(border=True):
        st.subheader("Auto-refresh metrics (2s)")

        @st.fragment(run_every="2s")
        def _live_metrics():
            cpu = random.uniform(10, 95)
            mem = random.uniform(40, 85)
            rps = random.randint(50, 500)
            latency = random.uniform(2, 120)

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("CPU", f"{cpu:.1f}%", delta=f"{random.uniform(-5, 5):.1f}%", delta_color="inverse")
            with c2:
                st.metric("Memory", f"{mem:.1f}%", delta=f"{random.uniform(-3, 3):.1f}%", delta_color="inverse")
            with c3:
                st.metric("Req/s", f"{rps}", delta=f"{random.randint(-20, 20)}")
            with c4:
                st.metric("Latency", f"{latency:.0f} ms", delta=f"{random.uniform(-10, 10):.0f} ms", delta_color="inverse")

            st.caption(f"Last update: {datetime.datetime.now().strftime('%H:%M:%S')} (every 2s)")

        _live_metrics()

    st.divider()

    with st.container(border=True):
        st.subheader("Hybrid: timer + manual action")
        st.code('''@st.fragment(run_every="3s")
def _hybrid_fragment():
    if "hf_rolls" not in st.session_state:
        st.session_state.hf_rolls = []

    if st.button("Roll now"):
        st.session_state.hf_rolls.append(random.randint(1, 6))
    else:
        st.session_state.hf_rolls.append(random.randint(1, 6))

    rolls = st.session_state.hf_rolls[-10:]
    st.session_state.hf_rolls = rolls

    if rolls:
        avg = sum(rolls) / len(rolls)
        r_col, a_col = st.columns(2)
        with r_col:
            st.markdown("**Last 10 rolls:** " + " ".join(f"`{r}`" for r in rolls))
        with a_col:
            st.metric("Average", f"{avg:.2f}")

_hybrid_fragment()''', language="python")

        @st.fragment(run_every="3s")
        def _hybrid_fragment():
            if "hf_rolls" not in st.session_state:
                st.session_state.hf_rolls = []

            if st.button("Roll now"):
                st.session_state.hf_rolls.append(random.randint(1, 6))
            else:
                st.session_state.hf_rolls.append(random.randint(1, 6))

            rolls = st.session_state.hf_rolls[-10:]
            st.session_state.hf_rolls = rolls

            if rolls:
                avg = sum(rolls) / len(rolls)
                r_col, a_col = st.columns(2)
                with r_col:
                    st.markdown("**Last 10 rolls:** " + " ".join(f"`{r}`" for r in rolls))
                with a_col:
                    st.metric("Average", f"{avg:.2f}")

        _hybrid_fragment()

# =============================================================================
# 🧩 CUSTOM COMPONENTS
# =============================================================================
elif selected == "🧩 Custom Components":
    st.title("🧩 Custom Components")
    st.caption(
        "Compatibility layer for `st.components.v1`: static HTML, external iframes, "
        "and interactive components via Streamlit postMessage protocol."
    )

    st.divider()

    # -------------------------------------------------------------------------
    # st.components.v1.html
    # -------------------------------------------------------------------------
    with st.container(border=True):
        st.subheader("`st.components.v1.html()` — Static HTML")
        with st.expander("📖 Documentation", expanded=False):
            st.markdown("""
            **Parameters:**
            - `html_string` (str): HTML payload rendered in a sandboxed iframe
            - `height` (int | None): Iframe height in pixels (default `150`)
            - `scrolling` (bool): Enable scrollbars inside the iframe

            **Behavior:**
            - Uses a sandboxed iframe (`allow-scripts`)
            - Scripts run client-side, isolated from the parent app context
            """)

        col_code, col_preview = st.columns([1, 1])

        with col_code:
            st.code(
                '''st.components.v1.html("""
<style>
  body { font-family: sans-serif; margin: 12px; }
  .card {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white; border-radius: 12px;
    padding: 20px; text-align: center;
  }
  h2 { margin: 0 0 8px; font-size: 1.4rem; }
  p  { margin: 0; opacity: .85; font-size: .9rem; }
</style>
<div class="card">
  <h2>🚀 Custom HTML Card</h2>
  <p>Rendered inside a sandboxed iframe</p>
</div>
""", height=130)''',
                language="python",
            )

        with col_preview:
            st.components.v1.html(
                """
<style>
  body { font-family: sans-serif; margin: 12px; }
  .card {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white; border-radius: 12px;
    padding: 20px; text-align: center;
  }
  h2 { margin: 0 0 8px; font-size: 1.4rem; }
  p  { margin: 0; opacity: .85; font-size: .9rem; }
</style>
<div class="card">
  <h2>🚀 Custom HTML Card</h2>
  <p>Rendered inside a sandboxed iframe</p>
</div>
""",
                height=130,
            )

    st.divider()

    # -------------------------------------------------------------------------
    # HTML + JavaScript (client-only)
    # -------------------------------------------------------------------------
    with st.container(border=True):
        st.subheader("HTML + JavaScript (client-only)")
        with st.expander("📖 Documentation", expanded=False):
            st.markdown("""
            `st.components.v1.html()` is display-only from Python's perspective.

            - JavaScript executes in the iframe
            - No value is returned to Python
            - For bidirectional communication, use `declare_component()`
            """)

        st.code(
            '''st.components.v1.html("""
<canvas id="c" width="400" height="80"></canvas>
<script>
  const ctx = document.getElementById("c").getContext("2d");
  let x = 0;
  setInterval(function () {
    ctx.clearRect(0, 0, 400, 80);
    ctx.fillStyle = "#667eea";
    ctx.beginPath();
    ctx.arc(x % 400, 40, 18, 0, Math.PI * 2);
    ctx.fill();
    x += 3;
  }, 30);
</script>
""", height=90)''',
            language="python",
        )

        st.components.v1.html(
            """
<canvas id="c" width="400" height="80"></canvas>
<script>
  const ctx = document.getElementById("c").getContext("2d");
  let x = 0;
  setInterval(function () {
    ctx.clearRect(0, 0, 400, 80);
    ctx.fillStyle = "#667eea";
    ctx.beginPath();
    ctx.arc(x % 400, 40, 18, 0, Math.PI * 2);
    ctx.fill();
    x += 3;
  }, 30);
</script>
""",
            height=90,
        )

    st.divider()

    # -------------------------------------------------------------------------
    # st.components.v1.iframe
    # -------------------------------------------------------------------------
    with st.container(border=True):
        st.subheader("`st.components.v1.iframe()` — Embed External URL")
        with st.expander("📖 Documentation", expanded=False):
            st.markdown("""
            **Parameters:**
            - `src` (str): External URL to display
            - `height` (int | None): Iframe height in pixels
            - `scrolling` (bool): Enable scrollbars

            Read-only embed. No value is sent back to Python.
            """)

        url = st.text_input(
            "URL to embed",
            value="https://example.com",
            key="iframe_url",
        )
        iframe_height = st.slider("Height (px)", 100, 600, 250, key="iframe_h")

        st.code(
            f'st.components.v1.iframe("{url}", height={iframe_height})',
            language="python",
        )

        st.components.v1.iframe(url, height=iframe_height)

    st.divider()

    # -------------------------------------------------------------------------
    # st.components.v1.declare_component
    # -------------------------------------------------------------------------
    def _ensure_demo_component_build_dir() -> str:
        import tempfile
        from pathlib import Path

        build_dir = Path(tempfile.gettempdir()) / "fastlit_demo_counter_component_v2"
        build_dir.mkdir(parents=True, exist_ok=True)

        component_html = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: transparent;
    }
    .wrap {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 12px;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
    }
    .label {
      font-size: 12px;
      color: #6b7280;
      margin-bottom: 4px;
    }
    .value {
      font-size: 24px;
      font-weight: 700;
      min-width: 44px;
      text-align: center;
      color: #111827;
    }
    .controls { display: flex; align-items: center; gap: 8px; }
    button {
      border: none;
      border-radius: 8px;
      width: 34px;
      height: 34px;
      cursor: pointer;
      font-size: 18px;
      font-weight: 700;
      color: white;
      background: #4f46e5;
    }
    button:active { transform: translateY(1px); }
  </style>
</head>
<body>
  <div class="wrap">
    <div>
      <div class="label" id="lbl">Counter</div>
      <div class="value" id="val">0</div>
    </div>
    <div class="controls">
      <button id="dec" type="button">−</button>
      <button id="inc" type="button">+</button>
    </div>
  </div>

  <script>
    (function () {
      var state = {
        value: 0,
        step: 1,
        label: "Counter",
        resetNonce: "",
        lastHeight: 0
      };
      var initialized = false;

      function setHeight() {
        var root = document.querySelector(".wrap");
        var measured = root ? Math.ceil(root.getBoundingClientRect().height) : 56;
        var nextHeight = Math.max(56, Math.min(240, measured + 2));
        if (nextHeight !== state.lastHeight) {
          state.lastHeight = nextHeight;
          window.parent.postMessage(
            { type: "streamlit:setFrameHeight", height: nextHeight },
            "*"
          );
        }
      }

      function sendValue() {
        window.parent.postMessage({ type: "streamlit:setComponentValue", value: state.value }, "*");
      }

      function paint() {
        document.getElementById("lbl").textContent = state.label;
        document.getElementById("val").textContent = String(state.value);
      }

      function applyArgs(args) {
        var nextLabel = typeof args.label === "string" ? args.label : "Counter";
        var nextStep = Number(args.step);
        var nextInitial = Number(args.initial);
        var nextResetNonce = String(args.reset_nonce == null ? "" : args.reset_nonce);

        state.label = nextLabel;
        if (Number.isFinite(nextStep) && nextStep > 0) {
          state.step = nextStep;
        }

        if (!initialized || nextResetNonce !== state.resetNonce) {
          state.value = Number.isFinite(nextInitial) ? nextInitial : 0;
          state.resetNonce = nextResetNonce;
          initialized = true;
        }
      }

      document.getElementById("inc").addEventListener("click", function () {
        state.value += state.step;
        paint();
        sendValue();
      });
      document.getElementById("dec").addEventListener("click", function () {
        state.value -= state.step;
        paint();
        sendValue();
      });

      window.addEventListener("message", function (event) {
        var data = event.data || {};
        if (data.type !== "streamlit:render") return;
        applyArgs(data.args || {});
        paint();
        setHeight();
        sendValue();
      });

      window.parent.postMessage({ type: "streamlit:componentReady", apiVersion: 1 }, "*");
      setHeight();
    })();
  </script>
</body>
</html>
"""
        (build_dir / "index.html").write_text(component_html, encoding="utf-8")
        return str(build_dir)

    with st.container(border=True):
        st.subheader("`st.components.v1.declare_component()` — Interactive Component")
        with st.expander("📖 Documentation", expanded=False):
            st.markdown("""
            **Parameters:**
            - `name` (str): Unique component identifier
            - `url` (str | None): Dev server URL (HMR workflow)
            - `path` (str | None): Built frontend directory served at `/_components/{name}/`

            **Protocol expected in iframe JS:**
            - Parent → child: `streamlit:render`
            - Child → parent: `streamlit:componentReady`
            - Child → parent: `streamlit:setComponentValue`
            - Child → parent: `streamlit:setFrameHeight`
            """)

        st.code(
            '''demo_counter = st.components.v1.declare_component(
    "demo_counter_component_v2",
    path=_ensure_demo_component_build_dir(),
)

value = demo_counter(
    label="Demo counter",
    step=2,
    initial=10,
    reset_nonce=0,
    key="demo_counter_component_widget",
)
st.write("Returned value:", value)''',
            language="python",
        )

        if "demo_counter_reset_nonce" not in st.session_state:
            st.session_state.demo_counter_reset_nonce = 0

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            step = st.slider("Step", min_value=1, max_value=10, value=1, key="counter_step")
        with c2:
            initial = st.slider("Initial value", min_value=0, max_value=50, value=5, key="counter_init")
        with c3:
            st.markdown("&nbsp;")
            if st.button("Reset to initial", key="counter_reset"):
                st.session_state.demo_counter_reset_nonce += 1

        demo_counter = st.components.v1.declare_component(
            "demo_counter_component_v2",
            path=_ensure_demo_component_build_dir(),
        )

        counter_value = demo_counter(
            label="Demo counter",
            step=int(step),
            initial=int(initial),
            reset_nonce=int(st.session_state.demo_counter_reset_nonce),
            key="demo_counter_component_widget",
            default=int(initial),
        )

        st.metric("Value returned to Python", counter_value)
        st.caption(
            "This demo is fully interactive: button clicks in the iframe send "
            "`streamlit:setComponentValue`, and Python receives the value on rerun."
        )

    st.divider()

    # -------------------------------------------------------------------------
    # scrolling=True demo
    # -------------------------------------------------------------------------
    with st.container(border=True):
        st.subheader("`scrolling=True` behavior")
        with st.expander("📖 Documentation", expanded=False):
            st.markdown("""
            - `scrolling=False` (default): iframe content is clipped
            - `scrolling=True`: iframe shows scrollbars when content exceeds height
            """)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**scrolling=False** (default)")
            st.components.v1.html(
                "<br>".join(f"<p>Line {i}</p>" for i in range(1, 12)),
                height=80,
                scrolling=False,
            )
        with col2:
            st.markdown("**scrolling=True**")
            st.components.v1.html(
                "<br>".join(f"<p>Line {i}</p>" for i in range(1, 12)),
                height=80,
                scrolling=True,
            )

# =============================================================================
# 🔐 AUTH (BETA)
# =============================================================================
elif selected == "🔐 Auth (Beta)":
    st.title("🔐 Auth (Beta)")
    st.caption("OIDC authentication — `st.user`, `st.require_login()`, `st.logout()`")

    st.warning(
        "**Beta feature** — The implementation is complete (Authorization Code + PKCE, "
        "HMAC-signed cookies) but has not been validated against a live IdP. "
        "API and behaviour may change.",
        icon="⚠️",
    )

    st.divider()

    # -------------------------------------------------------------------------
    # Overview
    # -------------------------------------------------------------------------
    with st.container(border=True):
        st.subheader("Overview")
        st.markdown("""
        Fastlit integrates **OpenID Connect** at the server level — compatible with any
        OIDC provider (Google, Azure AD, Okta, Keycloak, Dex…) via auto-discovery
        (`/.well-known/openid-configuration`).

        Auth is **opt-in**: without an `[auth]` section in `secrets.toml`, the app
        runs normally and all auth calls are no-ops.

        **Install the extra:**
        ```bash
        pip install "fastlit[auth]"
        ```
        """)

    st.divider()

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------
    with st.container(border=True):
        st.subheader("`secrets.toml` configuration")
        with st.expander("📖 All options", expanded=True):
            st.markdown("""
            | Key | Required | Description |
            |---|---|---|
            | `provider` | yes | Always `"oidc"` |
            | `issuer_url` | yes | OIDC issuer (e.g. `https://accounts.google.com`) |
            | `client_id` | yes | OAuth2 client ID |
            | `client_secret` | yes* | OAuth2 client secret (*optional for public clients) |
            | `redirect_uri` | yes | Must match IdP registration (e.g. `http://localhost:8501/auth/callback`) |
            | `cookie_secret` | yes | HMAC signing key, min 32 chars |
            | `scopes` | no | Default: `["openid", "profile", "email"]` |
            | `cookie_name` | no | Default: `fl_session` |
            | `cookie_max_age` | no | Default: `86400` (24 h) |
            """)
        st.code("""
[auth]
provider = "oidc"
issuer_url = "https://accounts.google.com"
client_id = "your-client-id"
client_secret = "your-client-secret"
redirect_uri = "http://localhost:8501/auth/callback"
cookie_secret = "change-me-32-chars-minimum!!!!!"
scopes = ["openid", "profile", "email"]
""", language="toml")

    st.divider()

    # -------------------------------------------------------------------------
    # st.require_login
    # -------------------------------------------------------------------------
    with st.container(border=True):
        st.subheader("`st.require_login()`")
        with st.expander("📖 Documentation", expanded=False):
            st.markdown("""
            **Signature:** `st.require_login() -> None`

            Call at the top of any page that requires authentication. If the user
            has no valid session cookie, raises an internal exception that redirects
            to `/auth/login?next=<current_path>`.

            When auth is not configured (no `[auth]` in `secrets.toml`), this is a no-op.
            """)
        st.code("""
import fastlit as st

st.require_login()   # ← redirect to /auth/login if not authenticated

st.title("Protected page")
st.write(f"Welcome, {st.user.name}!")
""", language="python")

    st.divider()

    # -------------------------------------------------------------------------
    # st.user
    # -------------------------------------------------------------------------
    with st.container(border=True):
        st.subheader("`st.user`")
        with st.expander("📖 Documentation", expanded=False):
            st.markdown(r"""
            Lazy proxy that reads OIDC claims from the current session.

            | Property | OIDC claim | Type |
            |---|---|---|
            | `st.user.is_logged_in` | — | `bool` |
            | `st.user.email` | `email` | `str \\| None` |
            | `st.user.name` | `name` / `preferred_username` | `str \\| None` |
            | `st.user.sub` | `sub` | `str \\| None` |
            | `st.user.<claim>` | any | `Any` |

            All claims from the ID token are accessible as attributes.
            When auth is disabled or the user is not logged in, all properties
            return `None` / `False`.
            """)
        col_code, col_live = st.columns([1, 1])
        with col_code:
            st.code("""
import fastlit as st

# Check login status
if st.user.is_logged_in:
    st.success(f"Logged in as {st.user.email}")
else:
    st.info("Not authenticated (auth disabled or not logged in)")

# Access any OIDC claim
st.write("Name:", st.user.name)
st.write("Subject:", st.user.sub)
st.write("Picture:", st.user.picture)   # if provided by IdP
""", language="python")
        with col_live:
            st.markdown("**Live values** (in this session):")
            if st.user.is_logged_in:
                st.success(f"Logged in as `{st.user.email}`")
                st.json({
                    "is_logged_in": st.user.is_logged_in,
                    "email": st.user.email,
                    "name": st.user.name,
                    "sub": st.user.sub,
                })
            else:
                st.info("Not authenticated — auth is disabled in this demo (no `[auth]` in secrets.toml).")
                st.json({
                    "is_logged_in": False,
                    "email": None,
                    "name": None,
                    "sub": None,
                })

    st.divider()

    # -------------------------------------------------------------------------
    # st.logout
    # -------------------------------------------------------------------------
    with st.container(border=True):
        st.subheader("`st.logout()`")
        with st.expander("📖 Documentation", expanded=False):
            st.markdown("""
            **Signature:** `st.logout() -> None`

            Clears the session cookie and redirects to `/auth/logout` → then to `/`.
            Typically called inside a button handler.
            """)
        st.code("""
import fastlit as st

st.require_login()

if st.button("Sign out", type="secondary"):
    st.logout()
""", language="python")

    st.divider()

    # -------------------------------------------------------------------------
    # Auth flow diagram
    # -------------------------------------------------------------------------
    with st.container(border=True):
        st.subheader("Auth flow")
        st.markdown("""
        ```
        Browser          Fastlit server         IdP (Google/Azure/…)
           │                   │                        │
           │── GET /page ──────►│                        │
           │                   │ (no valid cookie)       │
           │◄─ 302 /auth/login─│                        │
           │                   │                        │
           │── GET /auth/login ►│                        │
           │                   │ generate state+PKCE     │
           │◄─ 302 IdP URL ───►│────── redirect ────────►│
           │                   │                        │
           │◄──────────────────────────────────────────►│
           │          user authenticates at IdP         │
           │                   │                        │
           │── GET /auth/callback?code=… ──────────────►│
           │                   │◄── token response ─────│
           │                   │  parse id_token claims  │
           │◄─ 302 /page ──────│  set fl_session cookie  │
           │    (with cookie)  │                        │
           │── GET /page ──────►│                        │
           │                   │  verify cookie HMAC     │
           │◄─ 200 (app) ──────│  attach user_claims     │
        ```
        """)

    st.divider()

    # -------------------------------------------------------------------------
    # Providers
    # -------------------------------------------------------------------------
    with st.container(border=True):
        st.subheader("Provider examples")
        provider = st.selectbox(
            "Select provider",
            ["Google", "Azure AD", "Okta", "Keycloak (self-hosted)"],
            key="auth_provider_select",
        )
        configs = {
            "Google": """[auth]
provider = "oidc"
issuer_url = "https://accounts.google.com"
client_id = "XXXXXXX.apps.googleusercontent.com"
client_secret = "GOCSPX-XXXXXXXXXXXXXXX"
redirect_uri = "http://localhost:8501/auth/callback"
cookie_secret = "change-me-32-chars-minimum!!!!!"
scopes = ["openid", "profile", "email"]""",
            "Azure AD": """[auth]
provider = "oidc"
issuer_url = "https://login.microsoftonline.com/<tenant-id>/v2.0"
client_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_secret = "your-client-secret"
redirect_uri = "http://localhost:8501/auth/callback"
cookie_secret = "change-me-32-chars-minimum!!!!!"
scopes = ["openid", "profile", "email"]""",
            "Okta": """[auth]
provider = "oidc"
issuer_url = "https://your-org.okta.com"
client_id = "your-client-id"
client_secret = "your-client-secret"
redirect_uri = "http://localhost:8501/auth/callback"
cookie_secret = "change-me-32-chars-minimum!!!!!"
scopes = ["openid", "profile", "email"]""",
            "Keycloak (self-hosted)": """[auth]
provider = "oidc"
issuer_url = "http://localhost:8080/realms/myrealm"
client_id = "fastlit"
client_secret = "your-client-secret"
redirect_uri = "http://localhost:8501/auth/callback"
cookie_secret = "change-me-32-chars-minimum!!!!!"
scopes = ["openid", "profile", "email"]""",
        }
        st.code(configs[provider], language="toml")


# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("Built with **Fastlit** A Streamlit-compatible, blazing fast Python UI framework 🚀")


