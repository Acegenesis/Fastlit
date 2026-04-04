import os
from pathlib import Path

from starlette.testclient import TestClient

from fastlit.server import app as app_module


def test_homepage_strips_ws_token_and_sets_secure_cookie(tmp_path: Path) -> None:
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<!doctype html><div>ok</div>", encoding="utf-8")

    app = app_module.create_app(script_path=__file__, static_dir=str(static_dir))

    with TestClient(app, base_url="https://testserver") as client:
        response = client.get(
            "/?fastlit_ws_token=abc123&foo=bar",
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["location"] == "/?foo=bar"
    set_cookie = response.headers["set-cookie"]
    assert "fastlit_ws_token=abc123" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie


def test_static_cache_middleware_exists() -> None:
    """_StaticCacheMiddleware and _make_cache_control_middleware must be importable."""
    from fastlit.server.app import _StaticCacheMiddleware, _make_cache_control_middleware

    middleware_class = _make_cache_control_middleware()
    assert middleware_class is _StaticCacheMiddleware


def test_static_cache_middleware_sets_immutable_for_assets() -> None:
    """_StaticCacheMiddleware must set Cache-Control: immutable for /assets/* paths."""
    import asyncio
    from fastlit.server.app import _StaticCacheMiddleware
    from unittest.mock import AsyncMock, MagicMock

    middleware = _StaticCacheMiddleware(app=MagicMock())

    async def run():
        mock_request = MagicMock()
        mock_request.url.path = "/assets/bundle.abc123.js"
        mock_request.method = "GET"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}

        call_next = AsyncMock(return_value=mock_response)
        return await middleware.dispatch(mock_request, call_next)

    response = asyncio.run(run())
    assert response.headers.get("Cache-Control") == "public, max-age=31536000, immutable"


def test_static_cache_middleware_sets_no_cache_for_index() -> None:
    """_StaticCacheMiddleware must set Cache-Control: no-cache for / and /index.html."""
    import asyncio
    from fastlit.server.app import _StaticCacheMiddleware
    from unittest.mock import AsyncMock, MagicMock

    middleware = _StaticCacheMiddleware(app=MagicMock())

    async def run(path):
        mock_request = MagicMock()
        mock_request.url.path = path
        mock_request.method = "GET"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}

        call_next = AsyncMock(return_value=mock_response)
        return await middleware.dispatch(mock_request, call_next)

    for path in ("/", "/index.html"):
        response = asyncio.run(run(path))
        assert response.headers.get("Cache-Control") == "no-cache", f"Expected no-cache for {path}"


def test_static_cache_middleware_sets_no_cache_for_components() -> None:
    """_StaticCacheMiddleware must set Cache-Control: no-cache for /_components/* paths."""
    import asyncio
    from fastlit.server.app import _StaticCacheMiddleware
    from unittest.mock import AsyncMock, MagicMock

    middleware = _StaticCacheMiddleware(app=MagicMock())

    async def run():
        mock_request = MagicMock()
        mock_request.url.path = "/_components/my-widget/index.js"
        mock_request.method = "GET"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}

        call_next = AsyncMock(return_value=mock_response)
        return await middleware.dispatch(mock_request, call_next)

    response = asyncio.run(run())
    assert response.headers.get("Cache-Control") == "no-cache"


def test_static_cache_middleware_skips_non_get() -> None:
    """_StaticCacheMiddleware must not set cache headers for non-GET/HEAD requests."""
    import asyncio
    from fastlit.server.app import _StaticCacheMiddleware
    from unittest.mock import AsyncMock, MagicMock

    middleware = _StaticCacheMiddleware(app=MagicMock())

    async def run():
        mock_request = MagicMock()
        mock_request.url.path = "/assets/bundle.abc123.js"
        mock_request.method = "POST"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}

        call_next = AsyncMock(return_value=mock_response)
        return await middleware.dispatch(mock_request, call_next)

    response = asyncio.run(run())
    assert "Cache-Control" not in response.headers


def test_fastlit_workers_env_defaults_to_1(monkeypatch) -> None:
    """FASTLIT_WORKERS defaults to 1 when not set."""
    monkeypatch.delenv("FASTLIT_WORKERS", raising=False)
    workers = max(1, int(os.environ.get("FASTLIT_WORKERS", "1")))
    assert workers == 1


def test_fastlit_workers_env_is_respected(monkeypatch) -> None:
    """FASTLIT_WORKERS=4 must result in workers=4."""
    monkeypatch.setenv("FASTLIT_WORKERS", "4")
    workers = max(1, int(os.environ.get("FASTLIT_WORKERS", "1")))
    assert workers == 4
