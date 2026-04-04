"""In-memory runtime metrics for Fastlit server."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import deque
from typing import Any

_SLOW_RERUN_THRESHOLD_MS = float(os.environ.get("FASTLIT_SLOW_RERUN_MS", "100"))
_perf_logger = logging.getLogger("fastlit.perf")

_LOCK = threading.Lock()
_START_TIME = time.time()
_BOOT_ID = f"{os.getpid()}-{int(_START_TIME * 1000)}"

_STATE: dict[str, Any] = {
    "active_sessions": 0,
    "total_sessions_opened": 0,
    "total_sessions_rejected": 0,
    "total_session_timeouts": 0,
    "total_runs": 0,
    "total_run_ms": 0.0,
    "last_run_ms": 0.0,
    "max_run_ms": 0.0,
    "total_run_cpu_ms": 0.0,
    "last_run_cpu_ms": 0.0,
    "max_run_cpu_ms": 0.0,
    "total_messages_sent": 0,
    "total_payload_bytes": 0,
    "last_payload_bytes": 0,
    "max_payload_bytes": 0,
    "last_message_type": None,
    "total_events_dropped": 0,
    "total_ws_origin_rejected": 0,
    "total_ws_auth_rejected": 0,
    "total_ws_rate_limited": 0,
    "total_ws_ip_banned": 0,
    "total_ws_ip_blocked": 0,
    "total_http_rate_limited": 0,
    "last_session_memory_bytes": 0,
    "max_session_memory_bytes": 0,
    "session_memory_budget_bytes": 0,
    "total_session_memory_near_limit": 0,
}
_RUN_SAMPLES: deque[float] = deque(maxlen=2048)
_PAYLOAD_SAMPLES: deque[float] = deque(maxlen=2048)


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


def record_run(duration_ms: float, *, cpu_duration_ms: float | None = None, session_id: str | None = None) -> None:
    if duration_ms > _SLOW_RERUN_THRESHOLD_MS:
        session_id_str = session_id[:8] if session_id else "?"
        _perf_logger.warning(
            "Slow rerun: %.1fms (session=%s) — set FASTLIT_SLOW_RERUN_MS to adjust threshold",
            duration_ms,
            session_id_str,
        )
    with _LOCK:
        _STATE["total_runs"] += 1
        _STATE["total_run_ms"] += duration_ms
        _STATE["last_run_ms"] = duration_ms
        if duration_ms > _STATE["max_run_ms"]:
            _STATE["max_run_ms"] = duration_ms
        if cpu_duration_ms is not None:
            _STATE["total_run_cpu_ms"] += cpu_duration_ms
            _STATE["last_run_cpu_ms"] = cpu_duration_ms
            if cpu_duration_ms > _STATE["max_run_cpu_ms"]:
                _STATE["max_run_cpu_ms"] = cpu_duration_ms
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


def record_ws_origin_rejected(count: int = 1) -> None:
    with _LOCK:
        _STATE["total_ws_origin_rejected"] += max(0, int(count))


def record_ws_auth_rejected(count: int = 1) -> None:
    with _LOCK:
        _STATE["total_ws_auth_rejected"] += max(0, int(count))


def record_ws_rate_limited(count: int = 1) -> None:
    with _LOCK:
        _STATE["total_ws_rate_limited"] += max(0, int(count))


def record_ws_ip_blocked(count: int = 1) -> None:
    with _LOCK:
        _STATE["total_ws_ip_blocked"] += max(0, int(count))


def record_ws_ip_banned(count: int = 1) -> None:
    with _LOCK:
        _STATE["total_ws_ip_banned"] += max(0, int(count))


def record_http_rate_limited(count: int = 1) -> None:
    with _LOCK:
        _STATE["total_http_rate_limited"] += max(0, int(count))


def record_session_timeout(count: int = 1) -> None:
    with _LOCK:
        _STATE["total_session_timeouts"] += max(0, int(count))


def record_session_memory(usage_bytes: int, *, budget_bytes: int = 0) -> None:
    with _LOCK:
        _STATE["last_session_memory_bytes"] = max(0, int(usage_bytes))
        if usage_bytes > _STATE["max_session_memory_bytes"]:
            _STATE["max_session_memory_bytes"] = max(0, int(usage_bytes))
        _STATE["session_memory_budget_bytes"] = max(0, int(budget_bytes))
        if budget_bytes > 0 and usage_bytes >= (budget_bytes / 2):
            _STATE["total_session_memory_near_limit"] += 1


def snapshot() -> dict[str, Any]:
    with _LOCK:
        total_runs = _STATE["total_runs"]
        total_messages = _STATE["total_messages_sent"]
        avg_run_ms = (_STATE["total_run_ms"] / total_runs) if total_runs else 0.0
        avg_run_cpu_ms = (_STATE["total_run_cpu_ms"] / total_runs) if total_runs else 0.0
        avg_payload_bytes = (
            _STATE["total_payload_bytes"] / total_messages if total_messages else 0.0
        )
        state_copy = dict(_STATE)
        run_samples = list(_RUN_SAMPLES)
        payload_samples = list(_PAYLOAD_SAMPLES)

    from fastlit.runtime import script_runner
    from fastlit.cache import data_cache_stats

    state_copy["avg_run_ms"] = avg_run_ms
    state_copy["avg_run_cpu_ms"] = avg_run_cpu_ms
    state_copy["avg_payload_bytes"] = avg_payload_bytes
    state_copy["boot_id"] = _BOOT_ID
    state_copy["process_id"] = os.getpid()
    state_copy["uptime_seconds"] = time.time() - _START_TIME
    state_copy["run_ms_p50"] = _percentile(run_samples, 0.50)
    state_copy["run_ms_p95"] = _percentile(run_samples, 0.95)
    state_copy["run_ms_p99"] = _percentile(run_samples, 0.99)
    state_copy["payload_bytes_p50"] = _percentile(payload_samples, 0.50)
    state_copy["payload_bytes_p95"] = _percentile(payload_samples, 0.95)
    state_copy["payload_bytes_p99"] = _percentile(payload_samples, 0.99)
    state_copy["script_cache_hits"] = script_runner.cache_stats()["hits"]
    state_copy["script_cache_misses"] = script_runner.cache_stats()["misses"]
    state_copy["script_cache_entries"] = script_runner.cache_stats()["entries"]
    cache_stats = data_cache_stats()
    state_copy["data_cache_hits"] = cache_stats["hits"]
    state_copy["data_cache_misses"] = cache_stats["misses"]
    state_copy["data_cache_waiters"] = cache_stats["waiters"]
    state_copy["data_cache_wait_ms_total"] = cache_stats["wait_ms_total"]
    return state_copy


def prometheus_text() -> str:
    snap = snapshot()
    lines = [
        "# HELP fastlit_active_sessions Active websocket sessions.",
        "# TYPE fastlit_active_sessions gauge",
        f"fastlit_active_sessions {snap['active_sessions']}",
        "# HELP fastlit_total_sessions_opened Total opened websocket sessions.",
        "# TYPE fastlit_total_sessions_opened counter",
        f"fastlit_total_sessions_opened {snap['total_sessions_opened']}",
        "# HELP fastlit_total_sessions_rejected Total rejected websocket sessions.",
        "# TYPE fastlit_total_sessions_rejected counter",
        f"fastlit_total_sessions_rejected {snap['total_sessions_rejected']}",
        "# HELP fastlit_total_session_timeouts Total sessions closed by idle timeout.",
        "# TYPE fastlit_total_session_timeouts counter",
        f"fastlit_total_session_timeouts {snap['total_session_timeouts']}",
        "# HELP fastlit_last_run_ms Last run wall-clock duration.",
        "# TYPE fastlit_last_run_ms gauge",
        f"fastlit_last_run_ms {snap['last_run_ms']}",
        "# HELP fastlit_last_run_cpu_ms Last run CPU duration.",
        "# TYPE fastlit_last_run_cpu_ms gauge",
        f"fastlit_last_run_cpu_ms {snap['last_run_cpu_ms']}",
        "# HELP fastlit_last_payload_bytes Last outbound payload size.",
        "# TYPE fastlit_last_payload_bytes gauge",
        f"fastlit_last_payload_bytes {snap['last_payload_bytes']}",
        "# HELP fastlit_last_session_memory_bytes Last measured session memory usage.",
        "# TYPE fastlit_last_session_memory_bytes gauge",
        f"fastlit_last_session_memory_bytes {snap['last_session_memory_bytes']}",
        "# HELP fastlit_script_cache_hits Script cache hits.",
        "# TYPE fastlit_script_cache_hits counter",
        f"fastlit_script_cache_hits {snap['script_cache_hits']}",
        "# HELP fastlit_script_cache_misses Script cache misses.",
        "# TYPE fastlit_script_cache_misses counter",
        f"fastlit_script_cache_misses {snap['script_cache_misses']}",
        "# HELP fastlit_uptime_seconds Process uptime in seconds.",
        "# TYPE fastlit_uptime_seconds gauge",
        f"fastlit_uptime_seconds {snap['uptime_seconds']}",
    ]
    return "\n".join(lines) + "\n"
