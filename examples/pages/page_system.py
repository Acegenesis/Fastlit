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

- auto-discover `pages/**/*.py`
- use the filename as the route by default
- build navigation from `st.navigation()`
- group nested pages in the sidebar automatically
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
    **Default mapping** from `pages/` to routes:
                
    - `pages/index.py` -> `/`
    - `pages/admin/index.py` -> `/admin`
    - `pages/admin/users.py` -> `/admin/users`
    - `pages/blog/[id].py` -> `/blog/[id]`
    - `pages/docs/[...slug].py` -> `/docs/a/b/c`
    - `pages/page_system.py` -> `/page_system`
    """)
with right:
    st.markdown("""
    **Notes**

    - underscores are preserved
    - filenames are the default slugs
    - you can override the slug with metadata
    - sidebar groups remember their open/closed state
    - hidden pages are not shown in navigation
    - `404.py` is used for unknown routes
    - `403.py` is used for forbidden routes when available
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
- `guard`: route guard metadata like auth/roles
""")

st.code(
    '''PAGE_CONFIG = {
    "title": "Admin Secure",
    "hidden": True,
    "guard": {
        "auth": True,
        "roles": ["admin"],
    },
}''',
    language="python",
)

st.header("Advanced Routing", divider="blue")

cards = st.columns(2)
with cards[0]:
    st.markdown("""
    **Nested routes**

    Put files in subfolders:

    - `pages/admin/users.py`
    - `pages/admin/settings.py`
    - `pages/shop/orders.py`

    Fastlit will group them in the sidebar by section.
    """)
with cards[1]:
    st.markdown("""
    **Dynamic routes**

    Use bracket syntax:

    - `[id].py` for one segment
    - `[...slug].py` for catch-all routes
    """)

st.header("Nested Layouts", divider="blue")

st.markdown("""
Fastlit can also apply nested layouts from a sibling `layouts/` directory.
""")

st.code(
    '''# layouts/admin.py
import fastlit as st

st.info("Admin layout")
st.page_outlet()
st.caption("Admin footer")''',
    language="python",
)

st.caption(
    "For a route like `/admin/users`, Fastlit can apply `layouts/default.py` "
    "then `layouts/admin.py`, then `layouts/admin/default.py` before rendering the page."
)

st.header("Route Helpers", divider="blue")

st.markdown("""
Use `st.page_path()` when you want to build a route from a file path or a
dynamic template, then pass the result to `st.page_link()` or call
`st.switch_page()` directly with params.
""")

st.code(
    '''st.page_link(
    st.page_path("pages/blog/[id].py", id=42),
    label="Blog post 42",
)

if st.button("Open docs route"):
    st.switch_page("pages/docs/[...slug].py", slug=["guides", "routing"])''',
    language="python",
)

st.header("Route Context", divider="blue")

st.code(
    '''import fastlit as st

st.write(st.context.path)
st.write(st.context.route_params)
st.write(st.context.layout_stack)
st.write(st.context.guard_failure)''',
    language="python",
)

st.write("Current path:", st.context.path)
st.write("Current route params:", st.context.route_params)
st.write("Current layout stack:", st.context.layout_stack)
st.write("Current guard failure:", st.context.guard_failure)

st.caption(
    "On a static page like `/page_system`, empty `route_params` and `layout_stack` are expected."
)

st.markdown("**Route Context test links**")

context_links = st.columns(4)
with context_links[0]:
    st.page_link("/page_system", label="Static Route", icon="📄")
    st.caption("Expected: `route_params = {}`")
with context_links[1]:
    st.page_link("/blog/42", label="Dynamic Route", icon="📝")
    st.caption("Expected: `{'id': '42'}`")
with context_links[2]:
    st.page_link("/docs/guides/routing", label="Catch-All Route", icon="📚")
    st.caption("Expected: `{'slug': ['guides', 'routing']}`")
with context_links[3]:
    st.page_link("/admin/users", label="Nested Layout", icon="🛡️")
    st.caption("Expected: non-empty `layout_stack`")

parent_link = st.columns(1)
with parent_link[0]:
    st.page_link("/admin", label="Parent Admin Page", icon="🧭")
    st.caption("Expected: clickable sidebar parent group entry for `Admin`.")

guard_test = st.columns(2)
with guard_test[0]:
    st.page_link("/admin/secure", label="Guard Failure", icon="🔒")
with guard_test[1]:
    st.caption(
        "Expected without `admin` role: `guard_failure = 'roles'` and render `403.py`."
    )

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
    st.Page("pages/index.py", title="Home", url_path="", default=True),
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
- Use `index.py` for section landing pages like `/` or `/admin`
""")

st.header("Live Links", divider="blue")

links = st.columns(3)
with links[0]:
    st.page_link("/", label="Home", icon="🏠")
with links[1]:
    st.page_link("/layout", label="Layout API", icon="📐")
with links[2]:
    st.page_link("/state_control", label="State Control", icon="🔄")

demo_links = st.columns(4)
with demo_links[0]:
    st.page_link("/admin/users", label="Nested Admin Route", icon="🛡️")
with demo_links[1]:
    st.page_link("/blog/42", label="Dynamic Blog Route", icon="📝")
with demo_links[2]:
    st.page_link("/docs/guides/routing", label="Catch-All Route", icon="📚")
with demo_links[3]:
    st.page_link("/missing/demo", label="404 Demo", icon="🚫")

guard_links = st.columns(2)
with guard_links[0]:
    st.page_link("/admin/secure", label="403 Guard Demo", icon="🔒")
with guard_links[1]:
    st.caption("If no `admin` role is present, Fastlit should render `403.py`.")
