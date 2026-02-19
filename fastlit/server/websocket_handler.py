"""WebSocket handler: manages the lifecycle of a client connection."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import time
import traceback
import zlib
from concurrent.futures import ThreadPoolExecutor

from starlette.websockets import WebSocket, WebSocketDisconnect

from fastlit.runtime.protocol import WidgetEvent
from fastlit.runtime.session import Session
from fastlit.server import metrics

try:
    import orjson  # type: ignore
except ImportError:  # pragma: no cover
    orjson = None

logger = logging.getLogger("fastlit.ws")

_MAX_QUERY_PARAMS = 64
_MAX_QUERY_KEY_LEN = 128
_MAX_QUERY_VAL_LEN = 2048
_MAX_WIDGET_ID_LEN = 512
_MAX_WS_MESSAGE_BYTES = int(
    os.environ.get("FASTLIT_MAX_WS_MESSAGE_BYTES", str(16 * 1024 * 1024))
)
_MAX_SESSIONS = int(os.environ.get("FASTLIT_MAX_SESSIONS", "0"))  # 0 = unlimited
_MAX_CONCURRENT_RUNS = max(1, int(os.environ.get("FASTLIT_MAX_CONCURRENT_RUNS", "4")))
_RUN_TIMEOUT_SECONDS = float(os.environ.get("FASTLIT_RUN_TIMEOUT_SECONDS", "60"))
_WS_EVENT_QUEUE_SIZE = max(8, int(os.environ.get("FASTLIT_WS_EVENT_QUEUE_SIZE", "256")))
_WS_COALESCE_WINDOW_MS = max(
    0.0, float(os.environ.get("FASTLIT_WS_COALESCE_WINDOW_MS", "10"))
)
_WS_BATCH_LIMIT = max(1, int(os.environ.get("FASTLIT_WS_BATCH_LIMIT", "256")))
_PATCH_COMPACT_MIN_OPS = max(
    8, int(os.environ.get("FASTLIT_PATCH_COMPACT_MIN_OPS", "48"))
)
_PATCH_COMPRESS_MIN_BYTES = max(
    4096, int(os.environ.get("FASTLIT_PATCH_COMPRESS_MIN_BYTES", "32768"))
)
_PATCH_ENABLE_ZLIB = os.environ.get("FASTLIT_PATCH_ENABLE_ZLIB", "0").strip() in {
    "1",
    "true",
    "yes",
    "on",
}
_MAX_WIDGET_STORE_BYTES = max(
    0, int(os.environ.get("FASTLIT_MAX_WIDGET_STORE_BYTES", str(8 * 1024 * 1024)))
)
_MAX_SESSION_STATE_BYTES = max(
    0, int(os.environ.get("FASTLIT_MAX_SESSION_STATE_BYTES", str(8 * 1024 * 1024)))
)
_MAX_TREE_NODES = max(0, int(os.environ.get("FASTLIT_MAX_TREE_NODES", "200000")))

_RUN_EXECUTOR = ThreadPoolExecutor(max_workers=_MAX_CONCURRENT_RUNS)
_RUN_SEMAPHORE = asyncio.Semaphore(_MAX_CONCURRENT_RUNS)
_SESSIONS_LOCK = asyncio.Lock()
_ACTIVE_SESSIONS: set[str] = set()


def _json_loads(raw: str):
    if orjson is not None:
        return orjson.loads(raw)
    return json.loads(raw)


def _serialize_payload(payload: dict) -> tuple[str, int]:
    if orjson is not None:
        body = orjson.dumps(payload)
        return body.decode("utf-8"), len(body)
    text = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return text, len(text.encode("utf-8"))


def _node_token(node: dict) -> str:
    if orjson is not None:
        raw = orjson.dumps(node)
    else:
        raw = json.dumps(node, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


async def _send_payload(
    websocket: WebSocket,
    payload: dict,
    *,
    node_cache: dict[str, dict] | None = None,
) -> None:
    payload, pre_serialized = _optimize_patch_payload(payload, node_cache=node_cache)
    if pre_serialized is not None:
        body = pre_serialized
        size_bytes = len(body.encode("utf-8"))
    else:
        body, size_bytes = _serialize_payload(payload)
    metrics.record_outbound_message(size_bytes=size_bytes, message_type=payload.get("type"))
    await websocket.send_text(body)


def _optimize_patch_payload(
    payload: dict,
    *,
    node_cache: dict[str, dict] | None = None,
) -> tuple[dict, str | None]:
    """Batch/compact heavy patch payloads to reduce WS transfer overhead."""
    if payload.get("type") != "render_patch":
        return payload, None

    ops = payload.get("ops")
    if not isinstance(ops, list) or len(ops) < _PATCH_COMPACT_MIN_OPS:
        return payload, None

    compact_ops = []
    for op in ops:
        node_val = op.get("node")
        compact_node = node_val
        if isinstance(node_val, dict) and node_cache is not None:
            token = _node_token(node_val)
            if token in node_cache:
                compact_node = {"$ref": token}
            else:
                node_cache[token] = node_val
                compact_node = {"$def": [token, node_val]}

        compact_ops.append(
            [
                op.get("op"),
                op.get("id"),
                op.get("parentId"),
                op.get("index"),
                op.get("props"),
                compact_node,
            ]
        )

    compact_payload = {
        "type": "render_patch_compact",
        "rev": payload.get("rev"),
        "ops": compact_ops,
    }

    # Optional second step: compress compact payload when still very large.
    if not _PATCH_ENABLE_ZLIB:
        return compact_payload, None

    compact_text, compact_size = _serialize_payload(compact_payload)
    if compact_size < _PATCH_COMPRESS_MIN_BYTES:
        return compact_payload, compact_text

    compressed = zlib.compress(compact_text.encode("utf-8"), level=6)
    if len(compressed) + 64 >= compact_size:
        return compact_payload, compact_text

    return ({
        "type": "render_patch_z",
        "rev": payload.get("rev"),
        "encoding": "zlib+base64",
        "ops": base64.b64encode(compressed).decode("ascii"),
    }, None)


def _estimate_json_bytes(obj: object) -> int:
    try:
        if orjson is not None:
            return len(orjson.dumps(obj))
        return len(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"))
    except Exception:
        return 0


def _session_limits_ok(session: Session) -> tuple[bool, str | None]:
    if _MAX_WIDGET_STORE_BYTES > 0:
        widget_bytes = _estimate_json_bytes(session.widget_store)
        if widget_bytes > _MAX_WIDGET_STORE_BYTES:
            return (
                False,
                f"Widget store limit exceeded ({widget_bytes} > {_MAX_WIDGET_STORE_BYTES} bytes)",
            )
    if _MAX_SESSION_STATE_BYTES > 0:
        state_bytes = _estimate_json_bytes(session.session_state)
        if state_bytes > _MAX_SESSION_STATE_BYTES:
            return (
                False,
                f"Session state limit exceeded ({state_bytes} > {_MAX_SESSION_STATE_BYTES} bytes)",
            )
    return True, None


def _count_nodes(tree: dict | None) -> int:
    if not tree:
        return 0
    count = 0
    stack = [tree]
    while stack:
        node = stack.pop()
        count += 1
        children = node.get("children")
        if isinstance(children, list):
            stack.extend(children)
    return count


def _is_origin_allowed(websocket: WebSocket) -> bool:
    """Allow same-origin by default; allow explicit origins via env override."""
    origin = websocket.headers.get("origin")
    if not origin:
        return True

    allowed = os.environ.get("FASTLIT_ALLOWED_ORIGINS", "").strip()
    if allowed:
        allowed_origins = {o.strip() for o in allowed.split(",") if o.strip()}
        return origin in allowed_origins

    host = websocket.headers.get("host")
    if not host:
        return False
    return origin in {f"http://{host}", f"https://{host}"}


def _validate_and_copy_query_params(websocket: WebSocket, session: Session) -> bool:
    """Validate query params shape/size before copying into session."""
    count = 0
    for key, value in websocket.query_params.multi_items():
        count += 1
        if count > _MAX_QUERY_PARAMS:
            return False
        if len(key) > _MAX_QUERY_KEY_LEN or len(value) > _MAX_QUERY_VAL_LEN:
            return False
        session.query_params[key] = value
    return True


def _parse_widget_event(raw: str) -> WidgetEvent | None:
    """Parse and validate widget event payload."""
    if len(raw.encode("utf-8")) > _MAX_WS_MESSAGE_BYTES:
        return None
    try:
        msg = _json_loads(raw)
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(msg, dict):
        return None
    if msg.get("type") != "widget_event":
        return None

    event = WidgetEvent.from_dict(msg)
    if not event.id or len(event.id) > _MAX_WIDGET_ID_LEN:
        return None
    return event


async def _run_in_worker(fn):
    """Run a blocking session operation in a bounded thread pool."""
    async with _RUN_SEMAPHORE:
        loop = asyncio.get_running_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(_RUN_EXECUTOR, fn),
            timeout=_RUN_TIMEOUT_SECONDS,
        )


async def _ws_reader(
    websocket: WebSocket, queue: asyncio.Queue[WidgetEvent | None]
) -> None:
    """Read and validate WS events into a bounded per-session queue."""
    try:
        while True:
            raw = await websocket.receive_text()
            event = _parse_widget_event(raw)
            if event is None:
                logger.warning("Invalid or oversized WebSocket message")
                continue

            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest then enqueue newest (latest value is usually most relevant).
                try:
                    queue.get_nowait()
                    metrics.record_dropped_event(1)
                except asyncio.QueueEmpty:
                    pass

                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    metrics.record_dropped_event(1)
    except WebSocketDisconnect:
        pass
    finally:
        try:
            queue.put_nowait(None)
        except asyncio.QueueFull:
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                queue.put_nowait(None)
            except asyncio.QueueFull:
                pass


def _coalesce_events(
    first_event: WidgetEvent,
    queue: asyncio.Queue[WidgetEvent | None],
    *,
    batch_limit: int,
) -> list[WidgetEvent]:
    """Drain currently available events and keep the latest value per widget."""
    merged: dict[str, WidgetEvent] = {first_event.id: first_event}
    drained = 0

    while drained < max(0, batch_limit - 1):
        try:
            ev = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        if ev is None:
            break
        merged[ev.id] = ev
        drained += 1

    return list(merged.values())


async def handle_websocket(websocket: WebSocket, script_path: str) -> None:
    """Handle a single WebSocket connection."""
    if not _is_origin_allowed(websocket):
        await websocket.close(code=1008, reason="WebSocket origin not allowed")
        return

    session = Session(script_path)
    admitted = False

    async with _SESSIONS_LOCK:
        if _MAX_SESSIONS > 0 and len(_ACTIVE_SESSIONS) >= _MAX_SESSIONS:
            metrics.on_session_rejected()
            await websocket.close(code=1013, reason="Server at capacity")
            return
        _ACTIVE_SESSIONS.add(session.session_id)
        admitted = True
        metrics.on_session_opened()

    reader_task: asyncio.Task | None = None
    node_cache: dict[str, dict] = {}
    events_queue: asyncio.Queue[WidgetEvent | None] = asyncio.Queue(
        maxsize=_WS_EVENT_QUEUE_SIZE
    )

    try:
        await websocket.accept()
        if not _validate_and_copy_query_params(websocket, session):
            await websocket.close(code=1008, reason="Invalid query parameters")
            return

        logger.info("Session %s connected", session.session_id)

        # Initial render.
        try:
            t_run0 = time.perf_counter()
            result = await _run_in_worker(session.run)
            t_run1 = time.perf_counter()
            metrics.record_run((t_run1 - t_run0) * 1000)
        except asyncio.TimeoutError:
            await _send_payload(
                websocket,
                {
                    "type": "error",
                    "message": f"Initial render exceeded timeout of {_RUN_TIMEOUT_SECONDS:.1f}s",
                },
                node_cache=node_cache,
            )
            await websocket.close(code=1011, reason="Initial render timeout")
            return

        await _send_payload(websocket, result.to_dict(), node_cache=node_cache)
        logger.debug("Sent initial render (rev=%d)", session.rev)
        if _MAX_TREE_NODES > 0 and hasattr(result, "tree"):
            node_count = _count_nodes(getattr(result, "tree", None))
            if node_count > _MAX_TREE_NODES:
                await _send_payload(
                    websocket,
                    {
                        "type": "error",
                        "message": f"Tree node limit exceeded ({node_count} > {_MAX_TREE_NODES})",
                    },
                    node_cache=node_cache,
                )
                await websocket.close(code=1013, reason="Tree too large")
                return

        reader_task = asyncio.create_task(_ws_reader(websocket, events_queue))

        while True:
            coalesce_window_s = _WS_COALESCE_WINDOW_MS / 1000.0
            first_event = await events_queue.get()
            if first_event is None:
                break

            if coalesce_window_s > 0:
                await asyncio.sleep(coalesce_window_s)

            batch = _coalesce_events(
                first_event,
                events_queue,
                batch_limit=_WS_BATCH_LIMIT,
            )

            should_rerun = False
            rerun_event_ids: list[str] = []
            for event in batch:
                sentinel = object()
                prev_val = session.widget_store.get(event.id, sentinel)
                session.widget_store[event.id] = event.value
                ok, reason = _session_limits_ok(session)
                if not ok:
                    if prev_val is sentinel:
                        session.widget_store.pop(event.id, None)
                    else:
                        session.widget_store[event.id] = prev_val
                    await _send_payload(
                        websocket,
                        {
                            "type": "error",
                            "message": reason or "Session limits exceeded",
                        },
                        node_cache=node_cache,
                    )
                    continue
                if not event.no_rerun:
                    should_rerun = True
                    rerun_event_ids.append(event.id)

            if not should_rerun:
                continue

            fragment_ids: list[str] = []
            seen_frags: set[str] = set()
            has_non_fragment_event = False
            for event_id in rerun_event_ids:
                fragment_id = session._widget_to_fragment.get(event_id)
                if fragment_id is None:
                    has_non_fragment_event = True
                    continue
                if fragment_id in seen_frags:
                    continue
                seen_frags.add(fragment_id)
                fragment_ids.append(fragment_id)

            try:
                t2 = time.perf_counter()
                if has_non_fragment_event:
                    result = await _run_in_worker(session.run)
                elif len(fragment_ids) == 1:
                    result = await _run_in_worker(
                        lambda: session.run_fragment(fragment_ids[0])
                    )
                    if result is None:
                        result = await _run_in_worker(session.run)
                elif len(fragment_ids) > 1:
                    result = await _run_in_worker(lambda: session.run_fragments(fragment_ids))
                    if result is None:
                        result = await _run_in_worker(session.run)
                else:
                    result = await _run_in_worker(session.run)

                t3 = time.perf_counter()
                metrics.record_run((t3 - t2) * 1000)
                payload = result.to_dict()
                if _MAX_TREE_NODES > 0 and payload.get("type") == "render_full":
                    node_count = _count_nodes(payload.get("tree"))
                    if node_count > _MAX_TREE_NODES:
                        await _send_payload(
                            websocket,
                            {
                                "type": "error",
                                "message": (
                                    f"Tree node limit exceeded "
                                    f"({node_count} > {_MAX_TREE_NODES})"
                                ),
                            },
                            node_cache=node_cache,
                        )
                        await websocket.close(code=1013, reason="Tree too large")
                        return
                await _send_payload(websocket, payload, node_cache=node_cache)
                t4 = time.perf_counter()
                logger.info(
                    "[TIMING] Rerun took %.3fms, send took %.3fms (rev=%d, batch=%d)",
                    (t3 - t2) * 1000,
                    (t4 - t3) * 1000,
                    session.rev,
                    len(batch),
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Session %s rerun timed out after %.1fs",
                    session.session_id,
                    _RUN_TIMEOUT_SECONDS,
                )
                await _send_payload(
                    websocket,
                    {
                        "type": "error",
                        "message": f"Rerun exceeded timeout of {_RUN_TIMEOUT_SECONDS:.1f}s",
                    },
                    node_cache=node_cache,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Error during rerun: %s", exc)
                await _send_payload(
                    websocket,
                    {
                        "type": "error",
                        "message": str(exc),
                        "traceback": traceback.format_exc(),
                    },
                    node_cache=node_cache,
                )

    except Exception as exc:  # noqa: BLE001
        logger.info("Session %s disconnected: %s", session.session_id, exc)
    finally:
        if reader_task is not None:
            reader_task.cancel()
            try:
                await reader_task
            except Exception:  # noqa: BLE001
                pass

        if admitted:
            async with _SESSIONS_LOCK:
                _ACTIVE_SESSIONS.discard(session.session_id)
            metrics.on_session_closed()
        logger.info("Session %s closed", session.session_id)
