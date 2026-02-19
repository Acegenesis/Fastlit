"""In-memory runtime metrics for Fastlit server."""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from typing import Any

_LOCK = threading.Lock()
_START_TIME = time.time()

_STATE: dict[str, Any] = {
    "active_sessions": 0,
    "total_sessions_opened": 0,
    "total_sessions_rejected": 0,
    "total_runs": 0,
    "total_run_ms": 0.0,
    "last_run_ms": 0.0,
    "max_run_ms": 0.0,
    "total_messages_sent": 0,
    "total_payload_bytes": 0,
    "last_payload_bytes": 0,
    "max_payload_bytes": 0,
    "last_message_type": None,
    "total_events_dropped": 0,
}
_RUN_SAMPLES = deque(maxlen=2048)
_PAYLOAD_SAMPLES = deque(maxlen=2048)


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    idx = int(round((len(vals) - 1) * p))
    idx = max(0, min(idx, len(vals) - 1))
    return float(vals[idx])


def on_session_opened() -> None:
    with _LOCK:
        _STATE["active_sessions"] += 1
        _STATE["total_sessions_opened"] += 1


def on_session_closed() -> None:
    with _LOCK:
        _STATE["active_sessions"] = max(0, _STATE["active_sessions"] - 1)


def on_session_rejected() -> None:
    with _LOCK:
        _STATE["total_sessions_rejected"] += 1


def record_run(duration_ms: float) -> None:
    with _LOCK:
        _STATE["total_runs"] += 1
        _STATE["total_run_ms"] += duration_ms
        _STATE["last_run_ms"] = duration_ms
        if duration_ms > _STATE["max_run_ms"]:
            _STATE["max_run_ms"] = duration_ms
        _RUN_SAMPLES.append(float(duration_ms))


def record_outbound_message(
    payload: dict[str, Any] | None = None,
    *,
    size_bytes: int | None = None,
    message_type: str | None = None,
) -> None:
    """Record outbound WS payload stats.

    For best performance, pass ``size_bytes`` + ``message_type`` directly to
    avoid a second JSON serialization pass.
    """
    if size_bytes is None:
        if payload is None:
            raise ValueError("payload required when size_bytes is not provided")
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        size_bytes = len(body.encode("utf-8"))
    if message_type is None and payload is not None:
        message_type = payload.get("type")

    with _LOCK:
        _STATE["total_messages_sent"] += 1
        _STATE["total_payload_bytes"] += size_bytes
        _STATE["last_payload_bytes"] = size_bytes
        if size_bytes > _STATE["max_payload_bytes"]:
            _STATE["max_payload_bytes"] = size_bytes
        _STATE["last_message_type"] = message_type
        _PAYLOAD_SAMPLES.append(float(size_bytes))


def record_dropped_event(count: int = 1) -> None:
    with _LOCK:
        _STATE["total_events_dropped"] += max(0, int(count))


def snapshot() -> dict[str, Any]:
    with _LOCK:
        total_runs = _STATE["total_runs"]
        total_messages = _STATE["total_messages_sent"]
        avg_run_ms = (_STATE["total_run_ms"] / total_runs) if total_runs else 0.0
        avg_payload_bytes = (
            _STATE["total_payload_bytes"] / total_messages if total_messages else 0.0
        )
        state_copy = dict(_STATE)
        run_samples = list(_RUN_SAMPLES)
        payload_samples = list(_PAYLOAD_SAMPLES)

    state_copy["avg_run_ms"] = avg_run_ms
    state_copy["avg_payload_bytes"] = avg_payload_bytes
    state_copy["uptime_seconds"] = time.time() - _START_TIME
    state_copy["run_ms_p50"] = _percentile(run_samples, 0.50)
    state_copy["run_ms_p95"] = _percentile(run_samples, 0.95)
    state_copy["run_ms_p99"] = _percentile(run_samples, 0.99)
    state_copy["payload_bytes_p50"] = _percentile(payload_samples, 0.50)
    state_copy["payload_bytes_p95"] = _percentile(payload_samples, 0.95)
    state_copy["payload_bytes_p99"] = _percentile(payload_samples, 0.99)
    return state_copy
