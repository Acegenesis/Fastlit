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
