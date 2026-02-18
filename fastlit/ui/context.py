"""Runtime context info for Fastlit — st.context."""

from __future__ import annotations

from fastlit.runtime.context import get_current_session


class _ContextProxy:
    """Exposes request context info: headers, cookies, locale, etc.

    Access via ``st.context``.
    """

    def _get_session(self):
        return get_current_session()

    @property
    def headers(self) -> dict[str, str]:
        """HTTP headers from the WebSocket connection."""
        session = self._get_session()
        return dict(getattr(session, "request_headers", {}))

    @property
    def cookies(self) -> dict[str, str]:
        """Cookies from the WebSocket connection."""
        session = self._get_session()
        return dict(getattr(session, "request_cookies", {}))

    @property
    def ip_address(self) -> str | None:
        """Client IP address."""
        session = self._get_session()
        return getattr(session, "client_ip", None)

    @property
    def locale(self) -> str | None:
        """Locale from Accept-Language header."""
        headers = self.headers
        accept_lang = headers.get("accept-language", "")
        if accept_lang:
            # Return primary language tag
            return accept_lang.split(",")[0].split(";")[0].strip()
        return None

    @property
    def timezone(self) -> str | None:
        """Timezone hint (from session if set, or None)."""
        session = self._get_session()
        return getattr(session, "timezone", None)

    def __repr__(self) -> str:
        return (
            f"Context(locale={self.locale!r}, "
            f"ip={self.ip_address!r})"
        )
