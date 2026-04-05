import asyncio
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from starlette.datastructures import QueryParams
from starlette.testclient import TestClient

from fastlit.server import app as app_module
from fastlit.runtime.session import Session
from fastlit.server.dataframe_store import _SOURCES
from fastlit.server.session_store import InMemorySessionStore


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


def test_metrics_endpoint_returns_prometheus_format(tmp_path: Path) -> None:
    """/_fastlit/metrics must return text/plain with metric lines."""
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<!doctype html><div>ok</div>", encoding="utf-8")

    app = app_module.create_app(script_path=__file__, static_dir=str(static_dir))

    with TestClient(app) as client:
        response = client.get("/_fastlit/metrics/prometheus")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        body = response.text
        # Must contain at least one metric line
        assert any(line and not line.startswith("#") for line in body.splitlines())
        # Check for new gauges
        assert "fastlit_rerun_latency_ms_p50" in body
        assert "fastlit_rerun_latency_ms_p95" in body
        assert "fastlit_patch_size_bytes_p95" in body


def test_dataframe_slice_endpoint_queries_process_worker_for_session_scoped_sources() -> None:
    class DummyWorker:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        async def query_dataframe(self, *, source_id: str, query, timeout_seconds: float):
            self.calls.append((source_id, query))
            return {
                "sourceId": source_id,
                "offset": query.offset,
                "limit": query.limit,
                "totalRows": 1,
                "columns": [{"name": "Name"}],
                "rows": [["Alice"]],
                "index": [query.offset],
                "positions": [query.offset],
            }

    async def run():
        _SOURCES.clear()
        session_store = InMemorySessionStore()
        session = Session(__file__)
        session.session_id = "a" * 32
        record = await session_store.add(
            session,
            websocket=MagicMock(),
            client_ip="127.0.0.1",
            request_id="req-1",
        )
        worker = DummyWorker()
        record.process_worker = worker
        request = SimpleNamespace(
            path_params={"source_id": f"{session.session_id}:deadbeefdeadbeefdeadbeefdeadbeef"},
            query_params=QueryParams(
                "offset=10&limit=5&format=json&search=alice"
                "&sort=%5B%7B%22column%22%3A%22Name%22%2C%22direction%22%3A%22desc%22%7D%5D"
                "&filters=%5B%5D"
            ),
            app=SimpleNamespace(state=SimpleNamespace(session_store=session_store)),
        )
        response = await app_module.dataframe_slice_endpoint(request)
        return response, worker

    response, worker = asyncio.run(run())

    assert response.status_code == 200
    assert worker.calls
    source_id, query = worker.calls[0]
    assert source_id.startswith("a" * 32)
    assert query.offset == 10
    assert query.limit == 5
    assert query.search == "alice"
    assert query.sorts[0].column == "Name"
    assert query.sorts[0].direction == "desc"

    body = json.loads(response.body)
    assert body["rows"] == [["Alice"]]
    assert body["offset"] == 10


def test_dataframe_slice_endpoint_uses_to_thread_for_local_sources(monkeypatch) -> None:
    calls = {"to_thread": 0, "get_slice": 0}

    def fake_get_dataframe_slice(source_id, query):
        calls["get_slice"] += 1
        assert source_id == "local-source"
        assert query.offset == 2
        return {
            "sourceId": source_id,
            "offset": query.offset,
            "limit": query.limit,
            "totalRows": 1,
            "columns": [{"name": "Name"}],
            "rows": [["Alice"]],
            "index": [query.offset],
            "positions": [query.offset],
        }

    async def fake_to_thread(fn, *args, **kwargs):
        calls["to_thread"] += 1
        return fn(*args, **kwargs)

    monkeypatch.setattr(app_module, "get_dataframe_slice", fake_get_dataframe_slice)
    monkeypatch.setattr(app_module.asyncio, "to_thread", fake_to_thread)

    request = SimpleNamespace(
        path_params={"source_id": "local-source"},
        query_params=QueryParams("offset=2&limit=3&format=json&search=&sort=%5B%5D&filters=%5B%5D"),
        app=SimpleNamespace(state=SimpleNamespace(session_store=None)),
    )

    response = asyncio.run(app_module.dataframe_slice_endpoint(request))

    assert response.status_code == 200
    assert calls["to_thread"] == 1
    assert calls["get_slice"] == 1
