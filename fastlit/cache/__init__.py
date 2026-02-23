"""Caching decorators for Fastlit: cache_data and cache_resource."""

from __future__ import annotations

import copy as _copy
import functools
import hashlib
import inspect
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_lock = threading.Lock()

_DATA_CACHE_MAX = 1000

# Global stores shared across all sessions.
_data_cache: OrderedDict[str, tuple[Any, float | None]] = OrderedDict()
_resource_cache: dict[str, Any] = {}
_resource_key_locks: dict[str, threading.Lock] = {}
_MISSING = object()


def _function_cache_prefix(func: Callable) -> str:
    """Build a deterministic function fingerprint used as a key prefix."""
    try:
        source = inspect.getsource(func)
    except (OSError, TypeError):
        source = func.__qualname__
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _make_cache_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """Build a deterministic cache key from function fingerprint + arguments."""
    prefix = _function_cache_prefix(func)
    raw = "\n".join([repr(args), repr(sorted(kwargs.items()))])
    args_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"{prefix}:{args_hash}"


def _clear_prefixed_cache(store: dict | OrderedDict, prefix: str) -> None:
    target = f"{prefix}:"
    keys = [k for k in store.keys() if k.startswith(target)]
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
            now = time.monotonic()

            with _lock:
                cached = _data_cache.get(key)
                if cached is not None:
                    value, expire_at = cached
                    if expire_at is None or now < expire_at:
                        _data_cache.move_to_end(key)
                        return _copy.deepcopy(value) if copy else value
                    # Expired.
                    del _data_cache[key]

            # Compute outside lock.
            result = fn(*args, **kwargs)

            expire_at = (now + ttl) if ttl is not None else None
            with _lock:
                _data_cache[key] = (result, expire_at)
                _data_cache.move_to_end(key)
                while len(_data_cache) > max_entries:
                    _data_cache.popitem(last=False)

            return _copy.deepcopy(result) if copy else result

        def _clear_fn_cache() -> None:
            with _lock:
                _clear_prefixed_cache(_data_cache, fn_prefix)

        wrapper.clear = _clear_fn_cache  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator


def cache_resource(
    func: F | None = None,
) -> Any:
    """Cache a resource (DB connection, pool, etc.) as a singleton."""

    def decorator(fn: F) -> F:
        fn_prefix = _function_cache_prefix(fn)

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _make_cache_key(fn, args, kwargs)

            with _lock:
                cached = _resource_cache.get(key, _MISSING)
                if cached is not _MISSING:
                    return cached
                key_lock = _resource_key_locks.get(key)
                if key_lock is None:
                    key_lock = threading.Lock()
                    _resource_key_locks[key] = key_lock

            # Serialize creation per key so only one thread initializes.
            with key_lock:
                with _lock:
                    cached = _resource_cache.get(key, _MISSING)
                    if cached is not _MISSING:
                        return cached

                created = fn(*args, **kwargs)

                with _lock:
                    existing = _resource_cache.get(key, _MISSING)
                    if existing is _MISSING:
                        _resource_cache[key] = created
                        return created
                    return existing

        def _clear_fn_cache() -> None:
            with _lock:
                target = f"{fn_prefix}:"
                keys = [k for k in _resource_cache.keys() if k.startswith(target)]
                for key in keys:
                    _resource_cache.pop(key, None)
                    _resource_key_locks.pop(key, None)

        wrapper.clear = _clear_fn_cache  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator

