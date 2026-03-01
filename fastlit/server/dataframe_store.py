"""Ephemeral server-side store for large DataFrame/table payloads."""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


_LOCK = threading.Lock()
_SOURCES: dict[str, "_DataFrameSource"] = {}
_MAX_SOURCES = max(32, int(os.environ.get("FASTLIT_DF_MAX_SOURCES", "512")))
_TTL_SECONDS = max(60, int(os.environ.get("FASTLIT_DF_TTL_SECONDS", "1800")))
_QUERY_CACHE_LIMIT = max(8, int(os.environ.get("FASTLIT_DF_QUERY_CACHE_LIMIT", "64")))


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
    query_cache: dict[str, tuple[float, dict[str, Any]]] = field(default_factory=dict)


def _prune(now: float) -> None:
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


def _set_query_cache(src: _DataFrameSource, cache_key: str, payload: dict[str, Any]) -> None:
    src.query_cache[cache_key] = (time.time(), payload)
    if len(src.query_cache) <= _QUERY_CACHE_LIMIT:
        return
    victims = sorted(src.query_cache.items(), key=lambda item: item[1][0])[
        : len(src.query_cache) - _QUERY_CACHE_LIMIT
    ]
    for key, _value in victims:
        src.query_cache.pop(key, None)


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
) -> str:
    """Register a tabular source and return an opaque ID."""
    now = time.time()
    source_id = uuid.uuid4().hex
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
    with _LOCK:
        _SOURCES[source_id] = src
        _prune(now)
    return source_id


def get_slice(source_id: str, query: DataframeQuery) -> dict[str, Any] | None:
    """Return a row window for a registered source."""
    with _LOCK:
        src = _SOURCES.get(source_id)
        if src is None:
            return None
        src.last_access = time.time()

        cache_key = query.cache_key()
        cached = src.query_cache.get(cache_key)
        if cached is not None:
            return cached[1]

        total = src.total_rows
        safe_offset = max(0, min(int(query.offset), total))
        safe_limit = max(1, min(int(query.limit), 5000))
        normalized_query = DataframeQuery(
            offset=safe_offset,
            limit=safe_limit,
            search=query.search,
            sorts=query.sorts,
            filters=query.filters,
        )

        if src.query_fn is not None:
            payload = src.query_fn(normalized_query)
            payload.setdefault("sourceId", source_id)
            payload.setdefault("columns", src.columns)
            payload.setdefault("schemaVersion", src.schema_version)
            _set_query_cache(src, cache_key, payload)
            return payload

        end = min(total, safe_offset + safe_limit)
        if src.slice_fn is not None:
            out_rows, out_index = src.slice_fn(safe_offset, end)
        else:
            out_rows = (src.rows or [])[safe_offset:end]
            out_index = None
            if src.index is not None:
                out_index = src.index[safe_offset:end]

        payload = {
            "sourceId": source_id,
            "offset": safe_offset,
            "limit": safe_limit,
            "totalRows": total,
            "columns": src.columns,
            "rows": out_rows,
            "index": out_index,
            "positions": list(range(safe_offset, end)),
            "schemaVersion": src.schema_version,
        }
        _set_query_cache(src, cache_key, payload)
        return payload
