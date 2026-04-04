import asyncio
import json
from types import SimpleNamespace

import pytest
from starlette.datastructures import Headers, QueryParams

from fastlit.runtime.session import Session
from fastlit.server import websocket_handler
from fastlit.server.websocket_handler import _optimize_patch_payload


def test_websocket_rate_limit_defaults_to_50_events_per_second() -> None:
    assert websocket_handler._WS_MAX_EVENTS_PER_SECOND == 50


def test_page_navigation_reruns_use_plain_patches_without_force_full() -> None:
    session = Session(__file__)
    session._page_nav_id = "k:nav"

    force_full_render, progressive = websocket_handler._render_flags_for_event_batch(
        session,
        ["k:nav"],
    )

    assert force_full_render is False
    assert progressive is False


def test_session_limits_enforce_total_memory_budget(monkeypatch) -> None:
    monkeypatch.setattr(websocket_handler, "_MAX_WIDGET_STORE_BYTES", 0)
    monkeypatch.setattr(websocket_handler, "_MAX_SESSION_STATE_BYTES", 0)
    monkeypatch.setattr(websocket_handler, "_MAX_SESSION_MEMORY_BYTES", 32)

    session = Session(__file__)
    session.widget_store["payload"] = "x" * 128

    ok, reason = websocket_handler._session_limits_ok(session)

    assert ok is False
    assert "Session memory limit exceeded" in (reason or "")


def test_extract_ws_token_decodes_cookie_value() -> None:
    websocket = SimpleNamespace(
        query_params=QueryParams(""),
        headers=Headers({"cookie": "fastlit_ws_token=abc%2B123%3D"}),
    )

    token = websocket_handler._extract_ws_token(websocket)

    assert token == "abc+123="


def test_serialize_payload_rejects_unsupported_types() -> None:
    class Unsupported:
        pass

    with pytest.raises(websocket_handler._PayloadSerializationError):
        websocket_handler._serialize_payload(
            {"type": "render_full", "tree": {"id": "root", "bad": Unsupported()}}
        )


def test_send_payload_sends_safe_error_on_serialization_failure() -> None:
    class Unsupported:
        pass

    class DummyWebSocket:
        def __init__(self) -> None:
            self.sent: list[str] = []

        async def send_text(self, body: str) -> None:
            self.sent.append(body)

    websocket = DummyWebSocket()

    with pytest.raises(websocket_handler._PayloadSerializationError):
        asyncio.run(
            websocket_handler._send_payload(
                websocket,
                {"type": "render_full", "tree": {"id": "root", "bad": Unsupported()}},
            )
        )

    assert len(websocket.sent) == 1
    assert json.loads(websocket.sent[0]) == {
        "type": "error",
        "message": "An internal serialization error occurred.",
    }


def test_optimize_patch_payload_returns_preserialized_always() -> None:
    """For render_patch with >= 48 ops, must always return a pre-serialized string
    so _send_payload never has to re-serialize the compact payload."""
    payload = {
        "type": "render_patch",
        "rev": 1,
        "ops": [{"op": "updateProps", "id": f"n{i}", "props": {"v": i}} for i in range(50)],
    }
    node_cache: dict = {}

    _, pre_serialized = _optimize_patch_payload(payload, node_cache=node_cache)

    assert pre_serialized is not None, (
        "_optimize_patch_payload must return pre-serialized text for large patches "
        "to avoid double serialization in _send_payload"
    )
    assert isinstance(pre_serialized, str)
    assert "render_patch_compact" in pre_serialized
