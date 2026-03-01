"""Text Elements page for the Fastlit demo."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Text Elements",
    "icon": "📝",
    "order": 20,
}

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
