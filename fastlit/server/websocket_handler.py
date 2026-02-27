"""WebSocket handler: manages the lifecycle of a client connection."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import time
import traceback
import zlib
from collections import deque
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
_SENSITIVE_QUERY_PARAM_KEYS = {
    "token",  # internal WS auth token
}
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
_WS_REQUIRE_ORIGIN = os.environ.get("FASTLIT_WS_REQUIRE_ORIGIN", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
_WS_AUTH_TOKEN = os.environ.get("FASTLIT_WS_AUTH_TOKEN", "").strip()
_WS_MAX_CONNECTIONS_PER_IP = max(
    0, int(os.environ.get("FASTLIT_WS_MAX_CONNECTIONS_PER_IP", "0"))
)
_WS_MAX_CONNECTS_PER_MINUTE = max(
    0, int(os.environ.get("FASTLIT_WS_MAX_CONNECTS_PER_MINUTE", "0"))
)
_WS_MAX_EVENTS_PER_SECOND = max(
    0, int(os.environ.get("FASTLIT_WS_MAX_EVENTS_PER_SECOND", "0"))
)
_WS_RATE_LIMIT_MAX_VIOLATIONS = max(
    1, int(os.environ.get("FASTLIT_WS_RATE_LIMIT_MAX_VIOLATIONS", "3"))
)
_WS_BLOCK_SECONDS = max(
    0.0, float(os.environ.get("FASTLIT_WS_BLOCK_SECONDS", "0"))
)
_WS_MAX_REJECTS_PER_WINDOW = max(
    0, int(os.environ.get("FASTLIT_WS_MAX_REJECTS_PER_WINDOW", "0"))
)
_WS_REJECT_WINDOW_SECONDS = max(
    1.0, float(os.environ.get("FASTLIT_WS_REJECT_WINDOW_SECONDS", "60"))
)
_WS_IP_STATE_GC_INTERVAL_SECONDS = max(
    10.0, float(os.environ.get("FASTLIT_WS_IP_STATE_GC_INTERVAL_SECONDS", "60"))
)

_RUN_EXECUTOR = ThreadPoolExecutor(max_workers=_MAX_CONCURRENT_RUNS)
_RUN_SEMAPHORE: asyncio.Semaphore | None = None
_SESSIONS_LOCK: asyncio.Lock | None = None
_SYNC_PRIMITIVES_LOOP: asyncio.AbstractEventLoop | None = None
_ACTIVE_SESSIONS: set[str] = set()
_IP_ACTIVE_CONNECTIONS: dict[str, int] = {}
_IP_CONNECT_HISTORY: dict[str, deque[float]] = {}
_IP_REJECT_HISTORY: dict[str, deque[float]] = {}
_IP_BANNED_UNTIL: dict[str, float] = {}
_LAST_IP_STATE_GC_MONOTONIC = 0.0


def _get_sync_primitives() -> tuple[asyncio.Semaphore, asyncio.Lock]:
    """Get event-loop-local asyncio primitives."""
    loop = asyncio.get_running_loop()
    global _RUN_SEMAPHORE, _SESSIONS_LOCK, _SYNC_PRIMITIVES_LOOP
    if (
        _SYNC_PRIMITIVES_LOOP is not loop
        or _RUN_SEMAPHORE is None
        or _SESSIONS_LOCK is None
    ):
        _RUN_SEMAPHORE = asyncio.Semaphore(_MAX_CONCURRENT_RUNS)
        _SESSIONS_LOCK = asyncio.Lock()
        _SYNC_PRIMITIVES_LOOP = loop
    return _RUN_SEMAPHORE, _SESSIONS_LOCK


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


def _normalize_origin(value: str) -> str:
    return value.strip().rstrip("/").lower()


def _is_origin_allowed(websocket: WebSocket) -> bool:
    """Allow same-origin by default; allow explicit origins via env override."""
    origin = websocket.headers.get("origin")
    if not origin:
        return not _WS_REQUIRE_ORIGIN

    allowed = os.environ.get("FASTLIT_ALLOWED_ORIGINS", "").strip()
    if allowed:
        allowed_origins = {
            _normalize_origin(o)
            for o in allowed.split(",")
            if o.strip()
        }
        if "*" in allowed_origins:
            return True
        return _normalize_origin(origin) in allowed_origins

    host = websocket.headers.get("host")
    if not host:
        return False
    return _normalize_origin(origin) in {
        _normalize_origin(f"http://{host}"),
        _normalize_origin(f"https://{host}"),
    }


def _extract_ws_token(websocket: WebSocket) -> str | None:
    query_token = websocket.query_params.get("token")
    if query_token:
        return query_token

    auth_header = websocket.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        bearer = auth_header[7:].strip()
        if bearer:
            return bearer

    cookie_header = websocket.headers.get("cookie", "")
    for part in cookie_header.split(";"):
        item = part.strip()
        if not item or "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key.strip() == "fastlit_ws_token":
            token = value.strip()
            if token:
                return token
    return None


def _extract_ws_cookie(websocket: WebSocket, cookie_name: str) -> str | None:
    """Extract a specific cookie value from WebSocket upgrade headers."""
    cookie_header = websocket.headers.get("cookie", "")
    for part in cookie_header.split(";"):
        item = part.strip()
        if not item or "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key.strip() == cookie_name:
            v = value.strip()
            if v:
                return v
    return None


def _is_ws_auth_allowed(websocket: WebSocket) -> bool:
    if not _WS_AUTH_TOKEN:
        return True
    presented = _extract_ws_token(websocket)
    if not presented:
        return False
    return hmac.compare_digest(presented, _WS_AUTH_TOKEN)


def _client_ip(websocket: WebSocket) -> str:
    if websocket.client and websocket.client.host:
        return websocket.client.host
    return "unknown"


def _trim_window(history: deque[float], now: float, window_seconds: float) -> None:
    cutoff = now - window_seconds
    while history and history[0] < cutoff:
        history.popleft()


def _is_ip_temporarily_blocked(client_ip: str, now: float) -> bool:
    blocked_until = _IP_BANNED_UNTIL.get(client_ip)
    if blocked_until is None:
        return False
    if now >= blocked_until:
        _IP_BANNED_UNTIL.pop(client_ip, None)
        return False
    return True


def _record_reject_and_maybe_block(client_ip: str, now: float) -> bool:
    if _WS_BLOCK_SECONDS <= 0 or _WS_MAX_REJECTS_PER_WINDOW <= 0:
        return False

    history = _IP_REJECT_HISTORY.get(client_ip)
    if history is None:
        history = deque()
        _IP_REJECT_HISTORY[client_ip] = history

    _trim_window(history, now, _WS_REJECT_WINDOW_SECONDS)
    history.append(now)
    if len(history) < _WS_MAX_REJECTS_PER_WINDOW:
        return False

    _IP_BANNED_UNTIL[client_ip] = now + _WS_BLOCK_SECONDS
    _IP_REJECT_HISTORY.pop(client_ip, None)
    metrics.record_ws_ip_banned(1)
    return True


def _cleanup_ip_state(now: float, *, force: bool = False) -> None:
    """Prune idle IP state maps to avoid unbounded growth over time."""
    global _LAST_IP_STATE_GC_MONOTONIC

    if not force and (now - _LAST_IP_STATE_GC_MONOTONIC) < _WS_IP_STATE_GC_INTERVAL_SECONDS:
        return
    _LAST_IP_STATE_GC_MONOTONIC = now

    # Remove expired bans.
    for ip, blocked_until in list(_IP_BANNED_UNTIL.items()):
        if now >= blocked_until:
            _IP_BANNED_UNTIL.pop(ip, None)

    # Trim rolling histories and remove idle keys.
    for ip, history in list(_IP_CONNECT_HISTORY.items()):
        _trim_window(history, now, 60.0)
        if not history and _IP_ACTIVE_CONNECTIONS.get(ip, 0) <= 0:
            _IP_CONNECT_HISTORY.pop(ip, None)

    for ip, history in list(_IP_REJECT_HISTORY.items()):
        _trim_window(history, now, _WS_REJECT_WINDOW_SECONDS)
        if (
            not history
            and _IP_ACTIVE_CONNECTIONS.get(ip, 0) <= 0
            and ip not in _IP_BANNED_UNTIL
        ):
            _IP_REJECT_HISTORY.pop(ip, None)


def _validate_and_copy_query_params(websocket: WebSocket, session: Session) -> bool:
    """Validate query params shape/size before copying into session."""
    count = 0
    for key, value in websocket.query_params.multi_items():
        count += 1
        if count > _MAX_QUERY_PARAMS:
            return False
        if len(key) > _MAX_QUERY_KEY_LEN or len(value) > _MAX_QUERY_VAL_LEN:
            return False
        if key.lower() in _SENSITIVE_QUERY_PARAM_KEYS:
            continue
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
    run_semaphore, _ = _get_sync_primitives()
    async with run_semaphore:
        loop = asyncio.get_running_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(_RUN_EXECUTOR, fn),
            timeout=_RUN_TIMEOUT_SECONDS,
        )


async def _run_session_op_with_runtime_events(
    fn,
    *,
    session: Session,
    websocket: WebSocket,
    node_cache: dict[str, dict],
):
    """Run a session op and forward runtime events (spinner, etc.) live."""
    run_semaphore, _ = _get_sync_primitives()
    async with run_semaphore:
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(_RUN_EXECUTOR, fn)
        deadline = loop.time() + _RUN_TIMEOUT_SECONDS

        while True:
            # Flush runtime events emitted by the running script.
            events = session.drain_runtime_events()
            for event in events:
                await _send_payload(
                    websocket,
                    {"type": "runtime_event", "event": event},
                    node_cache=node_cache,
                )

            if future.done():
                # Final flush before returning.
                events = session.drain_runtime_events()
                for event in events:
                    await _send_payload(
                        websocket,
                        {"type": "runtime_event", "event": event},
                        node_cache=node_cache,
                    )
                return future.result()

            if loop.time() >= deadline:
                raise asyncio.TimeoutError()

            await asyncio.sleep(0.01)


async def _stream_generator_to_client(
    websocket: WebSocket,
    session: Session,
    node_id: str,
    gen: object,
    node_cache: dict[str, dict],
) -> None:
    """Iterate a sync generator and forward each chunk as an updateProps patch.

    Each ``next()`` call is dispatched to the shared thread-pool executor so
    the event loop stays responsive while waiting for slow producers (e.g. LLM
    APIs).  Chunks accumulate into *accumulated* so the frontend always shows
    the full text so far, not just the latest fragment.
    """
    accumulated = ""
    loop = asyncio.get_running_loop()

    def _get_next() -> str | None:
        return next(gen, None)  # type: ignore[call-overload]

    while True:
        chunk = await loop.run_in_executor(_RUN_EXECUTOR, _get_next)
        if chunk is None:
            break
        accumulated += str(chunk)
        await _send_payload(
            websocket,
            {
                "type": "render_patch",
                "rev": session.rev,  # not incremented — streaming is not a rerun
                "ops": [
                    {
                        "op": "updateProps",
                        "id": node_id,
                        "props": {"text": accumulated, "isStreaming": True},
                    }
                ],
            },
            node_cache=node_cache,
        )

    # Final update: mark streaming done (removes blinking cursor on frontend).
    if accumulated:
        await _send_payload(
            websocket,
            {
                "type": "render_patch",
                "rev": session.rev,
                "ops": [
                    {
                        "op": "updateProps",
                        "id": node_id,
                        "props": {"text": accumulated, "isStreaming": False},
                    }
                ],
            },
            node_cache=node_cache,
        )


async def _run_fragment_timer(
    fragment_id: str,
    interval_s: float,
    session: Session,
    websocket: WebSocket,
    node_cache: dict[str, dict],
) -> None:
    """Periodic loop: re-execute a fragment at *interval_s* second intervals.

    Runs via ``_run_in_worker`` so it respects the shared concurrency semaphore
    and serializes correctly with widget-triggered reruns.
    """
    while True:
        await asyncio.sleep(interval_s)
        try:
            result = await _run_session_op_with_runtime_events(
                lambda: session.run_fragment(fragment_id),
                session=session,
                websocket=websocket,
                node_cache=node_cache,
            )
            if result is not None:
                await _send_payload(websocket, result.to_dict(), node_cache=node_cache)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error in fragment timer for '%s'", fragment_id)


def _sync_fragment_timers(
    session: Session,
    fragment_timers: dict[str, asyncio.Task],
    websocket: WebSocket,
    node_cache: dict[str, dict],
) -> None:
    """Reconcile asyncio timer tasks with ``session._fragment_run_every``.

    Must be called only after a **full** ``session.run()`` (not after fragment
    reruns) because ``_fragment_registry`` is only rebuilt during full runs.

    Steps:
    1. Prune ``_fragment_run_every`` entries for fragments that no longer exist
       in the script (conditional branches etc.).
    2. Start new timer tasks for newly registered fragments.
    3. Cancel timer tasks for fragments that were removed.
    """
    # 1. Remove stale run_every entries (fragment no longer called this run).
    stale = set(session._fragment_run_every) - set(session._fragment_registry)
    for frag_id in stale:
        del session._fragment_run_every[frag_id]

    current_ids = set(session._fragment_run_every)

    # 2. Start missing timer tasks.
    for frag_id, interval_s in session._fragment_run_every.items():
        if frag_id not in fragment_timers or fragment_timers[frag_id].done():
            fragment_timers[frag_id] = asyncio.create_task(
                _run_fragment_timer(frag_id, interval_s, session, websocket, node_cache)
            )

    # 3. Cancel tasks for fragments that lost their run_every.
    for frag_id in list(fragment_timers):
        if frag_id not in current_ids:
            fragment_timers[frag_id].cancel()
            del fragment_timers[frag_id]


async def _ws_reader(
    websocket: WebSocket,
    queue: asyncio.Queue[WidgetEvent | None],
    *,
    client_ip: str,
    sessions_lock: asyncio.Lock,
) -> None:
    """Read and validate WS events into a bounded per-session queue."""
    recent_events: deque[float] = deque()
    violations = 0
    try:
        while True:
            raw = await websocket.receive_text()

            if _WS_MAX_EVENTS_PER_SECOND > 0:
                now = time.monotonic()
                cutoff = now - 1.0
                while recent_events and recent_events[0] < cutoff:
                    recent_events.popleft()
                if len(recent_events) >= _WS_MAX_EVENTS_PER_SECOND:
                    violations += 1
                    metrics.record_ws_rate_limited(1)
                    metrics.record_dropped_event(1)
                    if violations >= _WS_RATE_LIMIT_MAX_VIOLATIONS:
                        logger.warning("WebSocket rate limit exceeded; closing connection")
                        if _WS_BLOCK_SECONDS > 0 and _WS_MAX_REJECTS_PER_WINDOW > 0:
                            async with sessions_lock:
                                now2 = time.monotonic()
                                if _record_reject_and_maybe_block(client_ip, now2):
                                    logger.warning(
                                        "Temporarily blocked IP %s for %.0fs after WS event abuse",
                                        client_ip,
                                        _WS_BLOCK_SECONDS,
                                    )
                        try:
                            await websocket.close(
                                code=1013, reason="WebSocket event rate limit exceeded"
                            )
                        except Exception:  # noqa: BLE001
                            pass
                        break
                    continue
                recent_events.append(now)
                if violations > 0:
                    violations -= 1

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
    session = Session(script_path)
    admitted = False
    client_ip = _client_ip(websocket)

    _, sessions_lock = _get_sync_primitives()
    async with sessions_lock:
        now = time.monotonic()
        _cleanup_ip_state(now)

        if _is_ip_temporarily_blocked(client_ip, now):
            metrics.on_session_rejected()
            metrics.record_ws_ip_blocked(1)
            await websocket.close(code=1013, reason="IP temporarily blocked")
            return

        if not _is_origin_allowed(websocket):
            metrics.on_session_rejected()
            metrics.record_ws_origin_rejected(1)
            if _record_reject_and_maybe_block(client_ip, now):
                logger.warning(
                    "Temporarily blocked IP %s for %.0fs after origin rejects",
                    client_ip,
                    _WS_BLOCK_SECONDS,
                )
            await websocket.close(code=1008, reason="WebSocket origin not allowed")
            return

        if not _is_ws_auth_allowed(websocket):
            metrics.on_session_rejected()
            metrics.record_ws_auth_rejected(1)
            if _record_reject_and_maybe_block(client_ip, now):
                logger.warning(
                    "Temporarily blocked IP %s for %.0fs after auth rejects",
                    client_ip,
                    _WS_BLOCK_SECONDS,
                )
            await websocket.close(code=1008, reason="WebSocket authentication failed")
            return

        if _WS_MAX_CONNECTS_PER_MINUTE > 0:
            connect_history = _IP_CONNECT_HISTORY.get(client_ip)
            if connect_history is None:
                connect_history = deque()
                _IP_CONNECT_HISTORY[client_ip] = connect_history
            cutoff = now - 60.0
            while connect_history and connect_history[0] < cutoff:
                connect_history.popleft()
            if len(connect_history) >= _WS_MAX_CONNECTS_PER_MINUTE:
                metrics.on_session_rejected()
                metrics.record_ws_rate_limited(1)
                if _record_reject_and_maybe_block(client_ip, now):
                    logger.warning(
                        "Temporarily blocked IP %s for %.0fs after connect-rate rejects",
                        client_ip,
                        _WS_BLOCK_SECONDS,
                    )
                await websocket.close(code=1013, reason="Too many connection attempts")
                return
            connect_history.append(now)

        ip_active = _IP_ACTIVE_CONNECTIONS.get(client_ip, 0)
        if _WS_MAX_CONNECTIONS_PER_IP > 0 and ip_active >= _WS_MAX_CONNECTIONS_PER_IP:
            metrics.on_session_rejected()
            metrics.record_ws_rate_limited(1)
            if _record_reject_and_maybe_block(client_ip, now):
                logger.warning(
                    "Temporarily blocked IP %s for %.0fs after active-connection rejects",
                    client_ip,
                    _WS_BLOCK_SECONDS,
                )
            await websocket.close(code=1013, reason="Too many active sessions for this IP")
            return

        if _MAX_SESSIONS > 0 and len(_ACTIVE_SESSIONS) >= _MAX_SESSIONS:
            metrics.on_session_rejected()
            await websocket.close(code=1013, reason="Server at capacity")
            return
        _ACTIVE_SESSIONS.add(session.session_id)
        _IP_ACTIVE_CONNECTIONS[client_ip] = ip_active + 1
        admitted = True
        metrics.on_session_opened()

    reader_task: asyncio.Task | None = None
    node_cache: dict[str, dict] = {}
    events_queue: asyncio.Queue[WidgetEvent | None] = asyncio.Queue(
        maxsize=_WS_EVENT_QUEUE_SIZE
    )
    fragment_timers: dict[str, asyncio.Task] = {}

    try:
        await websocket.accept()
        if not _validate_and_copy_query_params(websocket, session):
            await websocket.close(code=1008, reason="Invalid query parameters")
            return

        # Attach OIDC user claims from session cookie (if auth is configured).
        try:
            from fastlit.server.app import _auth_cfg as _app_auth_cfg
            if _app_auth_cfg:
                from fastlit.server.auth import read_session_cookie
                _cookie_name = _app_auth_cfg.get("cookie_name", "fl_session")
                _cookie_val = _extract_ws_cookie(websocket, _cookie_name)
                if _cookie_val:
                    _claims = read_session_cookie(_cookie_val, _app_auth_cfg)
                    if _claims:
                        session.user_claims = _claims
        except Exception:
            pass  # Auth optional — never break WS on config errors

        logger.info("Session %s connected (%s)", session.session_id, client_ip)

        # Initial render.
        try:
            t_run0 = time.perf_counter()
            result = await _run_session_op_with_runtime_events(
                session.run,
                session=session,
                websocket=websocket,
                node_cache=node_cache,
            )
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

        # Execute any write_stream() generators registered during the run.
        if session._deferred_streams:
            deferred = session._deferred_streams[:]
            session._deferred_streams.clear()
            for _node_id, _gen in deferred:
                await _stream_generator_to_client(
                    websocket, session, _node_id, _gen, node_cache
                )

        # Sync fragment auto-refresh timers (full run only).
        _sync_fragment_timers(session, fragment_timers, websocket, node_cache)

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

        reader_task = asyncio.create_task(
            _ws_reader(
                websocket,
                events_queue,
                client_ip=client_ip,
                sessions_lock=sessions_lock,
            )
        )

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

            sentinel = object()
            previous_values: list[tuple[str, object]] = []
            rerun_event_ids: list[str] = []
            for event in batch:
                prev_val = session.widget_store.get(event.id, sentinel)
                previous_values.append((event.id, prev_val))
                session.widget_store[event.id] = event.value
                if not event.no_rerun:
                    rerun_event_ids.append(event.id)

            ok, reason = _session_limits_ok(session)
            if not ok:
                # Roll back the full batch atomically if session limits are exceeded.
                for event_id, prev_val in previous_values:
                    if prev_val is sentinel:
                        session.widget_store.pop(event_id, None)
                    else:
                        session.widget_store[event_id] = prev_val
                await _send_payload(
                    websocket,
                    {
                        "type": "error",
                        "message": reason or "Session limits exceeded",
                    },
                    node_cache=node_cache,
                )
                continue

            should_rerun = len(rerun_event_ids) > 0

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
                did_full_run = False
                if has_non_fragment_event:
                    result = await _run_session_op_with_runtime_events(
                        session.run,
                        session=session,
                        websocket=websocket,
                        node_cache=node_cache,
                    )
                    did_full_run = True
                elif len(fragment_ids) == 1:
                    result = await _run_session_op_with_runtime_events(
                        lambda: session.run_fragment(fragment_ids[0]),
                        session=session,
                        websocket=websocket,
                        node_cache=node_cache,
                    )
                    if result is None:
                        result = await _run_session_op_with_runtime_events(
                            session.run,
                            session=session,
                            websocket=websocket,
                            node_cache=node_cache,
                        )
                        did_full_run = True
                elif len(fragment_ids) > 1:
                    result = await _run_session_op_with_runtime_events(
                        lambda: session.run_fragments(fragment_ids),
                        session=session,
                        websocket=websocket,
                        node_cache=node_cache,
                    )
                    if result is None:
                        result = await _run_session_op_with_runtime_events(
                            session.run,
                            session=session,
                            websocket=websocket,
                            node_cache=node_cache,
                        )
                        did_full_run = True
                else:
                    result = await _run_session_op_with_runtime_events(
                        session.run,
                        session=session,
                        websocket=websocket,
                        node_cache=node_cache,
                    )
                    did_full_run = True

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

                # Execute any write_stream() generators registered during the run.
                if session._deferred_streams:
                    deferred = session._deferred_streams[:]
                    session._deferred_streams.clear()
                    for _node_id, _gen in deferred:
                        await _stream_generator_to_client(
                            websocket, session, _node_id, _gen, node_cache
                        )

                # Sync fragment auto-refresh timers (full runs only — fragment
                # runs don't rebuild _fragment_registry).
                if did_full_run:
                    _sync_fragment_timers(
                        session, fragment_timers, websocket, node_cache
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
            except BaseException:  # noqa: BLE001
                pass

        # Cancel all fragment auto-refresh timers tied to this connection.
        if fragment_timers:
            for _task in fragment_timers.values():
                _task.cancel()
            await asyncio.gather(*fragment_timers.values(), return_exceptions=True)
            fragment_timers.clear()

        if admitted:
            # Reuse the same lock instance used at admission time; do not
            # recreate loop-local primitives during teardown.
            async with sessions_lock:
                _ACTIVE_SESSIONS.discard(session.session_id)
                ip_active = _IP_ACTIVE_CONNECTIONS.get(client_ip, 0)
                if ip_active <= 1:
                    _IP_ACTIVE_CONNECTIONS.pop(client_ip, None)
                else:
                    _IP_ACTIVE_CONNECTIONS[client_ip] = ip_active - 1

                history = _IP_CONNECT_HISTORY.get(client_ip)
                if history:
                    cutoff = time.monotonic() - 60.0
                    while history and history[0] < cutoff:
                        history.popleft()
                    if not history and client_ip not in _IP_ACTIVE_CONNECTIONS:
                        _IP_CONNECT_HISTORY.pop(client_ip, None)
                _cleanup_ip_state(time.monotonic(), force=True)
            metrics.on_session_closed()
        logger.info("Session %s closed", session.session_id)
