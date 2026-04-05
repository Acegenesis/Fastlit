"""Caching decorators for Fastlit: cache_data and cache_resource.

These caches are process-global and shared across all Fastlit sessions, which
matches Streamlit's caching model.
"""

from __future__ import annotations

import asyncio
import copy as _copy
import datetime as _dt
import enum
import functools
import hashlib
import inspect
import threading
import time
from collections.abc import Awaitable, Coroutine
from collections import OrderedDict
from typing import Any, Callable, TypeVar, cast

from fastlit.ui.widget_value import LiveValue, WidgetValue

F = TypeVar("F", bound=Callable[..., Any])

_lock = threading.Lock()

_DATA_CACHE_MAX = 1000

# Global stores shared across all sessions.
_data_cache: OrderedDict[str, tuple[Any, float | None]] = OrderedDict()
_resource_cache: dict[str, tuple[Any, Callable[[Any], Any] | None]] = {}
_resource_key_locks: dict[str, threading.Lock] = {}
_data_inflight: dict[str, threading.Event] = {}
_data_inflight_results: dict[str, tuple[Any, BaseException | None]] = {}
_data_cache_metrics = {
    "hits": 0,
    "misses": 0,
    "waiters": 0,
    "wait_ms_total": 0.0,
}
_MISSING = object()


def _copy_cached_value(value: Any) -> Any:
    """Copy cached data while preserving isolation for mutable values."""
    if value is None or isinstance(value, (bool, int, float, complex, str, bytes)):
        return value
    try:
        import pandas as pd

        if isinstance(value, (pd.DataFrame, pd.Series)):
            return value.copy(deep=True)
    except ImportError:
        pass
    try:
        import numpy as np

        if isinstance(value, np.ndarray):
            return value.copy()
        if isinstance(value, np.generic):
            return value.item()
    except ImportError:
        pass
    return _copy.deepcopy(value)


def _run_cleanup_sync(cleanup: Callable[[Any], Any] | None, value: Any) -> None:
    if cleanup is None:
        return
    result = cleanup(value)
    if isinstance(result, Awaitable):
        coroutine = _coerce_coroutine(result)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(coroutine)
        else:
            loop.create_task(coroutine)


async def _run_cleanup_async(cleanup: Callable[[Any], Any] | None, value: Any) -> None:
    if cleanup is None:
        return
    result = cleanup(value)
    if isinstance(result, Awaitable):
        await _coerce_coroutine(result)


def _coerce_coroutine(result: Awaitable[Any]) -> Coroutine[Any, Any, Any]:
    if asyncio.iscoroutine(result):
        return cast(Coroutine[Any, Any, Any], result)

    async def _await_result() -> Any:
        return await result

    return _await_result()


def _function_cache_prefix(func: Callable) -> str:
    """Build a deterministic function fingerprint used as a key prefix."""
    try:
        source = inspect.getsource(func)
    except (OSError, TypeError):
        source = func.__qualname__
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _hash_cache_value(hasher: "hashlib._Hash", value: Any) -> None:
    if isinstance(value, (WidgetValue, LiveValue)):
        _hash_cache_value(hasher, value._val)
        return
    if value is None:
        hasher.update(b"n")
        return
    if isinstance(value, bool):
        hasher.update(b"b1" if value else b"b0")
        return
    if isinstance(value, int):
        hasher.update(b"i")
        hasher.update(str(value).encode("utf-8"))
        return
    if isinstance(value, float):
        hasher.update(b"f")
        hasher.update(repr(value).encode("utf-8"))
        return
    if isinstance(value, complex):
        hasher.update(b"c")
        hasher.update(repr(value).encode("utf-8"))
        return
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        hasher.update(b"s")
        hasher.update(len(encoded).to_bytes(8, "big"))
        hasher.update(encoded)
        return
    if isinstance(value, bytes):
        hasher.update(b"y")
        hasher.update(len(value).to_bytes(8, "big"))
        hasher.update(value)
        return
    if isinstance(value, _dt.datetime):
        hasher.update(b"dt")
        hasher.update(value.isoformat().encode("utf-8"))
        return
    if isinstance(value, _dt.date):
        hasher.update(b"dd")
        hasher.update(value.isoformat().encode("utf-8"))
        return
    if isinstance(value, _dt.time):
        hasher.update(b"tm")
        hasher.update(value.isoformat().encode("utf-8"))
        return
    if isinstance(value, _dt.timedelta):
        hasher.update(b"td")
        hasher.update(repr(value.total_seconds()).encode("utf-8"))
        return
    if isinstance(value, enum.Enum):
        hasher.update(b"en")
        hasher.update(type(value).__module__.encode("utf-8"))
        hasher.update(type(value).__qualname__.encode("utf-8"))
        _hash_cache_value(hasher, value.value)
        return
    if isinstance(value, (list, tuple)):
        hasher.update(b"l" if isinstance(value, list) else b"t")
        hasher.update(len(value).to_bytes(8, "big"))
        for item in value:
            _hash_cache_value(hasher, item)
        return
    if isinstance(value, dict):
        hasher.update(b"d")
        items = []
        for key, item in value.items():
            sub = hashlib.sha256()
            _hash_cache_value(sub, key)
            items.append((sub.digest(), key, item))
        for _digest, key, item in sorted(items, key=lambda entry: entry[0]):
            _hash_cache_value(hasher, key)
            _hash_cache_value(hasher, item)
        return
    if isinstance(value, (set, frozenset)):
        hasher.update(b"e" if isinstance(value, set) else b"r")
        digests = []
        for item in value:
            sub = hashlib.sha256()
            _hash_cache_value(sub, item)
            digests.append(sub.digest())
        for digest in sorted(digests):
            hasher.update(digest)
        return
    try:
        import numpy as np

        if isinstance(value, np.ndarray):
            arr = np.ascontiguousarray(value)
            hasher.update(b"na")
            hasher.update(str(arr.dtype).encode("utf-8"))
            hasher.update(str(arr.shape).encode("utf-8"))
            hasher.update(arr.tobytes())
            return
        if isinstance(value, np.generic):
            _hash_cache_value(hasher, value.item())
            return
    except ImportError:
        pass
    try:
        import pandas as pd

        if isinstance(value, pd.DataFrame):
            hashed = pd.util.hash_pandas_object(value, index=True).to_numpy()
            hasher.update(b"pdf")
            hasher.update("|".join(map(str, value.columns)).encode("utf-8"))
            hasher.update("|".join(map(str, value.dtypes.astype(str))).encode("utf-8"))
            hasher.update(hashed.tobytes())
            return
        if isinstance(value, pd.Series):
            hashed = pd.util.hash_pandas_object(value, index=True).to_numpy()
            hasher.update(b"pds")
            hasher.update(str(value.dtype).encode("utf-8"))
            hasher.update(hashed.tobytes())
            return
    except ImportError:
        pass
    try:
        import pyarrow as pa

        if isinstance(value, pa.Table):
            hasher.update(b"pat")
            _hash_cache_value(hasher, value.schema.to_string())
            _hash_cache_value(hasher, value.to_pydict())
            return
        if isinstance(value, pa.RecordBatch):
            hasher.update(b"par")
            _hash_cache_value(hasher, value.schema.to_string())
            _hash_cache_value(hasher, value.to_pydict())
            return
        if isinstance(value, (pa.Array, pa.ChunkedArray, pa.Scalar)):
            hasher.update(b"paa")
            _hash_cache_value(hasher, value.to_pylist() if hasattr(value, "to_pylist") else value.as_py())
            return
    except ImportError:
        pass

    raise TypeError(
        f"Unsupported cache_data argument type: {type(value).__module__}.{type(value).__qualname__}"
    )


def _make_cache_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """Build a deterministic cache key from function fingerprint + arguments."""
    prefix = _function_cache_prefix(func)
    hasher = hashlib.sha256()
    _hash_cache_value(hasher, args)
    _hash_cache_value(hasher, kwargs)
    args_hash = hasher.hexdigest()
    return f"{prefix}:{args_hash}"


def _clear_prefixed_cache(store: dict | OrderedDict, prefix: str) -> None:
    target = f"{prefix}:"
    keys = [k for k in store if k.startswith(target)]
    for key in keys:
        del store[key]


def cache_data(
    func: F | None = None,
    *,
    ttl: float | None = None,
    max_entries: int = _DATA_CACHE_MAX,
    copy: bool = True,
) -> Any:
    """Cache function results with optional TTL.

    Supports both ``@cache_data`` and ``@cache_data(ttl=60)`` syntax.
    Returns a deep copy of cached values by default to prevent mutation.
    Set ``copy=False`` for immutable return values to avoid deepcopy cost.
    """

    def decorator(fn: F) -> F:
        fn_prefix = _function_cache_prefix(fn)

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _make_cache_key(fn, args, kwargs)
            cached_value = _MISSING
            wait_started = 0.0
            should_wait = False
            flight: threading.Event | None = None

            with _lock:
                cached = _data_cache.get(key)
                if cached is not None:
                    value, expire_at = cached
                    now = time.monotonic()
                    if expire_at is None or now < expire_at:
                        _data_cache.move_to_end(key)
                        cached_value = value
                    # Expired.
                    else:
                        del _data_cache[key]
                if cached_value is _MISSING:
                    flight = _data_inflight.get(key)
                    if flight is None:
                        _data_inflight_results.pop(key, None)
                        flight = threading.Event()
                        _data_inflight[key] = flight
                    else:
                        should_wait = True
                        wait_started = time.perf_counter()
                        _data_cache_metrics["waiters"] += 1

            if cached_value is not _MISSING:
                with _lock:
                    _data_cache_metrics["hits"] += 1
                return _copy_cached_value(cached_value) if copy else cached_value

            if should_wait:
                assert flight is not None
                flight.wait()
                with _lock:
                    _data_cache_metrics["wait_ms_total"] += (
                        time.perf_counter() - wait_started
                    ) * 1000.0
                    cached = _data_cache.get(key)
                    if cached is not None:
                        value, expire_at = cached
                        now = time.monotonic()
                        if expire_at is None or now < expire_at:
                            _data_cache.move_to_end(key)
                            _data_cache_metrics["hits"] += 1
                            return _copy_cached_value(value) if copy else value
                        del _data_cache[key]
                    replay = _data_inflight_results.get(key)
                if replay is not None:
                    value, error = replay
                    if error is not None:
                        raise error
                    return _copy_cached_value(value) if copy else value

            with _lock:
                _data_cache_metrics["misses"] += 1

            # Compute outside lock.
            try:
                result = fn(*args, **kwargs)
            except BaseException as exc:
                with _lock:
                    inflight = _data_inflight.pop(key, None)
                    _data_inflight_results[key] = (_MISSING, exc)
                    if inflight is not None:
                        inflight.set()
                raise

            expire_at = (time.monotonic() + ttl) if ttl is not None else None
            with _lock:
                _data_cache[key] = (result, expire_at)
                _data_cache.move_to_end(key)
                while len(_data_cache) > max_entries:
                    _data_cache.popitem(last=False)
                inflight = _data_inflight.pop(key, None)
                _data_inflight_results[key] = (result, None)
                if inflight is not None:
                    inflight.set()

            return _copy_cached_value(result) if copy else result

        def _clear_fn_cache() -> None:
            with _lock:
                _clear_prefixed_cache(_data_cache, fn_prefix)

        wrapper.clear = _clear_fn_cache  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator


def data_cache_stats() -> dict[str, float]:
    with _lock:
        return dict(_data_cache_metrics)


def cache_resource(
    func: F | None = None,
    *,
    cleanup: Callable[[Any], Any] | None = None,
) -> Any:
    """Cache a resource (DB connection, pool, etc.) as a singleton.

    Resources are shared across all sessions in the current process.
    Optional ``cleanup=...`` callbacks run when the resource cache entry is
    cleared explicitly or during ASGI shutdown.
    """

    def decorator(fn: F) -> F:
        fn_prefix = _function_cache_prefix(fn)

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _make_cache_key(fn, args, kwargs)
            key_lock: threading.Lock | None = None

            with _lock:
                cached = _resource_cache.get(key, _MISSING)
                if cached is _MISSING:
                    key_lock = _resource_key_locks.get(key)
                    if key_lock is None:
                        key_lock = threading.Lock()
                        _resource_key_locks[key] = key_lock

            if cached is not _MISSING:
                cached_value, _ = cast(tuple[Any, Callable[[Any], Any] | None], cached)
                return cached_value
            assert key_lock is not None

            # Serialize creation per key so only one thread initializes.
            with key_lock:
                with _lock:
                    cached = _resource_cache.get(key, _MISSING)
                if cached is not _MISSING:
                    cached_value, _ = cast(tuple[Any, Callable[[Any], Any] | None], cached)
                    return cached_value

                created = fn(*args, **kwargs)

                with _lock:
                    existing = _resource_cache.get(key, _MISSING)
                    if existing is _MISSING:
                        _resource_cache[key] = (created, cleanup)
                        return created
                    existing_value, _ = cast(tuple[Any, Callable[[Any], Any] | None], existing)
                    return existing_value

        def _clear_fn_cache() -> None:
            removed: list[tuple[Any, Callable[[Any], Any] | None]] = []
            with _lock:
                target = f"{fn_prefix}:"
                keys = [k for k in _resource_cache if k.startswith(target)]
                for key in keys:
                    cached = _resource_cache.pop(key, None)
                    _resource_key_locks.pop(key, None)
                    if cached is not None:
                        removed.append(cached)
            for value, cleanup_fn in removed:
                _run_cleanup_sync(cleanup_fn, value)

        wrapper.clear = _clear_fn_cache  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator


async def clear_resource_caches() -> None:
    """Clear all cached resources and await any async cleanup callbacks."""
    removed: list[tuple[Any, Callable[[Any], Any] | None]] = []
    with _lock:
        removed.extend(_resource_cache.values())
        _resource_cache.clear()
        _resource_key_locks.clear()
    for value, cleanup in removed:
        await _run_cleanup_async(cleanup, value)
