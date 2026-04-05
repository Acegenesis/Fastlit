"""Ephemeral server-side store for large DataFrame/table payloads."""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
import random
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable


_LOCK = threading.Lock()
_SOURCES: dict[str, "_DataFrameSource"] = {}
_MAX_SOURCES = max(32, int(os.environ.get("FASTLIT_DF_MAX_SOURCES", "512")))
_TTL_SECONDS = max(60, int(os.environ.get("FASTLIT_DF_TTL_SECONDS", "1800")))
_QUERY_CACHE_LIMIT = max(8, int(os.environ.get("FASTLIT_DF_QUERY_CACHE_LIMIT", "64")))
_MAX_TOTAL_BYTES = max(
    0, int(os.environ.get("FASTLIT_DF_MAX_TOTAL_BYTES", str(256 * 1024 * 1024)))
)
logger = logging.getLogger("fastlit.dataframe")
_SESSION_SOURCE_SEPARATOR = ":"


@dataclass(frozen=True)
class DataframeSort:
    column: str
    direction: str = "asc"


@dataclass(frozen=True)
class DataframeFilter:
    column: str
    op: str
    value: Any = None


@dataclass(frozen=True)
class DataframeQuery:
    offset: int = 0
    limit: int = 200
    search: str = ""
    sorts: tuple[DataframeSort, ...] = ()
    filters: tuple[DataframeFilter, ...] = ()

    def cache_key(self) -> str:
        payload = {
            "offset": self.offset,
            "limit": self.limit,
            "search": self.search,
            "sorts": [sort.__dict__ for sort in self.sorts],
            "filters": [flt.__dict__ for flt in self.filters],
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()


@dataclass
class _DataFrameSource:
    columns: list[dict[str, Any]]
    rows: list[list[Any]] | None
    index: list[Any] | None
    slice_fn: Callable[[int, int], tuple[list[list[Any]], list[Any] | None]] | None
    total_rows: int
    created_at: float
    last_access: float
    query_fn: Callable[[DataframeQuery], dict[str, Any]] | None = None
    export_fn: Callable[[DataframeQuery], dict[str, Any]] | None = None
    schema_version: str | None = None
    query_cache: OrderedDict[str, dict[str, Any]] = field(default_factory=OrderedDict)
    inflight_queries: dict[str, threading.Event] = field(default_factory=dict)
    inflight_results: dict[str, tuple[dict[str, Any] | None, BaseException | None]] = field(
        default_factory=dict
    )
    estimated_bytes: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _valid_columns: frozenset[str] | None = field(default=None, repr=False)

    @property
    def valid_columns(self) -> frozenset[str]:
        """Cached set of valid column names."""
        if self._valid_columns is None:
            self._valid_columns = frozenset(
                str(col.get("name", "")).strip()
                for col in self.columns
                if str(col.get("name", "")).strip()
            )
        return self._valid_columns


def _build_source_id(session_id: str | None = None) -> str:
    token = uuid.uuid4().hex
    if not session_id:
        return token
    return f"{session_id}{_SESSION_SOURCE_SEPARATOR}{token}"


def extract_session_id(source_id: str) -> str | None:
    prefix, separator, _suffix = source_id.partition(_SESSION_SOURCE_SEPARATOR)
    if separator != _SESSION_SOURCE_SEPARATOR:
        return None
    if len(prefix) != 32:
        return None
    if any(ch not in "0123456789abcdef" for ch in prefix.lower()):
        return None
    return prefix


def _prune(now: float) -> None:
    """Remove stale or excess sources. Caller MUST hold _LOCK."""
    stale = [sid for sid, src in _SOURCES.items() if (now - src.last_access) > _TTL_SECONDS]
    for sid in stale:
        _SOURCES.pop(sid, None)

    if len(_SOURCES) > _MAX_SOURCES:
        victims = sorted(
            _SOURCES.items(),
            key=lambda item: item[1].last_access,
        )[: len(_SOURCES) - _MAX_SOURCES]
        for sid, _src in victims:
            _SOURCES.pop(sid, None)

    if _MAX_TOTAL_BYTES > 0:
        total = sum(src.estimated_bytes for src in _SOURCES.values())
        if total > _MAX_TOTAL_BYTES:
            victims = sorted(
                _SOURCES.items(),
                key=lambda item: item[1].last_access,
            )
            for sid, src in victims:
                if total <= _MAX_TOTAL_BYTES:
                    break
                total -= max(0, src.estimated_bytes)
                _SOURCES.pop(sid, None)


def _estimate_payload_bytes(value: Any) -> int:
    """Estimate JSON byte size without serializing the full payload.

    For large row arrays, samples rows randomly and extrapolates to avoid
    serializing thousands of rows just to produce a size hint.
    """
    try:
        if isinstance(value, dict):
            rows = value.get("rows")
            if isinstance(rows, list) and len(rows) > 20:
                sample_size = min(20, len(rows))
                sample = random.sample(rows, sample_size)
                sample_bytes = len(
                    json.dumps(
                        sample,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        default=str,
                    ).encode("utf-8")
                )
                row_estimate = sample_bytes * len(rows) // sample_size
                # Add overhead for the rest of the payload (columns, meta, etc.)
                overhead = {k: v for k, v in value.items() if k != "rows"}
                overhead_bytes = len(
                    json.dumps(
                        overhead,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        default=str,
                    ).encode("utf-8")
                )
                return row_estimate + overhead_bytes
        return len(
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                default=str,
            ).encode("utf-8")
        )
    except Exception:
        return 0


def _estimate_source_bytes(src: _DataFrameSource) -> int:
    total = _estimate_payload_bytes(
        {
            "columns": src.columns,
            "rows": src.rows,
            "index": src.index,
            "total_rows": src.total_rows,
            "schema_version": src.schema_version,
        }
    )
    for payload in src.query_cache.values():
        total += _estimate_payload_bytes(payload)
    return total


def _copy_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Shallow-copy a query result payload.

    Row cell values (str, int, float, bool, None) are immutable — copying the
    container structures (outer dict, rows list, each row list) is sufficient.
    Column metadata dicts are also copied one level deep.
    If cells contain mutable objects, set FASTLIT_DF_DEEP_COPY_PAYLOAD=1 to
    restore deepcopy behaviour.
    """
    if os.environ.get("FASTLIT_DF_DEEP_COPY_PAYLOAD", "0").strip() in {"1", "true", "yes"}:
        return copy.deepcopy(payload)
    rows = payload.get("rows")
    columns = payload.get("columns")
    copied: dict[str, Any] = {k: v for k, v in payload.items() if k not in ("rows", "columns")}
    if rows is not None:
        copied["rows"] = [list(row) for row in rows]
    if columns is not None:
        copied["columns"] = [dict(col) for col in columns]
    return copied


def _decorate_payload(
    payload: dict[str, Any],
    *,
    started_at: float,
    cache_hit: bool,
) -> dict[str, Any]:
    out = _copy_payload(payload)
    out["_fastlitMeta"] = {
        "cacheHit": cache_hit,
        "elapsedMs": round((time.perf_counter() - started_at) * 1000, 3),
    }
    return out


def _set_query_cache(src: _DataFrameSource, cache_key: str, payload: dict[str, Any]) -> None:
    src.query_cache[cache_key] = payload
    src.query_cache.move_to_end(cache_key)
    while len(src.query_cache) > _QUERY_CACHE_LIMIT:
        src.query_cache.popitem(last=False)


def register_source(
    *,
    columns: list[dict[str, Any]],
    rows: list[list[Any]] | None,
    index: list[Any] | None = None,
    slice_fn: Callable[[int, int], tuple[list[list[Any]], list[Any] | None]] | None = None,
    total_rows: int,
    query_fn: Callable[[DataframeQuery], dict[str, Any]] | None = None,
    export_fn: Callable[[DataframeQuery], dict[str, Any]] | None = None,
    schema_version: str | None = None,
    session_id: str | None = None,
) -> str:
    """Register a tabular source and return an opaque ID."""
    now = time.time()
    source_id = _build_source_id(session_id)
    src = _DataFrameSource(
        columns=columns,
        rows=rows,
        index=index,
        slice_fn=slice_fn,
        total_rows=total_rows,
        created_at=now,
        last_access=now,
        query_fn=query_fn,
        export_fn=export_fn,
        schema_version=schema_version,
    )
    src.estimated_bytes = _estimate_source_bytes(src)
    with _LOCK:
        _SOURCES[source_id] = src
        _prune(now)
    return source_id


def get_slice(source_id: str, query: DataframeQuery) -> dict[str, Any] | None:
    """Return a row window for a registered source."""
    started_at = time.perf_counter()
    now = time.time()
    with _LOCK:
        _prune(now)
        src = _SOURCES.get(source_id)
        if src is None:
            return None
        src.last_access = now

    should_wait = False
    inflight: threading.Event | None = None
    cache_key = ""
    normalized_query: DataframeQuery | None = None
    valid_cols: frozenset[str]

    with src.lock:
        valid_cols = src.valid_columns
        valid_sorts: list[DataframeSort] = []
        for sort in query.sorts:
            if sort.column in valid_cols:
                valid_sorts.append(sort)
                continue
            logger.warning(
                "Ignoring invalid dataframe sort column=%s source_id=%s",
                sort.column,
                source_id,
            )
        normalized_input = DataframeQuery(
            offset=query.offset,
            limit=query.limit,
            search=query.search,
            sorts=tuple(valid_sorts),
            filters=query.filters,
        )
        cache_key = normalized_input.cache_key()
        cached = src.query_cache.get(cache_key)
        if cached is not None:
            src.query_cache.move_to_end(cache_key)
            src.last_access = time.time()
            return _decorate_payload(cached, started_at=started_at, cache_hit=True)

        total = src.total_rows
        safe_offset = max(0, min(int(normalized_input.offset), total))
        safe_limit = max(1, min(int(normalized_input.limit), 5000))
        normalized_query = DataframeQuery(
            offset=safe_offset,
            limit=safe_limit,
            search=normalized_input.search,
            sorts=normalized_input.sorts,
            filters=normalized_input.filters,
        )
        inflight = src.inflight_queries.get(cache_key)
        if inflight is None:
            src.inflight_results.pop(cache_key, None)
            inflight = threading.Event()
            src.inflight_queries[cache_key] = inflight
        else:
            should_wait = True

    if should_wait:
        assert inflight is not None
        inflight.wait()
        with src.lock:
            cached = src.query_cache.get(cache_key)
            if cached is not None:
                src.query_cache.move_to_end(cache_key)
                src.last_access = time.time()
                return _decorate_payload(cached, started_at=started_at, cache_hit=True)
            replay = src.inflight_results.get(cache_key)
        if replay is None:
            return None
        payload, error = replay
        if error is not None:
            raise error
        if payload is None:
            return None
        return _decorate_payload(payload, started_at=started_at, cache_hit=True)

    assert normalized_query is not None

    try:
        if src.query_fn is not None:
            payload = src.query_fn(normalized_query)
            payload.setdefault("sourceId", source_id)
            payload.setdefault("columns", src.columns)
            payload.setdefault("schemaVersion", src.schema_version)
        else:
            end = min(src.total_rows, normalized_query.offset + normalized_query.limit)
            if src.slice_fn is not None:
                out_rows, out_index = src.slice_fn(normalized_query.offset, end)
            else:
                out_rows = (src.rows or [])[normalized_query.offset:end]
                out_index = None
                if src.index is not None:
                    out_index = src.index[normalized_query.offset:end]

            payload = {
                "sourceId": source_id,
                "offset": normalized_query.offset,
                "limit": normalized_query.limit,
                "totalRows": src.total_rows,
                "columns": src.columns,
                "rows": out_rows,
                "index": out_index,
                "positions": list(range(normalized_query.offset, end)),
                "schemaVersion": src.schema_version,
            }
    except BaseException as exc:
        with src.lock:
            src.inflight_queries.pop(cache_key, None)
            src.inflight_results[cache_key] = (None, exc)
            if inflight is not None:
                inflight.set()
        raise

    stored_payload = {
        key: value for key, value in payload.items() if key != "_fastlitMeta"
    }
    with src.lock:
        _set_query_cache(src, cache_key, stored_payload)
        src.estimated_bytes = _estimate_source_bytes(src)
        src.last_access = time.time()
        src.inflight_queries.pop(cache_key, None)
        src.inflight_results[cache_key] = (stored_payload, None)
        if inflight is not None:
            inflight.set()
    with _LOCK:
        _prune(time.time())
    return _decorate_payload(stored_payload, started_at=started_at, cache_hit=False)
