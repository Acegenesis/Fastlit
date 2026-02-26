"""Base class for Fastlit connections."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnection(ABC):
    """Abstract base class for all Fastlit connections.

    Subclass this to create custom connections::

        class MyAPIConnection(BaseConnection):
            def _connect(self, **kwargs) -> None:
                self._raw_instance = create_api_client(
                    api_key=kwargs.get("api_key"),
                )

        conn = st.connection("myapi", type=MyAPIConnection, api_key="...")
    """

    def __init__(self, connection_name: str, **kwargs: Any) -> None:
        self._connection_name = connection_name
        self._kwargs = kwargs
        self._raw_instance: Any = None
        self._connect(**kwargs)

    @abstractmethod
    def _connect(self, **kwargs: Any) -> None:
        """Establish the connection.

        Store the live connection object in ``self._raw_instance``.
        Called once on construction and again by :meth:`reset`.
        """

    def reset(self) -> None:
        """Close the current connection and reconnect.

        Call this when the connection becomes stale (e.g. after a timeout).
        """
        self._raw_instance = None
        self._connect(**self._kwargs)

    @classmethod
    def _get_secrets(cls, connection_name: str) -> dict[str, Any]:
        """Return the ``[connections.<name>]`` block from ``secrets.toml``.

        Returns an empty dict if the block does not exist.
        """
        from fastlit.ui.secrets import _load_secrets

        secrets = _load_secrets()
        connections_block = secrets.get("connections", {})
        return dict(connections_block.get(connection_name, {}))
