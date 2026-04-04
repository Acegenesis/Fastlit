import fastlit.runtime.page_discovery as page_discovery
from pathlib import Path

from fastlit import page_path
from fastlit.runtime.navigation_slug import slugify_page_token
from fastlit.runtime.page_discovery import (
    build_navigation_items,
    clear_discover_pages_cache,
    discover_pages,
    read_page_config,
    resolve_page,
    visible_pages,
)
from fastlit.runtime.session import Session, SwitchPageException
from fastlit.ui.layout import switch_page


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_read_page_config_supports_dict_and_constant_metadata(tmp_path: Path) -> None:
    page_path = tmp_path / "pages" / "charts.py"
    _write(
        page_path,
        """
PAGE_CONFIG = {"title": "Charts", "icon": "C", "order": 20}
PAGE_DEFAULT = True
PAGE_HIDDEN = False
PAGE_URL_PATH = "custom_charts"
PAGE_AUTH = True
PAGE_ROLES = ["admin"]
""".strip(),
    )

    config = read_page_config(page_path)

    assert config == {
        "title": "Charts",
        "icon": "C",
        "order": 20,
        "default": True,
        "hidden": False,
        "url_path": "custom_charts",
        "auth": True,
        "roles": ["admin"],
    }


def test_discover_pages_supports_nested_routes_special_pages_and_layouts(tmp_path: Path) -> None:
    entry_path = tmp_path / "app.py"
    _write(entry_path, "import fastlit as st\n")
    _write(
        tmp_path / "layouts" / "default.py",
        'import fastlit as st\nst.text("DEFAULT LAYOUT")\n',
    )
    _write(
        tmp_path / "layouts" / "admin.py",
        'import fastlit as st\nst.text("ADMIN LAYOUT")\n',
    )
    _write(
        tmp_path / "layouts" / "admin" / "default.py",
        'import fastlit as st\nst.text("ADMIN DEFAULT")\n',
    )
    _write(
        tmp_path / "pages" / "index.py",
        """
PAGE_CONFIG = {"title": "Home", "icon": "H", "order": 0}
""".strip(),
    )
    _write(
        tmp_path / "pages" / "admin" / "index.py",
        """
PAGE_CONFIG = {"title": "Admin", "icon": "A", "order": 5}
""".strip(),
    )
    _write(
        tmp_path / "pages" / "status_feedback.py",
        """
PAGE_TITLE = "Status Feedback"
PAGE_ORDER = 30
""".strip(),
    )
    _write(
        tmp_path / "pages" / "admin" / "users.py",
        """
PAGE_CONFIG = {"title": "Users", "icon": "U", "order": 10}
PAGE_ROLES = ["admin"]
""".strip(),
    )
    _write(tmp_path / "pages" / "blog" / "[id].py", 'PAGE_TITLE = "Blog Post"\n')
    _write(tmp_path / "pages" / "docs" / "[...slug].py", 'PAGE_TITLE = "Docs"\n')
    _write(tmp_path / "pages" / "404.py", 'PAGE_TITLE = "Not Found"\n')
    _write(tmp_path / "pages" / "403.py", 'PAGE_TITLE = "Forbidden"\n')
    _write(tmp_path / "pages" / "_draft.py", "PAGE_TITLE = 'Draft'\n")
    _write(tmp_path / "pages" / "__init__.py", "")

    pages = discover_pages(entry_path)
    visible = visible_pages(pages)

    assert [page.url_path for page in visible] == ["", "admin", "admin/users", "status_feedback"]
    assert pages[0].default is True
    blog_page = next(page for page in pages if page.filename == "[id]")
    docs_page = next(page for page in pages if page.filename == "[...slug]")
    admin_page = next(page for page in pages if page.url_path == "admin/users")
    admin_index = next(page for page in pages if page.url_path == "admin")
    not_found = next(page for page in pages if page.not_found)
    forbidden = next(page for page in pages if page.forbidden)

    assert blog_page.hidden is True
    assert blog_page.dynamic is True
    assert docs_page.catch_all is True
    assert admin_page.guard.roles == ("admin",)
    assert [path.relative_to(tmp_path / "layouts").as_posix() for path in admin_page.layout_paths] == [
        "default.py",
        "admin.py",
        "admin/default.py",
    ]
    assert admin_index.title == "Admin"
    assert not_found.hidden is True
    assert forbidden.hidden is True


def test_discover_pages_returns_empty_list_when_pages_directory_is_missing(tmp_path: Path) -> None:
    entry_path = tmp_path / "app.py"
    _write(entry_path, "import fastlit as st\n")

    assert discover_pages(entry_path) == []


def test_discover_pages_uses_cache_until_page_files_change(
    tmp_path: Path, monkeypatch
) -> None:
    clear_discover_pages_cache()
    entry_path = tmp_path / "app.py"
    _write(entry_path, "import fastlit as st\n")
    page_path = tmp_path / "pages" / "about.py"
    _write(page_path, 'PAGE_TITLE = "About"\n')

    calls: list[str] = []
    original = page_discovery.read_page_config

    def wrapped(path: Path):
        calls.append(path.name)
        return original(path)

    monkeypatch.setattr(page_discovery, "read_page_config", wrapped)

    first = discover_pages(entry_path)
    second = discover_pages(entry_path)

    assert len(first) == 1
    assert len(second) == 1
    assert calls == ["about.py"]

    _write(page_path, 'PAGE_TITLE = "About Updated"\n')

    refreshed = discover_pages(entry_path)

    assert calls == ["about.py", "about.py"]
    assert refreshed[0].title == "About Updated"


def test_discover_pages_cache_invalidates_when_layouts_are_added_or_removed(
    tmp_path: Path,
) -> None:
    clear_discover_pages_cache()
    entry_path = tmp_path / "app.py"
    _write(entry_path, "import fastlit as st\n")
    _write(tmp_path / "pages" / "admin" / "users.py", 'PAGE_TITLE = "Users"\n')

    initial = discover_pages(entry_path)
    admin_page = next(page for page in initial if page.url_path == "admin/users")
    assert admin_page.layout_paths == ()

    layout_path = tmp_path / "layouts" / "default.py"
    _write(layout_path, 'import fastlit as st\nst.text("ROOT")\n')

    with_layout = discover_pages(entry_path)
    admin_page = next(page for page in with_layout if page.url_path == "admin/users")
    assert [path.name for path in admin_page.layout_paths] == ["default.py"]

    layout_path.unlink()

    without_layout = discover_pages(entry_path)
    admin_page = next(page for page in without_layout if page.url_path == "admin/users")
    assert admin_page.layout_paths == ()


def test_slugify_page_token_preserves_file_style_names() -> None:
    assert slugify_page_token("Text Elements") == "text-elements"
    assert slugify_page_token("text_elements") == "text_elements"
    assert slugify_page_token("/status-feedback/") == "status-feedback"


def test_resolve_page_supports_dynamic_routes_404_and_guards(tmp_path: Path) -> None:
    entry_path = tmp_path / "app.py"
    _write(entry_path, "import fastlit as st\n")
    _write(tmp_path / "pages" / "index.py", 'PAGE_CONFIG = {"default": True}\n')
    _write(tmp_path / "pages" / "blog" / "[id].py", 'PAGE_TITLE = "Blog Post"\n')
    _write(tmp_path / "pages" / "docs" / "[...slug].py", 'PAGE_TITLE = "Docs"\n')
    _write(tmp_path / "pages" / "admin" / "users.py", 'PAGE_ROLES = ["admin"]\n')
    _write(tmp_path / "pages" / "404.py", 'PAGE_TITLE = "Not Found"\n')
    _write(tmp_path / "pages" / "403.py", 'PAGE_TITLE = "Forbidden"\n')

    pages = discover_pages(entry_path)

    home = resolve_page(pages, "/")
    home_alias = resolve_page(pages, "/index")
    blog = resolve_page(pages, "/blog/42")
    docs = resolve_page(pages, "/docs/guides/routing")
    missing = resolve_page(pages, "/missing/path")
    forbidden = resolve_page(pages, "/admin/users", user_claims={"roles": ["editor"]})
    allowed = resolve_page(pages, "/admin/users", user_claims={"roles": ["admin"]})

    assert home is not None
    assert home.page.url_path == ""

    assert home_alias is not None
    assert home_alias.page.url_path == ""

    assert blog is not None
    assert blog.page.url_path == "blog/[id]"
    assert blog.params == {"id": "42"}

    assert docs is not None
    assert docs.page.url_path == "docs/[...slug]"
    assert docs.params == {"slug": ["guides", "routing"]}

    assert missing is not None
    assert missing.page.not_found is True

    assert forbidden is not None
    assert forbidden.page.forbidden is True
    assert forbidden.guard_failure == "roles"

    assert allowed is not None
    assert allowed.page.url_path == "admin/users"


def test_build_navigation_items_groups_nested_pages_for_sidebar(tmp_path: Path) -> None:
    entry_path = tmp_path / "app.py"
    _write(entry_path, "import fastlit as st\n")
    _write(tmp_path / "pages" / "index.py", 'PAGE_CONFIG = {"title": "Home", "default": True}\n')
    _write(tmp_path / "pages" / "admin" / "index.py", 'PAGE_TITLE = "Admin"\n')
    _write(tmp_path / "pages" / "admin" / "users.py", 'PAGE_TITLE = "Users"\n')
    _write(tmp_path / "pages" / "admin" / "settings.py", 'PAGE_TITLE = "Settings"\n')
    _write(tmp_path / "pages" / "guides" / "install.py", 'PAGE_TITLE = "Install"\n')

    items = build_navigation_items(discover_pages(entry_path))

    assert items[0]["type"] == "page"
    assert items[0]["label"] == "Home"
    assert items[1]["type"] == "group"
    assert items[1]["label"] == "Admin"
    assert items[1]["pageIndex"] == 1
    assert items[1]["urlPath"] == "admin"
    assert [child["label"] for child in items[1]["children"]] == ["Settings", "Users"]
    assert items[2]["type"] == "group"
    assert items[2]["path"] == "guides"


def test_page_path_and_switch_page_support_dynamic_routes() -> None:
    assert page_path("/") == "/"
    assert page_path("blog/[id]", id=42) == "/blog/42"
    assert page_path("pages/admin/index.py") == "/admin"
    assert page_path("pages/docs/[...slug].py", slug=["guides", "routing"]) == "/docs/guides/routing"

    try:
        switch_page("pages/blog/[id].py", id=7)
    except SwitchPageException as exc:
        assert exc.page_name == "/blog/7"
    else:
        raise AssertionError("switch_page() should raise SwitchPageException")


def test_explicit_navigation_preserves_empty_root_url_path(tmp_path: Path) -> None:
    entry_path = tmp_path / "app.py"
    _write(
        entry_path,
        """
import fastlit as st

st.navigation([
    st.Page("pages/index.py", title="Home", url_path="", default=True),
    st.Page("pages/about.py", title="About", url_path="about"),
])
""".strip(),
    )
    _write(tmp_path / "pages" / "index.py", 'import fastlit as st\nst.text("HOME")\n')
    _write(tmp_path / "pages" / "about.py", 'import fastlit as st\nst.text("ABOUT")\n')

    session = Session(str(entry_path))
    session.run()

    assert session._page_url_paths == ["", "about"]


def test_page_run_renders_selected_page_inside_global_layout(tmp_path: Path) -> None:
    entry_path = tmp_path / "app.py"
    _write(
        entry_path,
        """
import fastlit as st

page = st.navigation([
    st.Page("pages/index.py", title="Home", default=True),
    st.Page("pages/about.py", title="About"),
])
st.text("before")
page.run()
st.text("after")
""".strip(),
    )
    _write(tmp_path / "pages" / "index.py", 'import fastlit as st\nst.text("HOME")\n')
    _write(tmp_path / "pages" / "about.py", 'import fastlit as st\nst.text("ABOUT")\n')

    session = Session(str(entry_path))
    result = session.run()

    texts = [
        child["props"].get("text")
        for child in result.tree["children"]
        if child["type"] == "text"
    ]
    assert texts == ["before", "HOME", "after"]
    assert session.script_path == str(entry_path)


def test_auto_discovered_pages_render_implicitly_inside_entry_layout(tmp_path: Path) -> None:
    entry_path = tmp_path / "app.py"
    _write(
        entry_path,
        """
import fastlit as st

st.sidebar.navigation()
st.text("AFTER")
""".strip(),
    )
    _write(
        tmp_path / "pages" / "index.py",
        """
import fastlit as st

PAGE_CONFIG = {"title": "Home", "default": True}
st.text("HOME")
""".strip(),
    )

    session = Session(str(entry_path))
    result = session.run()

    texts = [
        child["props"].get("text")
        for child in result.tree["children"]
        if child["type"] == "text"
    ]
    assert texts == ["HOME", "AFTER"]
    assert session.script_path == str(entry_path)


def test_nested_layouts_render_around_selected_page(tmp_path: Path) -> None:
    entry_path = tmp_path / "app.py"
    _write(
        entry_path,
        """
import fastlit as st

st.sidebar.navigation()
""".strip(),
    )
    _write(
        tmp_path / "layouts" / "admin.py",
        """
import fastlit as st

st.text("ADMIN HEADER")
st.page_outlet()
st.text("ADMIN FOOTER")
""".strip(),
    )
    _write(
        tmp_path / "pages" / "admin" / "users.py",
        """
import fastlit as st

PAGE_CONFIG = {"title": "Users", "default": True}
st.text("USERS PAGE")
""".strip(),
    )

    session = Session(str(entry_path))
    session.set_current_path("/admin/users")
    result = session.run()

    texts = [
        child["props"].get("text")
        for child in result.tree["children"]
        if child["type"] == "text"
    ]
    assert texts == ["ADMIN HEADER", "USERS PAGE", "ADMIN FOOTER"]
    assert session.layout_stack
    assert session.route_path == "admin/users"
    assert session.script_path == str(entry_path)


def test_nested_default_layouts_render_for_deeper_sections(tmp_path: Path) -> None:
    entry_path = tmp_path / "app.py"
    _write(
        entry_path,
        """
import fastlit as st

st.sidebar.navigation()
""".strip(),
    )
    _write(
        tmp_path / "layouts" / "default.py",
        """
import fastlit as st

st.text("ROOT")
st.page_outlet()
""".strip(),
    )
    _write(
        tmp_path / "layouts" / "admin" / "default.py",
        """
import fastlit as st

st.text("ADMIN DEFAULT")
st.page_outlet()
""".strip(),
    )
    _write(
        tmp_path / "layouts" / "admin" / "reports.py",
        """
import fastlit as st

st.text("REPORTS")
st.page_outlet()
""".strip(),
    )
    _write(
        tmp_path / "pages" / "admin" / "reports" / "monthly.py",
        """
import fastlit as st

PAGE_CONFIG = {"title": "Monthly", "default": True}
st.text("MONTHLY PAGE")
""".strip(),
    )

    session = Session(str(entry_path))
    session.set_current_path("/admin/reports/monthly")
    result = session.run()

    texts = [
        child["props"].get("text")
        for child in result.tree["children"]
        if child["type"] == "text"
    ]
    assert texts == ["ROOT", "ADMIN DEFAULT", "REPORTS", "MONTHLY PAGE"]


def test_navigation_without_page_run_keeps_legacy_page_switching(tmp_path: Path) -> None:
    entry_path = tmp_path / "app.py"
    _write(
        entry_path,
        """
import fastlit as st

st.navigation([
    st.Page("pages/index.py", title="Home", default=True),
    st.Page("pages/about.py", title="About"),
])
st.text("layout-only")
""".strip(),
    )
    _write(tmp_path / "pages" / "index.py", 'import fastlit as st\nst.text("HOME")\n')
    _write(tmp_path / "pages" / "about.py", 'import fastlit as st\nst.text("ABOUT")\n')

    session = Session(str(entry_path))
    result = session.run()

    texts = [
        child["props"].get("text")
        for child in result.tree["children"]
        if child["type"] == "text"
    ]
    assert texts == ["HOME"]
    assert session.script_path.endswith("index.py")


def test_require_login_in_file_based_page_requests_browser_redirect(tmp_path: Path) -> None:
    entry_path = tmp_path / "app.py"
    _write(
        entry_path,
        """
import fastlit as st

st.sidebar.navigation()
""".strip(),
    )
    _write(
        tmp_path / "pages" / "index.py",
        """
import fastlit as st

PAGE_CONFIG = {"default": True}
st.require_login()
st.text("SECRET")
""".strip(),
    )

    session = Session(str(entry_path))
    session.run()

    assert session.consume_pending_browser_redirect() == "/auth/login"


def test_page_discovery_cache_hit_is_fast(tmp_path: Path) -> None:
    """discover_pages() on a warm cache must complete significantly faster than cold."""
    import time

    clear_discover_pages_cache()
    entry_path = tmp_path / "app.py"
    _write(entry_path, "import fastlit as st\n")

    pages_dir = tmp_path / "pages"
    pages_dir.mkdir()
    for i in range(50):
        _write(
            pages_dir / f"page_{i:03d}.py",
            f'"""Page {i}."""\nimport fastlit as st\n',
        )

    # Cold call to populate cache (first discovery requires reading files)
    t_cold = time.perf_counter()
    discover_pages(str(entry_path))
    cold_time = (time.perf_counter() - t_cold) * 1000

    # Warm call — must use cached result and be much faster than cold
    t0 = time.perf_counter()
    for _ in range(20):
        discover_pages(str(entry_path))
    avg_warm_time = (time.perf_counter() - t0) / 20 * 1000

    # Cache hit should be at least 2x faster than cold call
    assert avg_warm_time < cold_time / 2, (
        f"discover_pages cache hit took {avg_warm_time:.2f}ms, "
        f"but cold call took {cold_time:.2f}ms — cache not effective"
    )
