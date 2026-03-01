"""Page System page for the Fastlit demo."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Page System",
    "icon": "🗂️",
    "order": 10,
}

st.title("🗂️ Page System")
st.caption("File-based pages, global layout, and routing conventions")

st.markdown("""
Fastlit now supports a **file-based page system** that works with a global
layout entrypoint.

If Fastlit finds a sibling `pages/` directory next to your `app.py`, it will:

- auto-discover `pages/*.py`
- use the filename as the route by default
- build navigation from `st.navigation()`
- render the selected page implicitly inside `app.py`
""")

st.header("Mental Model", divider="blue")

col1, col2 = st.columns([1.2, 1])
with col1:
    st.markdown("""
    Think of it like this:

    - `app.py` = the shared shell/layout
    - `pages/*.py` = the actual screens
    - `st.sidebar.navigation()` = the router entry

    So your header, sidebar, footer, or shared widgets stay in `app.py`,
    while each page lives in its own file.
    """)
with col2:
    st.code(
        """app.py
pages/
  index.py
  page_system.py
  input_widgets.py
  state_control.py""",
        language="text",
    )

st.header("Global Layout", divider="blue")

st.code(
    '''import fastlit as st

st.set_page_config(page_title="My App", layout="wide")

st.sidebar.title("My App")
st.sidebar.navigation()

st.caption("Shared footer visible on every page")''',
    language="python",
)

with st.container(border=True):
    st.info(
        "`app.py` stays the entry script and acts as the global layout "
        "when a `pages/` directory exists."
    )

st.header("Route Rules", divider="blue")

left, right = st.columns(2)
with left:
    st.markdown("""
    **Default mapping**

    - `pages/index.py` -> `/index`
    - `pages/page_system.py` -> `/page_system`
    - `pages/status_feedback.py` -> `/status_feedback`
    - `pages/custom_components.py` -> `/custom_components`
    """)
with right:
    st.markdown("""
    **Notes**

    - underscores are preserved
    - filenames are the default slugs
    - you can override the slug with metadata
    - hidden pages are not shown in navigation
    """)

st.header("Page Metadata", divider="blue")

st.markdown("Each page can declare its own sidebar and routing metadata.")

st.code(
    '''PAGE_CONFIG = {
    "title": "Status & Feedback",
    "icon": "⚡",
    "order": 70,
    "default": False,
    "hidden": False,
    "url_path": "status_feedback",
}''',
    language="python",
)

st.markdown("""
Supported options:

- `title`: label shown in navigation
- `icon`: emoji or text icon
- `order`: sort order in the sidebar
- `default`: marks the default page
- `hidden`: removes the page from navigation
- `url_path`: overrides the route slug
""")

st.header("Implicit vs Explicit", divider="blue")

tab1, tab2 = st.tabs(["Implicit pages/", "Explicit st.Page()"])

with tab1:
    st.markdown("""
    **Implicit mode** is the new file-based mode.

    You just create `app.py` + `pages/`, then call:
    """)
    st.code("st.sidebar.navigation()", language="python")
    st.caption(
        "Fastlit auto-discovers pages and renders the selected page "
        "inside the global layout."
    )

with tab2:
    st.markdown("""
    **Explicit mode** still exists when you want full manual control.
    """)
    st.code(
        '''page = st.navigation([
    st.Page("pages/index.py", title="Home", default=True),
    st.Page("pages/charts.py", title="Charts"),
])

page.run()''',
        language="python",
    )
    st.caption(
        "Use this mode if you want to register pages manually instead of relying on `pages/`."
    )

st.header("Monolithic Apps Still Work", divider="blue")

st.success(
    "The page system is optional. You can still build a classic mono-file app "
    "with a single `app.py` and no `pages/` directory."
)

st.code(
    '''import fastlit as st

st.title("Single-file app")
name = st.text_input("Name")

if st.button("Run"):
    st.write(f"Hello {name or 'world'}")''',
    language="python",
)

st.header("When To Use Which", divider="blue")

choice1, choice2, choice3 = st.columns(3)
with choice1:
    st.markdown("""
    **Mono-file**

    Good for:
    - small prototypes
    - quick experiments
    - linear apps
    """)
with choice2:
    st.markdown("""
    **pages/**

    Good for:
    - growing apps
    - one file per screen
    - step-by-step iteration
    """)
with choice3:
    st.markdown("""
    **Manual st.Page**

    Good for:
    - full control
    - custom registration
    - advanced routing setup
    """)

st.header("Best Practices", divider="blue")

st.markdown("""
- Keep shared layout elements in `app.py`
- Keep page-specific UI inside each page file
- Extract reusable helpers into shared modules when duplication appears
- Prefer clear filenames because they become routes by default
- Use `PAGE_CONFIG["order"]` to keep sidebar navigation stable
""")

st.header("Live Links", divider="blue")

links = st.columns(3)
with links[0]:
    st.page_link("/index", label="Home", icon="🏠")
with links[1]:
    st.page_link("/layout", label="Layout API", icon="📐")
with links[2]:
    st.page_link("/state_control", label="State Control", icon="🔄")
