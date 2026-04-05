"""WebSocket handler: manages the lifecycle of a client connection.

Optimized version:
- less duplicated rerun logic
- less copying of deferred streams
- clearer helpers for batch application / rollback
- removed dead code and unused imports
- keeps behavior aligned with the original implementation
"""

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
import uuid
import zlib
from collections import OrderedDict, deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import unquote

from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from fastlit.runtime.protocol import PatchOp, RenderFull, RenderPatch, WidgetEvent
from fastlit.runtime.session import Session
from fastlit.server import metrics
from fastlit.server.logging_config import reset_log_context, set_log_context
from fastlit.server.session_process import (
    SessionProcessCrashedError,
    SessionProcessExecutionError,
    SessionProcessWorker,
)
from fastlit.server.session_store import InMemorySessionStore, SessionRecord, SessionStore

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
    "token",
    "fastlit_path",
}
_MAX_WS_MESSAGE_BYTES = int(
    os.environ.get("FASTLIT_MAX_WS_MESSAGE_BYTES", str(16 * 1024 * 1024))
)

_MAX_SESSIONS = int(os.environ.get("FASTLIT_MAX_SESSIONS", "0"))
_MAX_CONCURRENT_RUNS = max(1, int(os.environ.get("FASTLIT_MAX_CONCURRENT_RUNS", "4")))
_RUN_TIMEOUT_SECONDS = float(os.environ.get("FASTLIT_RUN_TIMEOUT_SECONDS", "60"))
_RUNTIME_MODE = os.environ.get("FASTLIT_RUNTIME_MODE", "process").strip().lower() or "process"
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
_PATCH_ENABLE_ZLIB = os.environ.get("FASTLIT_PATCH_ENABLE_ZLIB", "1").strip().lower() in {
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
_MAX_SESSION_MEMORY_BYTES = max(
    0,
    int(os.environ.get("FASTLIT_MAX_SESSION_MEMORY_BYTES", str(32 * 1024 * 1024))),
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
    0, int(os.environ.get("FASTLIT_WS_MAX_EVENTS_PER_SECOND", "50"))
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
_WS_MAX_TRACKED_IPS = max(
    256, int(os.environ.get("FASTLIT_WS_MAX_TRACKED_IPS", "10000"))
)
_NODE_CACHE_LIMIT = 4096
_RUNTIME_EVENT_POLL_INTERVAL_SECONDS = 0.01

_RUN_EXECUTOR = ThreadPoolExecutor(max_workers=_MAX_CONCURRENT_RUNS)
_RUN_SEMAPHORE: asyncio.Semaphore | None = None
_STATE_LOCK: asyncio.Lock | None = None
_SYNC_PRIMITIVES_LOOP: asyncio.AbstractEventLoop | None = None

_IP_ACTIVE_CONNECTIONS: OrderedDict[str, int] = OrderedDict()
_IP_CONNECT_HISTORY: OrderedDict[str, deque[float]] = OrderedDict()
_IP_REJECT_HISTORY: OrderedDict[str, deque[float]] = OrderedDict()
_IP_BANNED_UNTIL: OrderedDict[str, float] = OrderedDict()
_LAST_IP_STATE_GC_MONOTONIC = 0.0


@dataclass(slots=True)
class _ProcessRuntimeState:
    worker: SessionProcessWorker
    committed_snapshot: dict[str, Any]


class _PayloadSerializationError(TypeError):
    """Raised when a websocket payload cannot be serialized safely."""


class _WebSocketClosedError(ConnectionError):
    """Raised when attempting to write to a closed websocket."""


class _SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that normalizes known payload types and rejects the rest."""

    def default(self, obj: object) -> object:
        try:
            import pandas as pd

            if isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient="records")
            if isinstance(obj, pd.Series):
                return obj.to_dict()
        except ImportError:
            pass

        try:
            import numpy as np

            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, np.bool_):
                return bool(obj)
        except ImportError:
            pass

        import datetime

        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()

        type_name = f"{type(obj).__module__}.{type(obj).__qualname__}"
        raise TypeError(f"Unsupported websocket payload type: {type_name}")


def _process_runtime_enabled() -> bool:
    return _RUNTIME_MODE == "process"


def _should_run_full_session_for_events(
    session: Session,
    rerun_event_ids: list[str],
    *,
    has_non_fragment_event: bool,
) -> bool:
    return has_non_fragment_event or any(
        event_id in session._force_full_render_widget_ids
        for event_id in rerun_event_ids
    )


def _render_flags_for_event_batch(
    session: Session,
    rerun_event_ids: list[str],
) -> tuple[bool, bool]:
    _ = session
    _ = rerun_event_ids
    return False, False


def _bound_ip_tracking_map(mapping: OrderedDict[str, Any]) -> None:
    if len(mapping) <= _WS_MAX_TRACKED_IPS:
        return
    for ip in list(mapping.keys()):
        if len(mapping) <= _WS_MAX_TRACKED_IPS:
            return
        if _IP_ACTIVE_CONNECTIONS.get(ip, 0) > 0:
            continue
        mapping.pop(ip, None)


def _remember_ip_tracking_value(mapping: OrderedDict[str, Any], ip: str, value: Any) -> Any:
    mapping[ip] = value
    mapping.move_to_end(ip)
    _bound_ip_tracking_map(mapping)
    return value


def _remember_node_cache_value(
    node_cache: dict[str, dict[str, Any]] | None,
    token: str,
    node: dict[str, Any],
) -> None:
    if node_cache is None:
        return

    if token in node_cache:
        if isinstance(node_cache, OrderedDict):
            node_cache.move_to_end(token)
        return

    node_cache[token] = node
    if isinstance(node_cache, OrderedDict):
        node_cache.move_to_end(token)

    while len(node_cache) > _NODE_CACHE_LIMIT:
        oldest = next(iter(node_cache))
        node_cache.pop(oldest, None)


def _lookup_node_cache_value(
    node_cache: dict[str, dict[str, Any]] | None,
    token: str,
) -> dict[str, Any] | None:
    if node_cache is None:
        return None
    node = node_cache.get(token)
    if node is not None and isinstance(node_cache, OrderedDict):
        node_cache.move_to_end(token)
    return node


def _get_sync_primitives() -> tuple[asyncio.Semaphore, asyncio.Lock]:
    loop = asyncio.get_running_loop()
    global _RUN_SEMAPHORE, _STATE_LOCK, _SYNC_PRIMITIVES_LOOP
    if (
        _SYNC_PRIMITIVES_LOOP is not loop
        or _RUN_SEMAPHORE is None
        or _STATE_LOCK is None
    ):
        _RUN_SEMAPHORE = asyncio.Semaphore(_MAX_CONCURRENT_RUNS)
        _STATE_LOCK = asyncio.Lock()
        _SYNC_PRIMITIVES_LOOP = loop
    return _RUN_SEMAPHORE, _STATE_LOCK


def _json_loads(raw: str) -> Any:
    if orjson is not None:
        return orjson.loads(raw)
    return json.loads(raw)


def _is_websocket_closed(websocket: WebSocket) -> bool:
    return (
        getattr(websocket, "application_state", None) == WebSocketState.DISCONNECTED
        or getattr(websocket, "client_state", None) == WebSocketState.DISCONNECTED
    )


def _is_send_after_close_error(exc: BaseException) -> bool:
    if isinstance(exc, WebSocketDisconnect):
        return True
    if isinstance(exc, RuntimeError):
        message = str(exc)
        return (
            "Unexpected ASGI message 'websocket.send'" in message
            or "after sending 'websocket.close'" in message
            or "response already completed" in message
        )
    return False


async def _send_websocket_text(websocket: WebSocket, body: str) -> None:
    if _is_websocket_closed(websocket):
        raise _WebSocketClosedError("WebSocket is already closed")
    try:
        await websocket.send_text(body)
    except BaseException as exc:  # noqa: BLE001
        if _is_send_after_close_error(exc):
            raise _WebSocketClosedError("WebSocket closed during send") from exc
        raise


def _finalize_background_task(
    task: asyncio.Task,
    *,
    tasks: set[asyncio.Task] | None = None,
    label: str,
) -> None:
    if tasks is not None:
        tasks.discard(task)
    try:
        exc = task.exception()
    except asyncio.CancelledError:
        return
    if exc is None or isinstance(exc, _WebSocketClosedError):
        return
    logger.error(
        "Background task failed: %s",
        label,
        exc_info=(type(exc), exc, exc.__traceback__),
    )


def _start_background_task(
    coro: Any,
    *,
    label: str,
    tasks: set[asyncio.Task] | None = None,
) -> asyncio.Task:
    task = asyncio.create_task(coro)
    if tasks is not None:
        tasks.add(task)
    task.add_done_callback(
        lambda done_task, tracked_tasks=tasks, task_label=label: _finalize_background_task(
            done_task,
            tasks=tracked_tasks,
            label=task_label,
        )
    )
    return task


def _serialize_payload(payload: dict[str, Any]) -> tuple[str, int]:
    if orjson is not None:
        try:
            body = orjson.dumps(payload)
            return body.decode("utf-8"), len(body)
        except TypeError:
            pass

    try:
        text = json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=False,
            cls=_SafeJSONEncoder,
        )
    except TypeError as exc:
        raise _PayloadSerializationError(
            f"Failed to serialize websocket payload: {exc}"
        ) from exc

    return text, len(text.encode("utf-8"))


def _node_token(node: dict[str, Any]) -> str:
    if orjson is not None:
        try:
            raw = orjson.dumps(node)
            return hashlib.sha1(raw).hexdigest()
        except TypeError:
            pass

    try:
        raw = json.dumps(
            node,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            cls=_SafeJSONEncoder,
        ).encode("utf-8")
    except TypeError as exc:
        raise _PayloadSerializationError(
            f"Failed to serialize websocket node payload: {exc}"
        ) from exc

    return hashlib.sha1(raw).hexdigest()


async def _send_safe_error_payload(websocket: WebSocket, message: str) -> None:
    body = json.dumps(
        {"type": "error", "message": message},
        separators=(",", ":"),
        ensure_ascii=False,
    )
    metrics.record_outbound_message(size_bytes=len(body.encode("utf-8")), message_type="error")
    await _send_websocket_text(websocket, body)


def _optimize_patch_payload(
    payload: dict[str, Any],
    *,
    node_cache: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], str | None, int | None]:
    if payload.get("type") != "render_patch":
        return payload, None, None

    ops = payload.get("ops")
    if not isinstance(ops, list) or len(ops) < _PATCH_COMPACT_MIN_OPS:
        return payload, None, None

    compact_ops: list[list[Any]] = []
    for op in ops:
        if not isinstance(op, dict):
            continue

        node_val = op.get("node")
        compact_node = node_val

        if isinstance(node_val, dict) and node_cache is not None:
            token = _node_token(node_val)
            if _lookup_node_cache_value(node_cache, token) is not None:
                compact_node = {"$ref": token}
            else:
                _remember_node_cache_value(node_cache, token, node_val)
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

    compact_text, compact_size = _serialize_payload(compact_payload)

    if not _PATCH_ENABLE_ZLIB or compact_size < _PATCH_COMPRESS_MIN_BYTES:
        return compact_payload, compact_text, compact_size

    compressed = zlib.compress(compact_text.encode("utf-8"), level=6)
    if len(compressed) + 64 >= compact_size:
        return compact_payload, compact_text, compact_size

    compressed_envelope = {
        "type": "render_patch_z",
        "rev": payload.get("rev"),
        "encoding": "zlib+base64",
        "ops": base64.b64encode(compressed).decode("ascii"),
    }
    compressed_text, compressed_size = _serialize_payload(compressed_envelope)
    return compressed_envelope, compressed_text, compressed_size


async def _send_payload(
    websocket: WebSocket,
    payload: dict[str, Any],
    *,
    node_cache: dict[str, dict[str, Any]] | None = None,
) -> None:
    payload_type = cast(object, payload.get("type"))
    try:
        payload, pre_serialized, pre_serialized_size = _optimize_patch_payload(
            payload,
            node_cache=node_cache,
        )
        if pre_serialized is not None:
            body = pre_serialized
            size_bytes = pre_serialized_size if pre_serialized_size is not None else len(
                body.encode("utf-8")
            )
        else:
            body, size_bytes = _serialize_payload(payload)
    except _PayloadSerializationError:
        logger.exception("Failed to serialize websocket payload (type=%s)", payload_type)
        await _send_safe_error_payload(
            websocket,
            "An internal serialization error occurred.",
        )
        raise

    metrics.record_outbound_message(size_bytes=size_bytes, message_type=payload.get("type"))
    await _send_websocket_text(websocket, body)


async def _send_error(
    websocket: WebSocket,
    node_cache: dict[str, dict[str, Any]],
    message: str,
) -> None:
    await _send_payload(
        websocket,
        {"type": "error", "message": message},
        node_cache=node_cache,
    )


async def _send_error_if_open(
    websocket: WebSocket,
    node_cache: dict[str, dict[str, Any]],
    message: str,
) -> bool:
    try:
        await _send_error(websocket, node_cache, message)
        return True
    except _WebSocketClosedError:
        return False


async def _send_pending_redirect(
    websocket: WebSocket,
    session: Session,
    *,
    node_cache: dict[str, dict[str, Any]],
) -> bool:
    target = session.consume_pending_browser_redirect()
    if not target:
        return False

    await _send_payload(
        websocket,
        {"type": "redirect", "path": target},
        node_cache=node_cache,
    )
    return True


def _estimate_json_bytes(obj: object) -> int:
    try:
        if orjson is not None:
            return len(orjson.dumps(obj))
        return len(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"))
    except Exception:
        return 0


def _get_session_store(websocket: WebSocket) -> SessionStore:
    app = websocket.scope.get("app")
    store = getattr(getattr(app, "state", None), "session_store", None)
    if store is None:
        store = InMemorySessionStore()
        if getattr(app, "state", None) is not None:
            app.state.session_store = store
    return store


def _estimate_session_tree_bytes(session: Session) -> int:
    total = session.committed_tree_bytes()
    if session.current_tree is not None and session.current_tree is not session._previous_tree:
        total += _estimate_json_bytes(session.current_tree.to_dict())
    return total


def _session_limits_ok(session: Session) -> tuple[bool, str | None]:
    widget_bytes = _estimate_json_bytes(session.widget_store)
    if _MAX_WIDGET_STORE_BYTES > 0 and widget_bytes > _MAX_WIDGET_STORE_BYTES:
        return (
            False,
            f"Widget store limit exceeded ({widget_bytes} > {_MAX_WIDGET_STORE_BYTES} bytes)",
        )

    state_bytes = _estimate_json_bytes(session.session_state)
    if _MAX_SESSION_STATE_BYTES > 0 and state_bytes > _MAX_SESSION_STATE_BYTES:
        return (
            False,
            f"Session state limit exceeded ({state_bytes} > {_MAX_SESSION_STATE_BYTES} bytes)",
        )

    tree_bytes = _estimate_session_tree_bytes(session)
    total_bytes = widget_bytes + state_bytes + tree_bytes
    metrics.record_session_memory(total_bytes, budget_bytes=_MAX_SESSION_MEMORY_BYTES)

    if _MAX_SESSION_MEMORY_BYTES > 0 and total_bytes > _MAX_SESSION_MEMORY_BYTES:
        return (
            False,
            f"Session memory limit exceeded ({total_bytes} > {_MAX_SESSION_MEMORY_BYTES} bytes)",
        )

    return True, None


def _count_nodes(tree: dict[str, Any] | None) -> int:
    if not tree:
        return 0

    count = 0
    stack = [tree]
    while stack:
        node = stack.pop()
        count += 1
        children = node.get("children")
        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    stack.append(child)
    return count


async def _enforce_tree_limit(
    websocket: WebSocket,
    payload: dict[str, Any],
    *,
    node_cache: dict[str, dict[str, Any]],
) -> bool:
    if _MAX_TREE_NODES <= 0 or payload.get("type") != "render_full":
        return True

    node_count = _count_nodes(cast(dict[str, Any] | None, payload.get("tree")))
    if node_count <= _MAX_TREE_NODES:
        return True

    await _send_error(
        websocket,
        node_cache,
        f"Tree node limit exceeded ({node_count} > {_MAX_TREE_NODES})",
    )
    await websocket.close(code=1013, reason="Tree too large")
    return False


def _normalize_origin(value: str) -> str:
    return value.strip().rstrip("/").lower()


def _is_origin_allowed(websocket: WebSocket) -> bool:
    origin = websocket.headers.get("origin")
    if not origin:
        return not _WS_REQUIRE_ORIGIN

    allowed = os.environ.get("FASTLIT_ALLOWED_ORIGINS", "").strip()
    if allowed:
        allowed_origins = {_normalize_origin(item) for item in allowed.split(",") if item.strip()}
        return "*" in allowed_origins or _normalize_origin(origin) in allowed_origins

    host = websocket.headers.get("host")
    if not host:
        return False

    normalized_origin = _normalize_origin(origin)
    return normalized_origin in {
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
                return unquote(token)

    return None


def _extract_ws_cookie(websocket: WebSocket, cookie_name: str) -> str | None:
    cookie_header = websocket.headers.get("cookie", "")
    for part in cookie_header.split(";"):
        item = part.strip()
        if not item or "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key.strip() == cookie_name:
            cookie_value = value.strip()
            if cookie_value:
                return cookie_value
    return None


def _auth_cfg_for_websocket(websocket: WebSocket) -> dict[str, Any]:
    app = websocket.scope.get("app")
    return dict(getattr(getattr(app, "state", None), "auth_cfg", {}) or {})


async def _touch_session(
    store: SessionStore | None,
    session_id: str,
    *,
    session_record: SessionRecord | None = None,
    at: float | None = None,
) -> SessionRecord | None:
    timestamp = time.monotonic() if at is None else float(at)
    if session_record is not None:
        session_record.last_activity = timestamp
        return session_record
    if store is None:
        return None
    return await store.touch(session_id, at=timestamp)


def _is_ws_auth_allowed(websocket: WebSocket) -> bool:
    if not _WS_AUTH_TOKEN:
        return True

    presented = _extract_ws_token(websocket)
    return bool(presented) and hmac.compare_digest(presented, _WS_AUTH_TOKEN)


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

    _IP_BANNED_UNTIL.move_to_end(client_ip)
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
        _remember_ip_tracking_value(_IP_REJECT_HISTORY, client_ip, history)
    else:
        _IP_REJECT_HISTORY.move_to_end(client_ip)

    _trim_window(history, now, _WS_REJECT_WINDOW_SECONDS)
    history.append(now)

    if len(history) < _WS_MAX_REJECTS_PER_WINDOW:
        return False

    _remember_ip_tracking_value(_IP_BANNED_UNTIL, client_ip, now + _WS_BLOCK_SECONDS)
    _IP_REJECT_HISTORY.pop(client_ip, None)
    metrics.record_ws_ip_banned(1)
    return True


def _cleanup_ip_state(now: float, *, force: bool = False) -> None:
    global _LAST_IP_STATE_GC_MONOTONIC

    if not force and (now - _LAST_IP_STATE_GC_MONOTONIC) < _WS_IP_STATE_GC_INTERVAL_SECONDS:
        return

    _LAST_IP_STATE_GC_MONOTONIC = now

    for ip, blocked_until in list(_IP_BANNED_UNTIL.items()):
        if now >= blocked_until:
            _IP_BANNED_UNTIL.pop(ip, None)

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

    _bound_ip_tracking_map(_IP_CONNECT_HISTORY)
    _bound_ip_tracking_map(_IP_REJECT_HISTORY)
    _bound_ip_tracking_map(_IP_BANNED_UNTIL)


def _validate_and_copy_query_params(websocket: WebSocket, session: Session) -> bool:
    count = 0
    for key, value in websocket.query_params.multi_items():
        count += 1
        if count > _MAX_QUERY_PARAMS:
            return False
        if len(key) > _MAX_QUERY_KEY_LEN or len(value) > _MAX_QUERY_VAL_LEN:
            return False

        if key == "fastlit_path":
            session.set_current_path(value)
            continue

        if key.lower() in _SENSITIVE_QUERY_PARAM_KEYS:
            continue

        session.query_params[key] = value

    return True


def _parse_widget_event(raw: str) -> WidgetEvent | None:
    if len(raw.encode("utf-8")) > _MAX_WS_MESSAGE_BYTES:
        return None

    try:
        msg = _json_loads(raw)
    except Exception:
        return None

    if not isinstance(msg, dict) or msg.get("type") != "widget_event":
        return None

    event = WidgetEvent.from_dict(msg)
    if not event.id or len(event.id) > _MAX_WIDGET_ID_LEN:
        return None

    return event


def _widget_events_to_runtime_payload(
    events: list[WidgetEvent],
) -> list[dict[str, Any]]:
    return [
        {
            "id": event.id,
            "value": event.value,
            "path": event.path,
        }
        for event in events
    ]


def _render_result_from_dict(
    payload: dict[str, Any] | None,
) -> RenderFull | RenderPatch | None:
    if payload is None:
        return None

    payload_type = str(payload.get("type", ""))
    if payload_type == "render_full":
        return RenderFull(
            rev=int(payload.get("rev", 0)),
            tree=cast(dict[str, Any] | None, payload.get("tree")),
        )

    if payload_type == "render_patch":
        raw_ops = payload.get("ops", [])
        ops: list[PatchOp] = []
        if isinstance(raw_ops, list):
            for raw_op in raw_ops:
                if not isinstance(raw_op, dict):
                    continue
                ops.append(
                    PatchOp(
                        op=cast(Any, raw_op.get("op", "updateProps")),
                        id=str(raw_op.get("id", "")),
                        node=cast(dict[str, Any] | None, raw_op.get("node")),
                        props=cast(dict[str, Any] | None, raw_op.get("props")),
                        parent_id=cast(str | None, raw_op.get("parentId")),
                        index=cast(int | None, raw_op.get("index")),
                    )
                )
        return RenderPatch(rev=int(payload.get("rev", 0)), ops=ops)

    raise ValueError(f"Unsupported render result payload type: {payload_type}")


async def _flush_runtime_events(
    session: Session,
    websocket: WebSocket,
    node_cache: dict[str, dict[str, Any]],
) -> None:
    for event in session.drain_runtime_events():
        await _send_payload(
            websocket,
            {"type": "runtime_event", "event": event},
            node_cache=node_cache,
        )


async def _run_session_op_with_runtime_events(
    fn: Any,
    *,
    session: Session,
    websocket: WebSocket,
    node_cache: dict[str, dict[str, Any]],
    session_lock: asyncio.Lock,
    session_store: SessionStore | None = None,
    session_record: SessionRecord | None = None,
    runtime_state: _ProcessRuntimeState | None = None,
    command_name: str | None = None,
    payload: dict[str, Any] | None = None,
    events: list[WidgetEvent] | None = None,
) -> RenderFull | RenderPatch | None:
    run_semaphore, _ = _get_sync_primitives()

    async with session_lock, run_semaphore:
        await _touch_session(
            session_store,
            session.session_id,
            session_record=session_record,
        )

        if runtime_state is not None:
            if command_name is None:
                raise ValueError("command_name is required in process runtime mode")

            async def _forward_runtime_event(event: dict[str, Any]) -> None:
                await _send_payload(
                    websocket,
                    {"type": "runtime_event", "event": event},
                    node_cache=node_cache,
                )

            try:
                result_dict, snapshot, pending_redirect = await runtime_state.worker.execute(
                    command_name=command_name,
                    payload=payload,
                    events=_widget_events_to_runtime_payload(events or []),
                    timeout_seconds=_RUN_TIMEOUT_SECONDS,
                    on_runtime_event=_forward_runtime_event,
                )
            except (asyncio.TimeoutError, SessionProcessCrashedError, SessionProcessExecutionError):
                await _restart_process_runtime(session, runtime_state)
                raise

            session.restore_snapshot(snapshot)
            if pending_redirect:
                session._pending_browser_redirect = pending_redirect
            runtime_state.committed_snapshot = snapshot

            await _touch_session(
                session_store,
                session.session_id,
                session_record=session_record,
            )

            return _render_result_from_dict(result_dict)

        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(_RUN_EXECUTOR, fn)
        deadline = loop.time() + _RUN_TIMEOUT_SECONDS

        while True:
            await _flush_runtime_events(session, websocket, node_cache)

            if future.done():
                await _flush_runtime_events(session, websocket, node_cache)
                await _touch_session(
                    session_store,
                    session.session_id,
                    session_record=session_record,
                )
                return future.result()

            if loop.time() >= deadline:
                raise asyncio.TimeoutError()

            await asyncio.sleep(_RUNTIME_EVENT_POLL_INTERVAL_SECONDS)


def _stream_patch_payload(
    session: Session,
    node_id: str,
    *,
    chunk: str | None = None,
    done: bool = False,
) -> dict[str, Any]:
    props = {"done": True} if done else {"chunk": chunk or ""}
    return {
        "type": "render_patch",
        "rev": session.rev,
        "ops": [{"op": "streamText", "id": node_id, "props": props}],
    }


async def _stream_generator_to_client(
    websocket: WebSocket,
    session: Session,
    node_id: str,
    gen: object,
    node_cache: dict[str, dict[str, Any]],
) -> None:
    loop = asyncio.get_running_loop()

    def _get_next() -> str | None:
        return next(gen, None)  # type: ignore[call-overload]

    while True:
        chunk = await loop.run_in_executor(_RUN_EXECUTOR, _get_next)
        if chunk is None:
            break
        await _send_payload(
            websocket,
            _stream_patch_payload(session, node_id, chunk=str(chunk)),
            node_cache=node_cache,
        )

    await _send_payload(
        websocket,
        _stream_patch_payload(session, node_id, done=True),
        node_cache=node_cache,
    )


async def _drain_deferred_streams(
    websocket: WebSocket,
    session: Session,
    node_cache: dict[str, dict[str, Any]],
    runtime_state: _ProcessRuntimeState | None = None,
) -> None:
    if runtime_state is not None:
        async def _send_stream_chunk(node_id: str, chunk: str) -> None:
            await _send_payload(
                websocket,
                _stream_patch_payload(session, node_id, chunk=chunk),
                node_cache=node_cache,
            )

        async def _send_stream_end(node_id: str) -> None:
            await _send_payload(
                websocket,
                _stream_patch_payload(session, node_id, done=True),
                node_cache=node_cache,
            )

        async def _send_stream_error(node_id: str, error: str) -> None:
            logger.warning("Stream error for node %s: %s", node_id, error)
            await _send_error(
                websocket,
                node_cache,
                "A streaming response failed before completion.",
            )

        await runtime_state.worker.drain_streams(
            timeout_seconds=_RUN_TIMEOUT_SECONDS,
            on_stream_chunk=_send_stream_chunk,
            on_stream_end=_send_stream_end,
            on_stream_error=_send_stream_error,
        )
        return

    deferred = session._deferred_streams
    if not deferred:
        return

    session._deferred_streams = []
    for node_id, gen in deferred:
        await _stream_generator_to_client(websocket, session, node_id, gen, node_cache)


async def _restart_process_runtime(
    session: Session,
    runtime_state: _ProcessRuntimeState,
) -> None:
    session.restore_snapshot(runtime_state.committed_snapshot)
    await runtime_state.worker.restart(runtime_state.committed_snapshot)


async def _apply_events_to_process_runtime(
    events: list[WidgetEvent],
    *,
    session: Session,
    session_lock: asyncio.Lock,
    session_store: SessionStore | None,
    session_record: SessionRecord | None,
    runtime_state: _ProcessRuntimeState,
) -> None:
    if not events:
        return

    run_semaphore, _ = _get_sync_primitives()
    async with session_lock, run_semaphore:
        await _touch_session(
            session_store,
            session.session_id,
            session_record=session_record,
        )
        try:
            await runtime_state.worker.apply_events(
                _widget_events_to_runtime_payload(events),
                timeout_seconds=_RUN_TIMEOUT_SECONDS,
            )
        except (asyncio.TimeoutError, SessionProcessCrashedError):
            await _restart_process_runtime(session, runtime_state)
            raise

        runtime_state.committed_snapshot = session.snapshot_state()
        await _touch_session(
            session_store,
            session.session_id,
            session_record=session_record,
        )


async def _cancel_background_tasks(tasks: set[asyncio.Task]) -> None:
    if not tasks:
        return

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    tasks.clear()


async def _run_fragment_timer(
    fragment_id: str,
    interval_s: float,
    session: Session,
    websocket: WebSocket,
    node_cache: dict[str, dict[str, Any]],
    *,
    session_lock: asyncio.Lock,
    session_store: SessionStore,
    fragment_timers: dict[str, asyncio.Task],
    deferred_fragment_tasks: set[asyncio.Task],
    session_record: SessionRecord | None = None,
    runtime_state: _ProcessRuntimeState | None = None,
) -> None:
    while True:
        await asyncio.sleep(interval_s)
        try:
            before_epoch, _ = session.get_deferred_fragment_snapshot()
            try:
                result = await _run_session_op_with_runtime_events(
                    lambda: session.run_fragment(fragment_id),
                    session=session,
                    websocket=websocket,
                    node_cache=node_cache,
                    session_lock=session_lock,
                    session_store=session_store,
                    session_record=session_record,
                    runtime_state=runtime_state,
                    command_name="run_fragment",
                    payload={"fragment_id": fragment_id},
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Fragment timer %s exceeded timeout after %.1fs",
                    fragment_id,
                    _RUN_TIMEOUT_SECONDS,
                )
                await _send_error_if_open(
                    websocket,
                    node_cache,
                    f"Fragment '{fragment_id}' exceeded timeout of {_RUN_TIMEOUT_SECONDS:.1f}s",
                )
                return
            except SessionProcessCrashedError:
                logger.warning(
                    "Fragment timer %s failed after worker restart",
                    fragment_id,
                )
                await _send_error_if_open(
                    websocket,
                    node_cache,
                    f"Fragment '{fragment_id}' failed to complete",
                )
                return
            if result is None:
                continue

            after_epoch, _ = session.get_deferred_fragment_snapshot()
            try:
                delivery = await _deliver_render_result(
                    result=result,
                    did_full_run=after_epoch != before_epoch,
                    websocket=websocket,
                    session=session,
                    node_cache=node_cache,
                    session_lock=session_lock,
                    session_store=session_store,
                    session_record=session_record,
                    fragment_timers=fragment_timers,
                    deferred_fragment_tasks=deferred_fragment_tasks,
                    runtime_state=runtime_state,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Fragment timer stream for %s timed out after %.1fs",
                    fragment_id,
                    _RUN_TIMEOUT_SECONDS,
                )
                await _send_error_if_open(
                    websocket,
                    node_cache,
                    (
                        f"Fragment '{fragment_id}' stream stalled for more than "
                        f"{_RUN_TIMEOUT_SECONDS:.1f}s"
                    ),
                )
                return
            except SessionProcessCrashedError:
                logger.warning(
                    "Fragment timer stream for %s failed after worker restart",
                    fragment_id,
                )
                await _send_error_if_open(
                    websocket,
                    node_cache,
                    f"Fragment '{fragment_id}' stream failed to complete",
                )
                return
            if delivery != "sent":
                return
        except asyncio.CancelledError:
            raise
        except _WebSocketClosedError:
            return
        except Exception:
            logger.exception("Error in fragment timer for '%s'", fragment_id)


async def _hydrate_deferred_fragments(
    fragment_ids: list[str],
    *,
    expected_epoch: int,
    session: Session,
    websocket: WebSocket,
    node_cache: dict[str, dict[str, Any]],
    session_lock: asyncio.Lock,
    session_store: SessionStore,
    session_record: SessionRecord | None,
    fragment_timers: dict[str, asyncio.Task],
    deferred_fragment_tasks: set[asyncio.Task],
    runtime_state: _ProcessRuntimeState | None = None,
) -> None:
    pending = deque(fragment_ids)
    epoch = expected_epoch

    while pending:
        try:
            current_epoch, _ = session.get_deferred_fragment_snapshot()
            if current_epoch != epoch:
                return

            fragment_id = pending.popleft()

            try:
                before_epoch = current_epoch
                result = await _run_session_op_with_runtime_events(
                    lambda frag_id=fragment_id: session.run_fragment(frag_id),
                    session=session,
                    websocket=websocket,
                    node_cache=node_cache,
                    session_lock=session_lock,
                    session_store=session_store,
                    session_record=session_record,
                    runtime_state=runtime_state,
                    command_name="run_fragment",
                    payload={"fragment_id": fragment_id},
                )
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError:
                logger.warning(
                    "Deferred fragment %s timed out after %.1fs",
                    fragment_id,
                    _RUN_TIMEOUT_SECONDS,
                )
                await _send_error_if_open(
                    websocket,
                    node_cache,
                    (
                        f"Deferred fragment '{fragment_id}' exceeded timeout "
                        f"of {_RUN_TIMEOUT_SECONDS:.1f}s"
                    ),
                )
                return
            except Exception:
                logger.exception("Deferred fragment hydration failed for '%s'", fragment_id)
                await _send_error_if_open(
                    websocket,
                    node_cache,
                    f"Deferred fragment '{fragment_id}' failed to load",
                )
                return

            if result is None:
                continue

            current_epoch, _ = session.get_deferred_fragment_snapshot()
            if current_epoch != epoch:
                return

            delivery = await _deliver_render_result(
                result=result,
                did_full_run=current_epoch != before_epoch,
                websocket=websocket,
                session=session,
                node_cache=node_cache,
                session_lock=session_lock,
                session_store=session_store,
                session_record=session_record,
                fragment_timers=fragment_timers,
                deferred_fragment_tasks=deferred_fragment_tasks,
                runtime_state=runtime_state,
                schedule_deferred_hydration=False,
            )
            if delivery != "sent":
                return

            if current_epoch != before_epoch:
                epoch, pending_ids = session.get_deferred_fragment_snapshot()
                pending = deque(pending_ids)

        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError:
            logger.warning(
                "Deferred fragment stream for %s timed out after %.1fs",
                fragment_id,
                _RUN_TIMEOUT_SECONDS,
            )
            await _send_error_if_open(
                websocket,
                node_cache,
                (
                    f"Deferred fragment '{fragment_id}' stream stalled for more than "
                    f"{_RUN_TIMEOUT_SECONDS:.1f}s"
                ),
            )
            return
        except SessionProcessCrashedError:
            logger.warning(
                "Deferred fragment stream for %s failed after worker restart",
                fragment_id,
            )
            await _send_error_if_open(
                websocket,
                node_cache,
                f"Deferred fragment '{fragment_id}' stream failed to complete",
            )
            return
        except _WebSocketClosedError:
            return


def _sync_fragment_timers(
    session: Session,
    fragment_timers: dict[str, asyncio.Task],
    deferred_fragment_tasks: set[asyncio.Task],
    websocket: WebSocket,
    node_cache: dict[str, dict[str, Any]],
    *,
    session_lock: asyncio.Lock,
    session_store: SessionStore,
    session_record: SessionRecord | None = None,
    runtime_state: _ProcessRuntimeState | None = None,
) -> None:
    if runtime_state is None:
        stale = set(session._fragment_run_every) - set(session._fragment_registry)
        for frag_id in stale:
            del session._fragment_run_every[frag_id]

    current_ids = set(session._fragment_run_every)

    for frag_id, interval_s in session._fragment_run_every.items():
        task = fragment_timers.get(frag_id)
        if task is None or task.done():
            fragment_timers[frag_id] = _start_background_task(
                _run_fragment_timer(
                    frag_id,
                    interval_s,
                    session,
                    websocket,
                    node_cache,
                    session_lock=session_lock,
                    session_store=session_store,
                    fragment_timers=fragment_timers,
                    deferred_fragment_tasks=deferred_fragment_tasks,
                    session_record=session_record,
                    runtime_state=runtime_state,
                ),
                label=f"fragment timer '{frag_id}'",
            )

    for frag_id in list(fragment_timers):
        if frag_id not in current_ids:
            fragment_timers[frag_id].cancel()
            del fragment_timers[frag_id]


def _start_deferred_fragment_hydration(
    *,
    session: Session,
    websocket: WebSocket,
    node_cache: dict[str, dict[str, Any]],
    session_lock: asyncio.Lock,
    session_store: SessionStore,
    session_record: SessionRecord | None,
    fragment_timers: dict[str, asyncio.Task],
    deferred_fragment_tasks: set[asyncio.Task],
    runtime_state: _ProcessRuntimeState | None,
) -> None:
    deferred_epoch, deferred_ids = session.get_deferred_fragment_snapshot()
    if not deferred_ids:
        return

    _start_background_task(
        _hydrate_deferred_fragments(
            deferred_ids,
            expected_epoch=deferred_epoch,
            session=session,
            websocket=websocket,
            node_cache=node_cache,
            session_lock=session_lock,
            session_store=session_store,
            session_record=session_record,
            fragment_timers=fragment_timers,
            deferred_fragment_tasks=deferred_fragment_tasks,
            runtime_state=runtime_state,
        ),
        label="deferred fragment hydration",
        tasks=deferred_fragment_tasks,
    )


async def _deliver_render_result(
    *,
    result: RenderFull | RenderPatch | None,
    did_full_run: bool,
    websocket: WebSocket,
    session: Session,
    node_cache: dict[str, dict[str, Any]],
    session_lock: asyncio.Lock,
    session_store: SessionStore,
    session_record: SessionRecord | None,
    fragment_timers: dict[str, asyncio.Task],
    deferred_fragment_tasks: set[asyncio.Task],
    runtime_state: _ProcessRuntimeState | None,
    schedule_deferred_hydration: bool = True,
) -> str:
    if result is None:
        return "noop"

    full_run = did_full_run or getattr(result, "type", None) == "render_full"
    if await _send_pending_redirect(websocket, session, node_cache=node_cache):
        return "redirected"

    payload = result.to_dict()
    if not await _enforce_tree_limit(websocket, payload, node_cache=node_cache):
        return "closed"

    await _send_payload(websocket, payload, node_cache=node_cache)
    await _drain_deferred_streams(
        websocket,
        session,
        node_cache,
        runtime_state=runtime_state,
    )

    if full_run:
        _sync_fragment_timers(
            session,
            fragment_timers,
            deferred_fragment_tasks,
            websocket,
            node_cache,
            session_lock=session_lock,
            session_store=session_store,
            session_record=session_record,
            runtime_state=runtime_state,
        )
        if schedule_deferred_hydration:
            _start_deferred_fragment_hydration(
                session=session,
                websocket=websocket,
                node_cache=node_cache,
                session_lock=session_lock,
                session_store=session_store,
                session_record=session_record,
                fragment_timers=fragment_timers,
                deferred_fragment_tasks=deferred_fragment_tasks,
                runtime_state=runtime_state,
            )

    return "sent"


def _queue_disconnect_sentinel(queue: asyncio.Queue[WidgetEvent | None]) -> None:
    while True:
        try:
            queue.put_nowait(None)
            return
        except asyncio.QueueFull:
            with suppress(asyncio.QueueEmpty):
                dropped = queue.get_nowait()
                if dropped is not None:
                    metrics.record_dropped_event(1)
                continue
            return


async def _ws_reader(
    websocket: WebSocket,
    queue: asyncio.Queue[WidgetEvent | None],
    *,
    client_ip: str,
    sessions_lock: asyncio.Lock,
    session_store: SessionStore,
    session_id: str,
    session_record: SessionRecord | None = None,
) -> None:
    recent_events: deque[float] = deque()
    violations = 0

    try:
        while True:
            raw = await websocket.receive_text()
            await _touch_session(
                session_store,
                session_id,
                session_record=session_record,
            )

            if _WS_MAX_EVENTS_PER_SECOND > 0:
                now = time.monotonic()
                _trim_window(recent_events, now, 1.0)

                if len(recent_events) >= _WS_MAX_EVENTS_PER_SECOND:
                    violations += 1
                    metrics.record_ws_rate_limited(1)
                    metrics.record_dropped_event(1)

                    if violations >= _WS_RATE_LIMIT_MAX_VIOLATIONS:
                        logger.warning("WebSocket rate limit exceeded; closing connection")
                        if _WS_BLOCK_SECONDS > 0 and _WS_MAX_REJECTS_PER_WINDOW > 0:
                            async with sessions_lock:
                                if _record_reject_and_maybe_block(client_ip, time.monotonic()):
                                    logger.warning(
                                        "Temporarily blocked IP %s for %.0fs after WS event abuse",
                                        client_ip,
                                        _WS_BLOCK_SECONDS,
                                    )
                        with suppress(Exception):
                            await websocket.close(
                                code=1013,
                                reason="WebSocket event rate limit exceeded",
                            )
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
                with suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
                    metrics.record_dropped_event(1)

                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    metrics.record_dropped_event(1)

    except WebSocketDisconnect:
        pass
    finally:
        _queue_disconnect_sentinel(queue)


def _coalesce_events(
    first_event: WidgetEvent,
    queue: asyncio.Queue[WidgetEvent | None],
    *,
    batch_limit: int,
) -> tuple[list[WidgetEvent], bool]:
    merged: dict[str, WidgetEvent] = {first_event.id: first_event}
    drained = 0
    saw_eof = False

    while drained < max(0, batch_limit - 1):
        try:
            ev = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        if ev is None:
            saw_eof = True
            break

        previous = merged.get(ev.id)
        if previous is None:
            merged[ev.id] = ev
        else:
            merged[ev.id] = WidgetEvent(
                type=ev.type,
                id=ev.id,
                value=ev.value,
                path=ev.path if ev.path is not None else previous.path,
                no_rerun=previous.no_rerun and ev.no_rerun,
            )

        drained += 1

    return list(merged.values()), saw_eof


def _event_batch_to_widget_store(
    session: Session,
    batch: list[WidgetEvent],
) -> tuple[list[str], list[tuple[str, object]], object]:
    sentinel = object()
    previous_values: list[tuple[str, object]] = []
    rerun_event_ids: list[str] = []

    for event in batch:
        if event.path is not None:
            session.set_current_path(event.path)

        prev_val = session.widget_store.get(event.id, sentinel)
        previous_values.append((event.id, prev_val))
        session.widget_store[event.id] = event.value

        if not event.no_rerun:
            rerun_event_ids.append(event.id)

    return rerun_event_ids, previous_values, sentinel


def _rollback_widget_store_batch(
    session: Session,
    previous_values: list[tuple[str, object]],
    sentinel: object,
) -> None:
    for event_id, prev_val in previous_values:
        if prev_val is sentinel:
            session.widget_store.pop(event_id, None)
        else:
            session.widget_store[event_id] = prev_val


def _fragment_ids_for_rerun(
    session: Session,
    rerun_event_ids: list[str],
) -> tuple[list[str], bool]:
    fragment_ids: list[str] = []
    seen: set[str] = set()
    has_non_fragment_event = False

    for event_id in rerun_event_ids:
        fragment_id = session._widget_to_fragment.get(event_id)
        if fragment_id is None:
            has_non_fragment_event = True
            continue
        if fragment_id in seen:
            continue
        seen.add(fragment_id)
        fragment_ids.append(fragment_id)

    return fragment_ids, has_non_fragment_event


async def _run_full_session(
    *,
    session: Session,
    websocket: WebSocket,
    node_cache: dict[str, dict[str, Any]],
    session_lock: asyncio.Lock,
    session_store: SessionStore,
    session_record: SessionRecord | None,
    runtime_state: _ProcessRuntimeState | None,
    events: list[WidgetEvent],
    force_full_render: bool,
    progressive: bool,
) -> RenderFull | RenderPatch | None:
    return await _run_session_op_with_runtime_events(
        lambda: session.run(
            force_full_render=force_full_render,
            progressive=progressive,
        ),
        session=session,
        websocket=websocket,
        node_cache=node_cache,
        session_lock=session_lock,
        session_store=session_store,
        session_record=session_record,
        runtime_state=runtime_state,
        command_name="run",
        payload={
            "force_full_render": force_full_render,
            "progressive": progressive,
        },
        events=events,
    )


async def _run_best_effort_batch(
    *,
    session: Session,
    websocket: WebSocket,
    node_cache: dict[str, dict[str, Any]],
    session_lock: asyncio.Lock,
    session_store: SessionStore,
    session_record: SessionRecord | None,
    runtime_state: _ProcessRuntimeState | None,
    batch: list[WidgetEvent],
    rerun_event_ids: list[str],
) -> tuple[RenderFull | RenderPatch | None, bool]:
    force_full_render, progressive = _render_flags_for_event_batch(
        session,
        rerun_event_ids,
    )

    fragment_ids, has_non_fragment_event = _fragment_ids_for_rerun(
        session,
        rerun_event_ids,
    )

    if _should_run_full_session_for_events(
        session,
        rerun_event_ids,
        has_non_fragment_event=has_non_fragment_event,
    ):
        result = await _run_full_session(
            session=session,
            websocket=websocket,
            node_cache=node_cache,
            session_lock=session_lock,
            session_store=session_store,
            session_record=session_record,
            runtime_state=runtime_state,
            events=batch,
            force_full_render=force_full_render,
            progressive=progressive,
        )
        return result, True

    if len(fragment_ids) == 1:
        result = await _run_session_op_with_runtime_events(
            lambda: session.run_fragment(fragment_ids[0]),
            session=session,
            websocket=websocket,
            node_cache=node_cache,
            session_lock=session_lock,
            session_store=session_store,
            session_record=session_record,
            runtime_state=runtime_state,
            command_name="run_fragment",
            payload={"fragment_id": fragment_ids[0]},
            events=batch,
        )
        if result is not None:
            return result, False

    elif len(fragment_ids) > 1:
        result = await _run_session_op_with_runtime_events(
            lambda: session.run_fragments(fragment_ids),
            session=session,
            websocket=websocket,
            node_cache=node_cache,
            session_lock=session_lock,
            session_store=session_store,
            session_record=session_record,
            runtime_state=runtime_state,
            command_name="run_fragments",
            payload={"fragment_ids": fragment_ids},
            events=batch,
        )
        if result is not None:
            return result, False

    result = await _run_full_session(
        session=session,
        websocket=websocket,
        node_cache=node_cache,
        session_lock=session_lock,
        session_store=session_store,
        session_record=session_record,
        runtime_state=runtime_state,
        events=batch,
        force_full_render=force_full_render,
        progressive=progressive,
    )
    return result, True


async def _accept_and_prepare_session(
    websocket: WebSocket,
    *,
    session: Session,
    script_path: str,
    session_record: SessionRecord | None,
) -> _ProcessRuntimeState | None:
    await websocket.accept()

    session_store = _get_session_store(websocket)
    await _touch_session(
        session_store,
        session.session_id,
        session_record=session_record,
    )

    if not _validate_and_copy_query_params(websocket, session):
        await websocket.close(code=1008, reason="Invalid query parameters")
        raise _WebSocketClosedError("Invalid query parameters")

    try:
        auth_cfg = _auth_cfg_for_websocket(websocket)
        if auth_cfg:
            from fastlit.server.auth import resolve_auth_claims

            cookie_name = auth_cfg.get("cookie_name", "fl_session")
            cookie_value = _extract_ws_cookie(websocket, cookie_name)
            if cookie_value:
                claims = resolve_auth_claims(cookie_value, auth_cfg, websocket.scope.get("app"))
                if claims:
                    session.user_claims = claims
    except Exception:
        pass

    if not _process_runtime_enabled():
        return None

    runtime_state = _ProcessRuntimeState(
        worker=SessionProcessWorker(
            script_path=script_path,
            session_id=session.session_id,
        ),
        committed_snapshot=session.snapshot_state(),
    )
    await runtime_state.worker.sync_snapshot(runtime_state.committed_snapshot)

    if session_record is not None:
        session_record.process_worker = runtime_state.worker

    return runtime_state


async def _perform_initial_render(
    *,
    websocket: WebSocket,
    session: Session,
    session_store: SessionStore,
    session_lock: asyncio.Lock,
    node_cache: dict[str, dict[str, Any]],
    fragment_timers: dict[str, asyncio.Task],
    deferred_fragment_tasks: set[asyncio.Task],
    session_record: SessionRecord | None,
    runtime_state: _ProcessRuntimeState | None,
) -> None:
    try:
        t0 = time.perf_counter()
        cpu0 = time.process_time()

        result = await _run_session_op_with_runtime_events(
            lambda: session.run(progressive=True),
            session=session,
            websocket=websocket,
            node_cache=node_cache,
            session_lock=session_lock,
            session_store=session_store,
            session_record=session_record,
            runtime_state=runtime_state,
            command_name="run",
            payload={"force_full_render": False, "progressive": True},
        )

        t1 = time.perf_counter()
        cpu1 = time.process_time()
        metrics.record_run(
            (t1 - t0) * 1000,
            cpu_duration_ms=(cpu1 - cpu0) * 1000,
            session_id=session.session_id,
        )

    except asyncio.TimeoutError:
        await _send_error(
            websocket,
            node_cache,
            f"Initial render exceeded timeout of {_RUN_TIMEOUT_SECONDS:.1f}s",
        )
        await websocket.close(code=1011, reason="Initial render timeout")
        raise _WebSocketClosedError("Initial render timeout")

    except SessionProcessExecutionError as exc:
        if exc.worker_traceback:
            logger.error(
                "Worker execution error during initial render: %s\n%s",
                exc,
                exc.worker_traceback,
            )
        else:
            logger.error("Worker execution error during initial render: %s", exc)

        await _send_error(
            websocket,
            node_cache,
            "An internal error occurred during initial render.",
        )
        await websocket.close(code=1011, reason="Initial render error")
        raise _WebSocketClosedError("Initial render error")

    except SessionProcessCrashedError as exc:
        logger.error("Session worker crashed during initial render: %s", exc)
        await _send_error(
            websocket,
            node_cache,
            "The session worker crashed during initial render.",
        )
        await websocket.close(code=1011, reason="Initial render crash")
        raise _WebSocketClosedError("Initial render crash")

    except _PayloadSerializationError:
        await websocket.close(code=1011, reason="Initial render serialization error")
        raise _WebSocketClosedError("Initial render serialization error")

    if result is None:
        await websocket.close(code=1011, reason="Initial render missing result")
        raise _WebSocketClosedError("Initial render missing result")

    delivery = await _deliver_render_result(
        result=result,
        did_full_run=True,
        websocket=websocket,
        session=session,
        node_cache=node_cache,
        session_lock=session_lock,
        session_store=session_store,
        session_record=session_record,
        fragment_timers=fragment_timers,
        deferred_fragment_tasks=deferred_fragment_tasks,
        runtime_state=runtime_state,
    )
    if delivery == "redirected":
        raise _WebSocketClosedError("Redirect sent during initial render")
    if delivery == "closed":
        raise _WebSocketClosedError("Initial render tree limit exceeded")
    if delivery != "sent":
        raise _WebSocketClosedError("Initial render did not produce a response")

    logger.debug("Sent initial render (rev=%d)", session.rev)


async def _process_event_batch(
    *,
    websocket: WebSocket,
    session: Session,
    session_store: SessionStore,
    session_lock: asyncio.Lock,
    runtime_state: _ProcessRuntimeState | None,
    node_cache: dict[str, dict[str, Any]],
    fragment_timers: dict[str, asyncio.Task],
    deferred_fragment_tasks: set[asyncio.Task],
    session_record: SessionRecord | None,
    batch: list[WidgetEvent],
) -> bool:
    rerun_event_ids, previous_values, sentinel = _event_batch_to_widget_store(session, batch)

    await _touch_session(
        session_store,
        session.session_id,
        session_record=session_record,
    )

    ok, reason = _session_limits_ok(session)
    if not ok:
        _rollback_widget_store_batch(session, previous_values, sentinel)
        await _send_error(
            websocket,
            node_cache,
            reason or "Session limits exceeded",
        )
        return True

    if not rerun_event_ids:
        if runtime_state is None:
            return True

        try:
            await _apply_events_to_process_runtime(
                batch,
                session=session,
                session_lock=session_lock,
                session_store=session_store,
                session_record=session_record,
                runtime_state=runtime_state,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Session %s state-sync timed out after %.1fs",
                session.session_id,
                _RUN_TIMEOUT_SECONDS,
            )
            await _send_error(
                websocket,
                node_cache,
                "State update exceeded the configured timeout.",
            )
        except SessionProcessCrashedError:
            logger.warning(
                "Session %s worker crashed while syncing state-only events",
                session.session_id,
            )
            await _send_error(
                websocket,
                node_cache,
                "The session worker restarted after a sync failure.",
            )

        return True

    try:
        t0 = time.perf_counter()
        cpu0 = time.process_time()

        result, did_full_run = await _run_best_effort_batch(
            session=session,
            websocket=websocket,
            node_cache=node_cache,
            session_lock=session_lock,
            session_store=session_store,
            session_record=session_record,
            runtime_state=runtime_state,
            batch=batch,
            rerun_event_ids=rerun_event_ids,
        )

        t1 = time.perf_counter()
        cpu1 = time.process_time()
        metrics.record_run(
            (t1 - t0) * 1000,
            cpu_duration_ms=(cpu1 - cpu0) * 1000,
            session_id=session.session_id,
        )

        result = session.coerce_widget_event_result(result, rerun_event_ids)
        if result is None:
            return True

        delivery = await _deliver_render_result(
            result=result,
            did_full_run=did_full_run,
            websocket=websocket,
            session=session,
            node_cache=node_cache,
            session_lock=session_lock,
            session_store=session_store,
            session_record=session_record,
            fragment_timers=fragment_timers,
            deferred_fragment_tasks=deferred_fragment_tasks,
            runtime_state=runtime_state,
        )
        if delivery == "closed":
            return False
        if delivery == "redirected":
            return True

        t2 = time.perf_counter()
        logger.info(
            "[TIMING] Rerun took %.3fms, send took %.3fms (rev=%d, batch=%d)",
            (t1 - t0) * 1000,
            (t2 - t1) * 1000,
            session.rev,
            len(batch),
        )

        return True

    except asyncio.TimeoutError:
        logger.warning(
            "Session %s rerun timed out after %.1fs",
            session.session_id,
            _RUN_TIMEOUT_SECONDS,
        )
        await _send_error(
            websocket,
            node_cache,
            f"Rerun exceeded timeout of {_RUN_TIMEOUT_SECONDS:.1f}s",
        )
        return True

    except _WebSocketClosedError:
        return False

    except SessionProcessExecutionError as exc:
        if exc.worker_traceback:
            logger.error(
                "Worker execution error during rerun: %s\n%s",
                exc,
                exc.worker_traceback,
            )
        else:
            logger.error("Worker execution error during rerun: %s", exc)

        await _send_error(
            websocket,
            node_cache,
            "An internal error occurred during script execution.",
        )
        return True

    except SessionProcessCrashedError as exc:
        logger.error("Session worker crashed during rerun: %s", exc)
        await _send_error(
            websocket,
            node_cache,
            "The session worker restarted after a crash.",
        )
        return True

    except _PayloadSerializationError:
        return True

    except Exception as exc:  # noqa: BLE001
        logger.error("Error during rerun: %s\n%s", exc, traceback.format_exc())
        await _send_error(
            websocket,
            node_cache,
            "An internal error occurred during script execution.",
        )
        return True


async def _admit_connection(
    *,
    websocket: WebSocket,
    session: Session,
    request_id: str,
    client_ip: str,
    session_store: SessionStore,
    sessions_lock: asyncio.Lock,
) -> tuple[bool, SessionRecord | None]:
    async with sessions_lock:
        now = time.monotonic()
        _cleanup_ip_state(now)

        if _is_ip_temporarily_blocked(client_ip, now):
            metrics.on_session_rejected()
            metrics.record_ws_ip_blocked(1)
            await websocket.close(code=1013, reason="IP temporarily blocked")
            return False, None

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
            return False, None

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
            return False, None

        if _WS_MAX_CONNECTS_PER_MINUTE > 0:
            history = _IP_CONNECT_HISTORY.get(client_ip)
            if history is None:
                history = deque()
                _remember_ip_tracking_value(_IP_CONNECT_HISTORY, client_ip, history)
            else:
                _IP_CONNECT_HISTORY.move_to_end(client_ip)

            _trim_window(history, now, 60.0)
            if len(history) >= _WS_MAX_CONNECTS_PER_MINUTE:
                metrics.on_session_rejected()
                metrics.record_ws_rate_limited(1)
                if _record_reject_and_maybe_block(client_ip, now):
                    logger.warning(
                        "Temporarily blocked IP %s for %.0fs after connect-rate rejects",
                        client_ip,
                        _WS_BLOCK_SECONDS,
                    )
                await websocket.close(code=1013, reason="Too many connection attempts")
                return False, None

            history.append(now)

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
            return False, None

        if _MAX_SESSIONS > 0 and await session_store.count() >= _MAX_SESSIONS:
            metrics.on_session_rejected()
            await websocket.close(code=1013, reason="Server at capacity")
            return False, None

        session_record = await session_store.add(
            session,
            websocket=websocket,
            client_ip=client_ip,
            request_id=request_id,
        )

        _remember_ip_tracking_value(_IP_ACTIVE_CONNECTIONS, client_ip, ip_active + 1)
        metrics.on_session_opened()
        return True, session_record


async def handle_websocket(websocket: WebSocket, script_path: str) -> None:
    session = Session(script_path)
    request_id = uuid.uuid4().hex
    admitted = False
    client_ip = _client_ip(websocket)
    session_store = _get_session_store(websocket)
    session_record: SessionRecord | None = None

    log_tokens = set_log_context(request_id=request_id, session_id=session.session_id)
    _, sessions_lock = _get_sync_primitives()

    reader_task: asyncio.Task | None = None
    node_cache: dict[str, dict[str, Any]] = OrderedDict()
    events_queue: asyncio.Queue[WidgetEvent | None] = asyncio.Queue(
        maxsize=_WS_EVENT_QUEUE_SIZE
    )
    fragment_timers: dict[str, asyncio.Task] = {}
    deferred_fragment_tasks: set[asyncio.Task] = set()
    runtime_state: _ProcessRuntimeState | None = None

    try:
        admitted, session_record = await _admit_connection(
            websocket=websocket,
            session=session,
            request_id=request_id,
            client_ip=client_ip,
            session_store=session_store,
            sessions_lock=sessions_lock,
        )
        if not admitted:
            return

        session_run_lock = session_record.run_lock if session_record is not None else asyncio.Lock()

        runtime_state = await _accept_and_prepare_session(
            websocket,
            session=session,
            script_path=script_path,
            session_record=session_record,
        )

        logger.info("Session connected (%s)", client_ip)

        await _perform_initial_render(
            websocket=websocket,
            session=session,
            session_store=session_store,
            session_lock=session_run_lock,
            node_cache=node_cache,
            fragment_timers=fragment_timers,
            deferred_fragment_tasks=deferred_fragment_tasks,
            session_record=session_record,
            runtime_state=runtime_state,
        )

        reader_task = asyncio.create_task(
            _ws_reader(
                websocket,
                events_queue,
                client_ip=client_ip,
                sessions_lock=sessions_lock,
                session_store=session_store,
                session_id=session.session_id,
                session_record=session_record,
            )
        )

        coalesce_window_s = _WS_COALESCE_WINDOW_MS / 1000.0

        while True:
            first_event = await events_queue.get()
            if first_event is None:
                break

            if coalesce_window_s > 0:
                await asyncio.sleep(coalesce_window_s)

            batch, saw_eof = _coalesce_events(
                first_event,
                events_queue,
                batch_limit=_WS_BATCH_LIMIT,
            )

            should_continue = await _process_event_batch(
                websocket=websocket,
                session=session,
                session_store=session_store,
                session_lock=session_run_lock,
                runtime_state=runtime_state,
                node_cache=node_cache,
                fragment_timers=fragment_timers,
                deferred_fragment_tasks=deferred_fragment_tasks,
                session_record=session_record,
                batch=batch,
            )
            if not should_continue or saw_eof:
                break

    except _WebSocketClosedError as exc:
        logger.info("Session disconnected: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.info("Session disconnected: %s", exc)
    finally:
        node_cache.clear()

        await _cancel_background_tasks(deferred_fragment_tasks)

        if reader_task is not None:
            reader_task.cancel()
            with suppress(BaseException):
                await reader_task

        if fragment_timers:
            for task in fragment_timers.values():
                task.cancel()
            await asyncio.gather(*fragment_timers.values(), return_exceptions=True)
            fragment_timers.clear()

        if runtime_state is not None:
            if session_record is not None:
                session_record.process_worker = None
            runtime_state.worker.close()

        if admitted:
            async with sessions_lock:
                removed = await session_store.remove(session.session_id)

                ip_active = _IP_ACTIVE_CONNECTIONS.get(client_ip, 0)
                if ip_active <= 1:
                    _IP_ACTIVE_CONNECTIONS.pop(client_ip, None)
                else:
                    _remember_ip_tracking_value(
                        _IP_ACTIVE_CONNECTIONS,
                        client_ip,
                        ip_active - 1,
                    )

                history = _IP_CONNECT_HISTORY.get(client_ip)
                if history:
                    _trim_window(history, time.monotonic(), 60.0)
                    if not history and client_ip not in _IP_ACTIVE_CONNECTIONS:
                        _IP_CONNECT_HISTORY.pop(client_ip, None)

                _cleanup_ip_state(time.monotonic(), force=True)

            if removed is not None:
                metrics.on_session_closed()

        logger.info("Session closed")
        reset_log_context(log_tokens)
