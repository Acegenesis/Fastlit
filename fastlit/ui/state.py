"""Session state access: st.session_state and st.query_params."""

from __future__ import annotations

from fastlit.runtime.context import get_current_session
from fastlit.runtime.session import SessionState


def _get_session_state() -> SessionState:
    """Return the session_state for the active session."""
    return get_current_session().session_state


class _QueryParamsProxy:
    """Proxy that forwards attribute and item access to the active session's query_params dict.

    Usage:
        st.query_params["page"] = "home"
        page = st.query_params.get("page", "default")
        st.query_params.clear()
    """

    def _get_params(self) -> dict:
        return get_current_session().query_params

    def __getitem__(self, key: str) -> str:
        return self._get_params()[key]

    def __setitem__(self, key: str, value) -> None:
        self._get_params()[key] = str(value)

    def __delitem__(self, key: str) -> None:
        del self._get_params()[key]

    def __contains__(self, key) -> bool:
        return key in self._get_params()

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._get_params().get(name)

    def get(self, key: str, default=None):
        return self._get_params().get(key, default)

    def get_all(self, key: str) -> list[str]:
        """Get all values for a key (for repeated params)."""
        val = self._get_params().get(key)
        if val is None:
            return []
        if isinstance(val, list):
            return val
        return [val]

    def to_dict(self) -> dict:
        return dict(self._get_params())

    def clear(self) -> None:
        self._get_params().clear()

    def keys(self):
        return self._get_params().keys()

    def values(self):
        return self._get_params().values()

    def items(self):
        return self._get_params().items()

    def __iter__(self):
        return iter(self._get_params())

    def __len__(self):
        return len(self._get_params())

    def __bool__(self):
        return bool(self._get_params())

    def __repr__(self):
        try:
            return repr(self._get_params())
        except RuntimeError:
            return "QueryParams(<no active session>)"
