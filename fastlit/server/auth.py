"""OIDC authentication for Fastlit — Authorization Code + PKCE flow.

Compatible with any OpenID Connect provider (Azure AD, Google, Okta, Keycloak…)
via auto-discovery at ``{issuer_url}/.well-known/openid-configuration``.

Configuration in ``secrets.toml``::

    [auth]
    provider = "oidc"
    issuer_url = "https://accounts.google.com"
    client_id = "your-client-id"
    client_secret = "your-client-secret"
    redirect_uri = "http://localhost:8501/auth/callback"
    cookie_secret = "change-me-32-chars-minimum"
    # Optional
    scopes = ["openid", "profile", "email"]
    cookie_name = "fl_session"
    cookie_max_age = 86400
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit

from collections import deque

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

try:
    import jwt
    from jwt import InvalidTokenError, PyJWK
except ImportError:  # pragma: no cover
    jwt = None
    InvalidTokenError = Exception
    PyJWK = None

logger = logging.getLogger("fastlit.auth")


# ---------------------------------------------------------------------------
# OIDC Client
# ---------------------------------------------------------------------------

class OIDCClient:
    """Minimal async OIDC client (Authorization Code + PKCE, no authlib dep)."""

    def __init__(self, cfg: dict) -> None:
        self.issuer_url = cfg["issuer_url"].rstrip("/")
        self.client_id = cfg["client_id"]
        self.client_secret = cfg.get("client_secret", "")
        self.redirect_uri = cfg["redirect_uri"]
        self.scopes: list[str] = cfg.get("scopes", ["openid", "profile", "email"])
        self._meta: dict | None = None
        self._jwks: dict | None = None
        self._jwks_loaded_at = 0.0

    async def _metadata(self) -> dict:
        """Fetch and cache OIDC discovery document."""
        if self._meta is None:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.issuer_url}/.well-known/openid-configuration",
                    timeout=10.0,
                )
                r.raise_for_status()
                self._meta = r.json()
        return self._meta

    async def _jwks_document(self) -> dict:
        """Fetch and cache the provider JWKS for one hour."""
        now = time.monotonic()
        if self._jwks is not None and (now - self._jwks_loaded_at) < 3600:
            return self._jwks
        meta = await self._metadata()
        async with httpx.AsyncClient() as client:
            response = await client.get(meta["jwks_uri"], timeout=10.0)
            response.raise_for_status()
            self._jwks = response.json()
            self._jwks_loaded_at = now
        return self._jwks

    async def authorization_url(self, state: str, code_verifier: str) -> str:
        """Build the IdP authorization URL with PKCE challenge."""
        meta = await self._metadata()
        digest = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return meta["authorization_endpoint"] + "?" + urlencode(params)

    async def exchange_code(self, code: str, code_verifier: str) -> dict:
        """Exchange authorization code for tokens."""
        meta = await self._metadata()
        async with httpx.AsyncClient() as client:
            r = await client.post(
                meta["token_endpoint"],
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code_verifier": code_verifier,
                },
                timeout=10.0,
            )
            r.raise_for_status()
            return r.json()

    @staticmethod
    def _decode_unverified_payload(id_token: str) -> dict:
        parts = id_token.split(".")
        if len(parts) != 3:
            return {}
        payload = parts[1]
        # Restore base64 padding
        payload += "=" * (-len(payload) % 4)
        try:
            return json.loads(base64.urlsafe_b64decode(payload))
        except Exception:
            return {}

    async def parse_id_token(self, token_response: dict) -> dict:
        """Decode and verify an ID token."""
        id_token = token_response.get("id_token", "")
        if not id_token:
            return {}

        if os.environ.get("FASTLIT_AUTH_SKIP_JWT_VERIFY", "").strip() in {"1", "true", "yes", "on"}:
            if os.environ.get("FASTLIT_DEV_MODE", "").strip() not in {"1", "true", "yes", "on"}:
                logger.error(
                    "FASTLIT_AUTH_SKIP_JWT_VERIFY is only allowed in dev mode "
                    "(FASTLIT_DEV_MODE=1). Refusing to skip JWT verification in production."
                )
                return {}
            logger.warning("Skipping JWT signature verification (dev mode only)")
            return self._decode_unverified_payload(id_token)

        if jwt is None or PyJWK is None:
            logger.warning("PyJWT is not installed; cannot verify id_token signature")
            return {}

        try:
            metadata = await self._metadata()
            jwks = await self._jwks_document()
            header = jwt.get_unverified_header(id_token)
            keys = jwks.get("keys", []) if isinstance(jwks, dict) else []
            kid = header.get("kid")
            key_data = next((key for key in keys if key.get("kid") == kid), None)
            if key_data is None and len(keys) == 1:
                key_data = keys[0]
            if key_data is None:
                logger.warning("Unable to find JWT signing key for kid=%s", kid)
                return {}
            signing_key = PyJWK.from_dict(key_data).key
            return jwt.decode(
                id_token,
                key=signing_key,
                algorithms=["RS256", "ES256"],
                audience=self.client_id,
                issuer=metadata.get("issuer", self.issuer_url),
            )
        except InvalidTokenError as exc:
            logger.warning("Invalid id_token received from provider: %s", exc)
            return {}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to verify id_token: %s", exc)
            return {}


# ---------------------------------------------------------------------------
# Cookie session helpers (HMAC-SHA256 signed opaque session identifiers)
# ---------------------------------------------------------------------------


@dataclass
class AuthSessionRecord:
    claims: dict[str, Any]
    expires_at: float
    created_at: float
    last_access: float


class InMemoryAuthSessionStore:
    """Process-local auth session store for opaque login cookies."""

    def __init__(self) -> None:
        self._sessions: dict[str, AuthSessionRecord] = {}
        self._lock = threading.Lock()

    def _prune(self, *, now: float | None = None) -> None:
        cutoff = time.time() if now is None else float(now)
        for session_id, record in list(self._sessions.items()):
            if cutoff >= record.expires_at:
                self._sessions.pop(session_id, None)

    def create(self, claims: dict[str, Any], *, ttl_seconds: int) -> str:
        now = time.time()
        session_id = uuid.uuid4().hex
        record = AuthSessionRecord(
            claims=dict(claims),
            expires_at=now + max(1, int(ttl_seconds)),
            created_at=now,
            last_access=now,
        )
        with self._lock:
            self._prune(now=now)
            self._sessions[session_id] = record
        return session_id

    def get(self, session_id: str) -> dict[str, Any] | None:
        now = time.time()
        with self._lock:
            self._prune(now=now)
            record = self._sessions.get(session_id)
            if record is None:
                return None
            record.last_access = now
            return dict(record.claims)

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


def _get_auth_session_store(app: Any) -> InMemoryAuthSessionStore:
    store = getattr(getattr(app, "state", None), "auth_session_store", None)
    if store is None:
        store = InMemoryAuthSessionStore()
        if getattr(app, "state", None) is not None:
            app.state.auth_session_store = store
    return store


def _sanitize_next_url(next_url: str | None) -> str:
    raw = (next_url or "").strip()
    if not raw:
        return "/"
    if raw.startswith("//"):
        return "/"

    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc:
        return "/"
    path = parsed.path or "/"
    if not path.startswith("/") or path.startswith("//"):
        return "/"
    return urlunsplit(("", "", path, parsed.query, parsed.fragment))


def _should_use_secure_cookies(request: Request) -> bool:
    if os.environ.get("FASTLIT_FORCE_SECURE_COOKIES", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return True
    if request.url.scheme == "https":
        return True
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    if forwarded_proto:
        return forwarded_proto.split(",", 1)[0].strip().lower() == "https"
    return False

def _sign(value: str, secret: str) -> str:
    """Return ``value.HMAC_HEX``."""
    sig = hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"{value}.{sig}"


def _verify(signed: str, secret: str) -> str | None:
    """Verify signature and return the original value, or None if invalid."""
    if "." not in signed:
        return None
    value, _, sig = signed.rpartition(".")
    expected = hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()
    if hmac.compare_digest(sig, expected):
        return value
    return None


def make_session_cookie(session_id: str, cfg: dict) -> str:
    """Encode an opaque auth session identifier as a signed cookie value."""
    return _sign(session_id, cfg["cookie_secret"])


def read_session_cookie(cookie_value: str, cfg: dict) -> str | None:
    """Decode and verify a signed opaque auth session cookie."""
    session_id = _verify(cookie_value, cfg["cookie_secret"])
    if session_id is None:
        logger.info("Rejected invalid auth session cookie")
        return None
    return session_id


def resolve_auth_claims(cookie_value: str | None, cfg: dict, app: Any) -> dict | None:
    """Resolve signed cookie -> opaque session id -> claims."""
    if not cookie_value:
        return None
    session_id = read_session_cookie(cookie_value, cfg)
    if session_id is None:
        return None
    return _get_auth_session_store(app).get(session_id)


# ---------------------------------------------------------------------------
# AuthMiddleware
# ---------------------------------------------------------------------------

class AuthMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that enforces OIDC authentication on all routes.

    Bypasses auth for:
    - ``/auth/*`` endpoints
    - ``/assets/*`` static files
    - ``/favicon.ico``
    - WebSocket upgrade requests (auth is checked inside the WS handler)
    """

    BYPASS_PATHS = frozenset({"/auth/login", "/auth/callback", "/auth/logout"})

    def __init__(self, app: Any, *, cfg: dict, oidc: OIDCClient) -> None:
        super().__init__(app)
        self.cfg = cfg
        self.oidc = oidc
        self._cookie_name: str = cfg.get("cookie_name", "fl_session")

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        path = request.url.path

        # Bypass: auth routes, static assets, websocket upgrades
        if (
            path in self.BYPASS_PATHS
            or path.startswith("/assets/")
            or path.startswith("/_components/")
            or path == "/favicon.ico"
            or request.headers.get("upgrade", "").lower() == "websocket"
        ):
            return await call_next(request)

        cookie_value = request.cookies.get(self._cookie_name)
        claims = resolve_auth_claims(cookie_value, self.cfg, request.app)

        if claims is None:
            login_url = f"/auth/login?next={request.url.path}"
            return RedirectResponse(login_url, status_code=302)

        request.state.user_claims = claims
        return await call_next(request)


# ---------------------------------------------------------------------------
# Auth rate limiter — per-IP, shared across login/callback/logout
# ---------------------------------------------------------------------------

_AUTH_RATE_LIMIT_PER_MINUTE = max(
    1, int(os.environ.get("FASTLIT_AUTH_RATE_LIMIT_PER_MINUTE", "20"))
)
_auth_rate_hits: dict[str, deque[float]] = {}
_auth_rate_lock = __import__("threading").Lock()


def _check_auth_rate_limit(request: Request) -> Response | None:
    """Return a 429 Response if the client IP exceeds the auth rate limit, else None."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()

    with _auth_rate_lock:
        hits = _auth_rate_hits.get(client_ip)
        if hits is None:
            hits = deque()
            _auth_rate_hits[client_ip] = hits

        cutoff = now - 60.0
        while hits and hits[0] < cutoff:
            hits.popleft()

        if len(hits) >= _AUTH_RATE_LIMIT_PER_MINUTE:
            retry_after = max(1, int(60.0 - (now - hits[0])))
            logger.warning("Auth rate limit exceeded for IP %s", client_ip)
            return JSONResponse(
                {"error": "Too many authentication requests. Please try again later."},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)

        # Periodic cleanup: remove IPs with no recent hits
        if len(_auth_rate_hits) > 1000:
            stale_ips = [ip for ip, h in _auth_rate_hits.items() if not h or h[-1] < cutoff]
            for ip in stale_ips:
                _auth_rate_hits.pop(ip, None)

    return None


# ---------------------------------------------------------------------------
# Auth HTTP routes
# ---------------------------------------------------------------------------

async def route_login(request: Request) -> Response:
    """Initiate OIDC flow: generate state + PKCE verifier, redirect to IdP."""
    rate_resp = _check_auth_rate_limit(request)
    if rate_resp is not None:
        return rate_resp
    oidc: OIDCClient = request.app.state.oidc_client
    cfg: dict = request.app.state.auth_cfg

    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    next_url = _sanitize_next_url(request.query_params.get("next", "/"))

    auth_url = await oidc.authorization_url(state, code_verifier)

    # Pack state + code_verifier + next URL into a short-lived signed cookie
    pending = json.dumps({"state": state, "cv": code_verifier, "next": next_url})
    encoded = base64.urlsafe_b64encode(pending.encode()).decode()
    signed_pending = _sign(encoded, cfg["cookie_secret"])

    response = RedirectResponse(auth_url, status_code=302)
    response.set_cookie(
        "fl_pending",
        signed_pending,
        httponly=True,
        samesite="lax",
        secure=_should_use_secure_cookies(request),
        max_age=300,  # 5 minutes to complete the flow
    )
    return response


async def route_callback(request: Request) -> Response:
    """Handle IdP callback: verify state, exchange code, set session cookie."""
    rate_resp = _check_auth_rate_limit(request)
    if rate_resp is not None:
        return rate_resp
    oidc: OIDCClient = request.app.state.oidc_client
    cfg: dict = request.app.state.auth_cfg

    code = request.query_params.get("code")
    returned_state = request.query_params.get("state")
    error = request.query_params.get("error")
    error_description = request.query_params.get("error_description", "")

    if error or not code:
        msg = error_description or error or "no authorization code received"
        logger.warning("Authentication callback failed: %s", msg)
        return Response(f"Authentication error: {msg}", status_code=400)

    # Verify the pending cookie (CSRF protection)
    pending_signed = request.cookies.get("fl_pending", "")
    raw = _verify(pending_signed, cfg["cookie_secret"])
    if raw is None:
        logger.warning("Authentication callback missing or invalid state cookie")
        return Response("Invalid or missing state cookie (possible CSRF).", status_code=400)

    try:
        pending = json.loads(base64.urlsafe_b64decode(raw + "==").decode())
    except Exception:
        logger.warning("Authentication callback contained malformed state cookie")
        return Response("Malformed state cookie.", status_code=400)

    if pending.get("state") != returned_state:
        logger.warning("Authentication callback state mismatch")
        return Response("State mismatch — authorization request may have been tampered with.", status_code=400)

    # Exchange authorization code for tokens
    try:
        token_resp = await oidc.exchange_code(code, pending["cv"])
    except httpx.HTTPStatusError as exc:
        logger.warning("OIDC token exchange failed: %s", exc.response.text)
        return Response(f"Token exchange failed: {exc.response.text}", status_code=502)
    except Exception as exc:  # noqa: BLE001
        logger.warning("OIDC token exchange failed: %s", exc)
        return Response("Token exchange failed.", status_code=502)

    claims = await oidc.parse_id_token(token_resp)
    if not claims:
        logger.warning("Failed to validate id_token from OIDC provider")
        return Response("Failed to decode id_token from provider.", status_code=502)

    # Create an opaque auth session and set a signed session-id cookie.
    max_age: int = cfg.get("cookie_max_age", 86400)
    store = _get_auth_session_store(request.app)
    session_id = store.create(claims, ttl_seconds=max_age)
    cookie_value = make_session_cookie(session_id, cfg)

    next_url = _sanitize_next_url(pending.get("next", "/"))
    response = RedirectResponse(next_url, status_code=302)
    response.set_cookie(
        cfg.get("cookie_name", "fl_session"),
        cookie_value,
        httponly=True,
        samesite="lax",
        secure=_should_use_secure_cookies(request),
        max_age=max_age,
    )
    response.delete_cookie("fl_pending", secure=_should_use_secure_cookies(request))
    return response


async def route_logout(request: Request) -> Response:
    """Clear session cookie and redirect to application root."""
    rate_resp = _check_auth_rate_limit(request)
    if rate_resp is not None:
        return rate_resp
    cfg: dict = request.app.state.auth_cfg
    cookie_name = cfg.get("cookie_name", "fl_session")
    cookie_value = request.cookies.get(cookie_name)
    session_id = read_session_cookie(cookie_value, cfg) if cookie_value else None
    if session_id is not None:
        _get_auth_session_store(request.app).delete(session_id)
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie(cookie_name, secure=_should_use_secure_cookies(request))
    return response
