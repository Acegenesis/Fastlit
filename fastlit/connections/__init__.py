"""Fastlit connections — st.connection() factory and built-in connectors."""

from __future__ import annotations

import importlib
import threading
import time
from typing import Any

from fastlit.connections.base import BaseConnection
from fastlit.connections.sql import SQLConnection

__all__ = ["connection", "BaseConnection", "SQLConnection"]

# ---------------------------------------------------------------------------
# Global connection cache (singleton per name+type, with optional TTL)
# ---------------------------------------------------------------------------

_connection_cache: dict[str, tuple[BaseConnection, float | None]] = {}
_connection_key_locks: dict[str, threading.Lock] = {}
_lock = threading.Lock()

# Built-in type aliases
_BUILTIN_TYPES: dict[str, type[BaseConnection]] = {
    "sql": SQLConnection,
}


def _resolve_type(type_: str | type[BaseConnection]) -> type[BaseConnection]:
    """Resolve a type string or class to a BaseConnection subclass."""
    if isinstance(type_, type):
        if not issubclass(type_, BaseConnection):
            raise TypeError(
                f"{type_.__qualname__} must be a subclass of BaseConnection"
            )
        return type_

    builtin = _BUILTIN_TYPES.get(type_.lower())
    if builtin is not None:
        return builtin

    # Dotted module path: "mypackage.MyConnection"
    module_path, sep, class_name = type_.rpartition(".")
    if not sep:
        raise ValueError(
            f"Unknown connection type: {type_!r}. "
            f"Built-in types: {sorted(_BUILTIN_TYPES)}. "
            f"For custom types use a dotted path like 'mypackage.MyConnection'."
        )
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        raise ImportError(f"Cannot import connection module {module_path!r}") from exc

    cls = getattr(mod, class_name, None)
    if cls is None:
        raise AttributeError(f"{module_path!r} has no attribute {class_name!r}")
    if not (isinstance(cls, type) and issubclass(cls, BaseConnection)):
        raise TypeError(f"{type_!r} must be a subclass of BaseConnection")
    return cls


def connection(
    name: str,
    type: str | type[BaseConnection] | None = None,  # noqa: A002
    ttl: float | int | None = None,
    **kwargs: Any,
) -> BaseConnection:
    """Return a cached connection by name.

    Reads configuration from ``[connections.<name>]`` in ``secrets.toml``.
    The ``type`` argument overrides the ``type`` key in secrets.

    Args:
        name: Connection name matching a ``[connections.<name>]`` secrets block.
        type: Connection type — ``"sql"`` or a :class:`BaseConnection` subclass
            or a dotted import path like ``"mypackage.MyConn"``.
            If ``None``, the ``type`` key from secrets is used.
        ttl: Seconds before the cached connection is discarded and recreated.
            ``None`` (default) means the connection lives for the entire session.
        **kwargs: Extra keyword arguments forwarded to :meth:`BaseConnection._connect`.
            Override secrets values.

    Returns:
        A :class:`BaseConnection` instance (cached singleton by default).

    Examples::

        # secrets.toml:
        # [connections.mydb]
        # type = "sql"
        # url = "sqlite:///app.db"

        conn = st.connection("mydb")
        df = conn.query("SELECT * FROM users")
        st.dataframe(df)

        # Custom connection class:
        class MyAPI(st.connections.BaseConnection):
            def _connect(self, *, api_key: str, **kw):
                self._raw_instance = MyClient(api_key=api_key)

        conn = st.connection("myapi", type=MyAPI, api_key="secret")
    """
    # Resolve type
    resolved_type = type
    if resolved_type is None:
        from fastlit.ui.secrets import _load_secrets

        secrets = _load_secrets()
        block = (secrets.get("connections") or {}).get(name) or {}
        resolved_type = block.get("type")
    if resolved_type is None:
        raise ValueError(
            f"st.connection({name!r}): 'type' not specified and not found in "
            f"secrets.toml under [connections.{name}]."
        )

    conn_class = _resolve_type(resolved_type)
    cache_key = f"{name}:{conn_class.__qualname__}"
    now = time.monotonic()

    # Fast path — check cache without acquiring key lock
    with _lock:
        hit = _connection_cache.get(cache_key)
        if hit is not None:
            conn_obj, expire_at = hit
            if expire_at is None or now < expire_at:
                return conn_obj
            # Expired — remove and fall through to recreate
            del _connection_cache[cache_key]

        # Ensure a per-key lock exists
        if cache_key not in _connection_key_locks:
            _connection_key_locks[cache_key] = threading.Lock()
        key_lock = _connection_key_locks[cache_key]

    # Slow path — serialize creation per connection name
    with key_lock:
        # Double-check after acquiring key lock
        with _lock:
            hit = _connection_cache.get(cache_key)
        if hit is not None:
            conn_obj, expire_at = hit
            if expire_at is None or now < expire_at:
                return conn_obj

        conn_obj = conn_class(name, **kwargs)
        expire_at = (time.monotonic() + float(ttl)) if ttl is not None else None
        with _lock:
            _connection_cache[cache_key] = (conn_obj, expire_at)

    return conn_obj


def _clear_all() -> None:
    """Clear the entire connection cache (for testing / hot reload)."""
    with _lock:
        _connection_cache.clear()
        _connection_key_locks.clear()
