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


def test_send_payload_raises_websocket_closed_error_after_close() -> None:
    class DummyWebSocket:
        application_state = None
        client_state = None

        async def send_text(self, _body: str) -> None:
            raise RuntimeError(
                "Unexpected ASGI message 'websocket.send', after sending "
                "'websocket.close' or response already completed."
            )

    websocket = DummyWebSocket()

    with pytest.raises(websocket_handler._WebSocketClosedError):
        asyncio.run(
            websocket_handler._send_payload(
                websocket,
                {"type": "error", "message": "closed"},
            )
        )


def test_hydrate_deferred_fragments_ignores_closed_socket_during_timeout_notification(monkeypatch) -> None:
    class RenderResult:
        def to_dict(self) -> dict:
            return {"type": "render_patch", "rev": 1, "ops": []}

    async def fake_run_session_op_with_runtime_events(*args, **kwargs):
        return RenderResult()

    async def fake_send_pending_redirect(*args, **kwargs) -> bool:
        return False

    async def fake_enforce_tree_limit(*args, **kwargs) -> bool:
        return True

    async def fake_drain_deferred_streams(*args, **kwargs) -> None:
        raise asyncio.TimeoutError()

    send_calls = {"count": 0}

    async def fake_send_payload(*args, **kwargs) -> None:
        send_calls["count"] += 1
        if send_calls["count"] >= 2:
            raise websocket_handler._WebSocketClosedError("closed")

    monkeypatch.setattr(
        websocket_handler,
        "_run_session_op_with_runtime_events",
        fake_run_session_op_with_runtime_events,
    )
    monkeypatch.setattr(websocket_handler, "_send_pending_redirect", fake_send_pending_redirect)
    monkeypatch.setattr(websocket_handler, "_enforce_tree_limit", fake_enforce_tree_limit)
    monkeypatch.setattr(websocket_handler, "_drain_deferred_streams", fake_drain_deferred_streams)
    monkeypatch.setattr(websocket_handler, "_send_payload", fake_send_payload)

    session = Session(__file__)
    session.get_deferred_fragment_snapshot = lambda: (0, [])  # type: ignore[method-assign]

    async def run() -> None:
        await websocket_handler._hydrate_deferred_fragments(
            ["frag-1"],
            expected_epoch=0,
            session=session,
            websocket=SimpleNamespace(),
            node_cache={},
            session_lock=asyncio.Lock(),
            session_store=SimpleNamespace(),
            session_record=None,
            fragment_timers={},
            deferred_fragment_tasks=set(),
            runtime_state=None,
        )

    asyncio.run(run())
    assert send_calls["count"] == 2


def test_finalize_background_task_discards_and_consumes_exception() -> None:
    async def fail() -> None:
        raise websocket_handler._WebSocketClosedError("closed")

    async def run() -> None:
        task = asyncio.create_task(fail())
        tracked = {task}
        await asyncio.sleep(0)
        websocket_handler._finalize_background_task(
            task,
            tasks=tracked,
            label="test-task",
        )
        assert not tracked

    asyncio.run(run())


def test_optimize_patch_payload_returns_preserialized_always() -> None:
    """For render_patch with >= 48 ops, must always return a pre-serialized string
    so _send_payload never has to re-serialize the compact payload."""
    payload = {
        "type": "render_patch",
        "rev": 1,
        "ops": [{"op": "updateProps", "id": f"n{i}", "props": {"v": i}} for i in range(50)],
    }
    node_cache: dict = {}

    _, pre_serialized, pre_serialized_size = _optimize_patch_payload(
        payload,
        node_cache=node_cache,
    )

    assert pre_serialized is not None, (
        "_optimize_patch_payload must return pre-serialized text for large patches "
        "to avoid double serialization in _send_payload"
    )
    assert isinstance(pre_serialized, str)
    assert isinstance(pre_serialized_size, int)
    assert "render_patch_compact" in pre_serialized


def test_optimize_patch_payload_compressed_path_returns_preserialized() -> None:
    """When zlib compression is used, pre_serialized must still be a string."""
    import fastlit.server.websocket_handler as ws_mod
    from fastlit.server.websocket_handler import _optimize_patch_payload

    # Build a payload large enough to trigger compression at threshold=0
    large_ops = [
        {
            "op": "insertChild",
            "id": f"n{i}",
            "parentId": "root",
            "index": i,
            "node": {"type": "text", "id": f"n{i}", "props": {"text": "x" * 50}, "children": []},
        }
        for i in range(60)
    ]
    payload = {"type": "render_patch", "rev": 1, "ops": large_ops}

    original_min = ws_mod._PATCH_COMPRESS_MIN_BYTES
    original_zlib = ws_mod._PATCH_ENABLE_ZLIB
    try:
        ws_mod._PATCH_COMPRESS_MIN_BYTES = 0  # Force compression for any size
        ws_mod._PATCH_ENABLE_ZLIB = True
        result_payload, pre_serialized, pre_serialized_size = _optimize_patch_payload(
            payload,
            node_cache={},
        )
    finally:
        ws_mod._PATCH_COMPRESS_MIN_BYTES = original_min
        ws_mod._PATCH_ENABLE_ZLIB = original_zlib

    # Whether compressed or not (depends on actual size), pre_serialized must be non-None
    assert pre_serialized is not None, (
        "All paths in _optimize_patch_payload must return pre-serialized text"
    )
    assert isinstance(pre_serialized, str)
    assert isinstance(pre_serialized_size, int)
    # If the compressed path was taken, verify the envelope structure
    if result_payload.get("type") == "render_patch_z":
        assert result_payload["encoding"] == "zlib+base64"
        import base64
        import zlib as _zlib
        raw = base64.b64decode(result_payload["ops"])
        decompressed = _zlib.decompress(raw)
        assert b"render_patch_compact" in decompressed


def test_node_cache_can_be_cleared_after_session() -> None:
    """node_cache must be clearable to prevent memory leaks on disconnect."""
    from fastlit.server.websocket_handler import _optimize_patch_payload

    node_cache: dict = {}
    # Populate the cache with some node definitions
    payload = {
        "type": "render_patch",
        "rev": 1,
        "ops": [
            {
                "op": "insertChild",
                "id": f"n{i}",
                "parentId": "root",
                "index": i,
                "node": {
                    "type": "text",
                    "id": f"n{i}",
                    "props": {"text": f"item {i}"},
                    "children": [],
                },
            }
            for i in range(50)
        ],
    }
    _optimize_patch_payload(payload, node_cache=node_cache)
    assert len(node_cache) > 0, "node_cache should have been populated"

    # Simulating session end: cache must be clearable
    node_cache.clear()
    assert len(node_cache) == 0, "node_cache must be empty after disconnect cleanup"


def test_optimize_patch_payload_bounds_node_cache(monkeypatch) -> None:
    monkeypatch.setattr(websocket_handler, "_NODE_CACHE_LIMIT", 2)
    payload = {
        "type": "render_patch",
        "rev": 1,
        "ops": [
            {
                "op": "insertChild",
                "id": f"n{i}",
                "parentId": "root",
                "index": i,
                "node": {
                    "type": "text",
                    "id": f"n{i}",
                    "props": {"text": f"item {i}"},
                    "children": [],
                },
            }
            for i in range(50)
        ],
    }

    node_cache: dict[str, dict] = {}
    _optimize_patch_payload(payload, node_cache=node_cache)

    assert len(node_cache) == 2


def test_coalesce_events_reports_eof_without_losing_batch() -> None:
    queue: asyncio.Queue[websocket_handler.WidgetEvent | None] = asyncio.Queue()
    first_event = websocket_handler.WidgetEvent(id="a", value=1)
    queue.put_nowait(websocket_handler.WidgetEvent(id="b", value=2))
    queue.put_nowait(None)

    batch, saw_eof = websocket_handler._coalesce_events(
        first_event,
        queue,
        batch_limit=10,
    )

    assert saw_eof is True
    assert [event.id for event in batch] == ["a", "b"]


def test_queue_disconnect_sentinel_has_priority_when_queue_is_full() -> None:
    queue: asyncio.Queue[websocket_handler.WidgetEvent | None] = asyncio.Queue(maxsize=1)
    queue.put_nowait(websocket_handler.WidgetEvent(id="a", value=1))

    websocket_handler._queue_disconnect_sentinel(queue)

    assert queue.get_nowait() is None
