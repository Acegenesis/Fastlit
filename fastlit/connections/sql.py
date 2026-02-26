"""SQLConnection — relational database via SQLAlchemy."""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator

from fastlit.connections.base import BaseConnection

if TYPE_CHECKING:
    import pandas as pd


def _build_url(cfg: dict[str, Any]) -> str:
    """Construct a SQLAlchemy URL from individual secrets keys."""
    dialect = cfg.get("dialect", "postgresql")
    driver = cfg.get("driver", "")
    username = cfg.get("username") or cfg.get("user", "")
    password = cfg.get("password", "")
    host = cfg.get("host", "localhost")
    port = cfg.get("port", "")
    database = cfg.get("database") or cfg.get("db", "")

    dialect_str = f"{dialect}+{driver}" if driver else dialect
    auth = f"{username}:{password}@" if username else ""
    port_str = f":{port}" if port else ""
    return f"{dialect_str}://{auth}{host}{port_str}/{database}"


class SQLConnection(BaseConnection):
    """SQL database connection powered by SQLAlchemy.

    Configure via ``secrets.toml``::

        [connections.mydb]
        type = "sql"
        url = "postgresql://user:pass@localhost/mydb"

    Or using individual fields::

        [connections.mydb]
        type = "sql"
        dialect = "postgresql"
        host = "localhost"
        port = 5432
        database = "mydb"
        username = "user"
        password = "pass"

    Usage::

        conn = st.connection("mydb")
        df = conn.query("SELECT * FROM users WHERE active = :active",
                        params={"active": True}, ttl=60)
        st.dataframe(df)

        with conn.session() as s:
            s.execute(sa.text("INSERT INTO logs (msg) VALUES (:m)"), {"m": "hi"})
    """

    def _connect(self, **kwargs: Any) -> None:
        try:
            import sqlalchemy as sa  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "SQLConnection requires SQLAlchemy. "
                "Install it with:  pip install sqlalchemy"
            ) from exc

        import sqlalchemy as sa

        secrets = self._get_secrets(self._connection_name)
        # kwargs passed to st.connection() override secrets
        merged = {**secrets, **kwargs}
        # Remove meta-keys not meant for SQLAlchemy
        for key in ("type", "dialect", "driver", "host", "port",
                    "database", "db", "username", "user", "password"):
            merged.pop(key, None)

        secrets_again = self._get_secrets(self._connection_name)
        url = secrets_again.get("url") or kwargs.get("url") or _build_url(
            {**self._get_secrets(self._connection_name), **kwargs}
        )

        # Extra SQLAlchemy engine kwargs (pool_size, pool_recycle, echo, …)
        engine_kwargs = {k: v for k, v in merged.items() if k != "url"}
        self._engine = sa.create_engine(url, **engine_kwargs)
        self._raw_instance = self._engine

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query(
        self,
        sql: str,
        *,
        ttl: float | int | None = 3600,
        params: dict[str, Any] | None = None,
    ) -> "pd.DataFrame":
        """Execute a SQL query and return a :class:`pandas.DataFrame`.

        Results are cached for *ttl* seconds (default 3600 s = 1 hour).
        Pass ``ttl=0`` or ``ttl=None`` to disable caching.

        Args:
            sql: SQL query string. Use ``:name`` placeholders for params.
            ttl: Cache time-to-live in seconds. ``None`` means no cache.
            params: Named parameters dict for the query.

        Returns:
            A pandas DataFrame with the query results.
        """
        try:
            import pandas as pd
        except ImportError as exc:
            raise ImportError(
                "SQLConnection.query() requires pandas. "
                "Install it with:  pip install pandas"
            ) from exc

        import sqlalchemy as sa

        if ttl:
            # Build a stable cache key from (connection_name, sql, params)
            raw = f"{self._connection_name}\n{sql}\n{repr(sorted((params or {}).items()))}"
            cache_key = hashlib.sha256(raw.encode()).hexdigest()

            from fastlit.cache import cache_data

            @cache_data(ttl=ttl)
            def _cached_query(key: str) -> "pd.DataFrame":  # noqa: ARG001
                with self._engine.connect() as conn:
                    return pd.read_sql_query(sa.text(sql), conn, params=params)

            return _cached_query(cache_key)

        with self._engine.connect() as conn:
            return pd.read_sql_query(sa.text(sql), conn, params=params)

    @contextmanager
    def session(self) -> Generator[Any, None, None]:
        """Context manager yielding a SQLAlchemy :class:`~sqlalchemy.orm.Session`.

        Commits on clean exit; rolls back on exception::

            with conn.session() as s:
                s.execute(sa.text("DELETE FROM tmp"))
        """
        import sqlalchemy.orm as orm

        SessionFactory = orm.sessionmaker(bind=self._engine)
        s = SessionFactory()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    @property
    def engine(self) -> Any:
        """The underlying ``sqlalchemy.Engine`` instance."""
        return self._engine
