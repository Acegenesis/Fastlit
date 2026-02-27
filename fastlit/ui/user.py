"""st.user — OIDC claims proxy for the current session."""

from __future__ import annotations

from typing import Any


class _UserProxy:
    """Lazy proxy that reads OIDC claims from the active Fastlit session.

    Usage::

        import fastlit as st

        st.require_login()
        st.write(st.user.name, st.user.email)

    All standard OIDC claims are available as attributes (``sub``, ``email``,
    ``name``, ``preferred_username``, ``picture``, …).  Custom claims returned
    by the IdP are also accessible.

    ``st.user.is_logged_in`` returns ``False`` when auth is disabled or the
    user has not authenticated yet.
    """

    def _claims(self) -> dict:
        try:
            from fastlit.runtime.context import get_current_session
            session = get_current_session()
            return getattr(session, "user_claims", None) or {}
        except Exception:
            return {}

    @property
    def is_logged_in(self) -> bool:
        """True if the current session has valid OIDC claims."""
        return bool(self._claims())

    @property
    def email(self) -> str | None:
        return self._claims().get("email")

    @property
    def name(self) -> str | None:
        c = self._claims()
        return c.get("name") or c.get("preferred_username")

    @property
    def sub(self) -> str | None:
        """OIDC subject identifier (unique user ID from the IdP)."""
        return self._claims().get("sub")

    def __getattr__(self, item: str) -> Any:
        # Fallback: look up arbitrary claim by name
        if item.startswith("_"):
            raise AttributeError(item)
        return self._claims().get(item)

    def __repr__(self) -> str:
        claims = self._claims()
        if not claims:
            return "_UserProxy(not authenticated)"
        email = claims.get("email", claims.get("sub", "?"))
        return f"_UserProxy(email={email!r})"


# Module-level singleton — accessed as ``st.user``
user = _UserProxy()
