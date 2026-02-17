"""Caching decorators for Fastlit: cache_data and cache_resource."""

from __future__ import annotations

import copy
import functools
import hashlib
import inspect
import time
import threading
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_lock = threading.Lock()

# Global stores shared across all sessions
_data_cache: dict[str, tuple[Any, float | None]] = {}  # key -> (value, expire_at)
_resource_cache: dict[str, Any] = {}  # key -> value


def _make_cache_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """Build a deterministic cache key from function source + arguments."""
    try:
        source = inspect.getsource(func)
    except (OSError, TypeError):
        source = func.__qualname__

    parts = [source, repr(args), repr(sorted(kwargs.items()))]
    raw = "\n".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def cache_data(
    func: F | None = None,
    *,
    ttl: float | None = None,
) -> Any:
    """Cache function results with optional TTL.

    Supports both ``@cache_data`` and ``@cache_data(ttl=60)`` syntax.
    Returns a deep copy of cached values to prevent mutation.
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _make_cache_key(fn, args, kwargs)
            now = time.monotonic()

            with _lock:
                cached = _data_cache.get(key)
                if cached is not None:
                    value, expire_at = cached
                    if expire_at is None or now < expire_at:
                        return copy.deepcopy(value)
                    # Expired — remove
                    del _data_cache[key]

            # Compute outside the lock
            result = fn(*args, **kwargs)

            expire_at = (now + ttl) if ttl is not None else None
            with _lock:
                _data_cache[key] = (result, expire_at)

            return copy.deepcopy(result)

        wrapper.clear = lambda: _data_cache.clear()  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    if func is not None:
        # Called as @cache_data (no parentheses)
        return decorator(func)
    # Called as @cache_data(ttl=60)
    return decorator


def cache_resource(
    func: F | None = None,
) -> Any:
    """Cache a resource (DB connection, pool, etc.) — singleton, no copy.

    Supports both ``@cache_resource`` and ``@cache_resource()`` syntax.
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _make_cache_key(fn, args, kwargs)

            with _lock:
                if key in _resource_cache:
                    return _resource_cache[key]

            result = fn(*args, **kwargs)

            with _lock:
                _resource_cache[key] = result

            return result

        wrapper.clear = lambda: _resource_cache.clear()  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator
