"""Ephemeral server-side store for large DataFrame/table payloads."""

from __future__ import annotations

import os
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable


_LOCK = threading.Lock()
_SOURCES: dict[str, "_DataFrameSource"] = {}
_MAX_SOURCES = max(32, int(os.environ.get("FASTLIT_DF_MAX_SOURCES", "512")))
_TTL_SECONDS = max(60, int(os.environ.get("FASTLIT_DF_TTL_SECONDS", "1800")))


@dataclass
class _DataFrameSource:
    columns: list[dict[str, Any]]
    rows: list[list[Any]] | None
    index: list[Any] | None
    slice_fn: Callable[[int, int], tuple[list[list[Any]], list[Any] | None]] | None
    total_rows: int
    created_at: float
    last_access: float


def _prune(now: float) -> None:
    stale = [
        sid
        for sid, src in _SOURCES.items()
        if (now - src.last_access) > _TTL_SECONDS
    ]
    for sid in stale:
        _SOURCES.pop(sid, None)

    if len(_SOURCES) > _MAX_SOURCES:
        # LRU-style trim by last access time.
        victims = sorted(
            _SOURCES.items(),
            key=lambda item: item[1].last_access,
        )[: len(_SOURCES) - _MAX_SOURCES]
        for sid, _src in victims:
            _SOURCES.pop(sid, None)


def register_source(
    *,
    columns: list[dict[str, Any]],
    rows: list[list[Any]] | None,
    index: list[Any] | None = None,
    slice_fn: Callable[[int, int], tuple[list[list[Any]], list[Any] | None]] | None = None,
    total_rows: int,
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
    )
    with _LOCK:
        _SOURCES[source_id] = src
        _prune(now)
    return source_id


def get_slice(source_id: str, offset: int, limit: int) -> dict[str, Any] | None:
    """Return a row window for a registered source."""
    with _LOCK:
        src = _SOURCES.get(source_id)
        if src is None:
            return None
        src.last_access = time.time()

        total = src.total_rows
        safe_offset = max(0, min(offset, total))
        safe_limit = max(1, min(limit, 5000))
        end = min(total, safe_offset + safe_limit)

        if src.slice_fn is not None:
            out_rows, out_index = src.slice_fn(safe_offset, end)
        else:
            out_rows = (src.rows or [])[safe_offset:end]
            out_index = None
            if src.index is not None:
                out_index = src.index[safe_offset:end]

        return {
            "sourceId": source_id,
            "offset": safe_offset,
            "limit": safe_limit,
            "totalRows": total,
            "columns": src.columns,
            "rows": out_rows,
            "index": out_index,
        }
