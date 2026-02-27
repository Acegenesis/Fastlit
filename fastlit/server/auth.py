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
import secrets
import time
from typing import Any
from urllib.parse import urlencode

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response


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

    def parse_id_token(self, token_response: dict) -> dict:
        """Decode id_token JWT payload (no signature verification — trust the TLS channel)."""
        id_token = token_response.get("id_token", "")
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


# ---------------------------------------------------------------------------
# Cookie session helpers (HMAC-SHA256 signed, base64-encoded JSON payload)
# ---------------------------------------------------------------------------

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


def make_session_cookie(claims: dict, cfg: dict) -> str:
    """Encode claims as a signed cookie value."""
    payload = json.dumps(claims, separators=(",", ":"))
    encoded = base64.urlsafe_b64encode(payload.encode()).decode()
    return _sign(encoded, cfg["cookie_secret"])


def read_session_cookie(cookie_value: str, cfg: dict) -> dict | None:
    """Decode and verify a session cookie. Returns claims or None if invalid/expired."""
    raw = _verify(cookie_value, cfg["cookie_secret"])
    if raw is None:
        return None
    try:
        payload = base64.urlsafe_b64decode(raw + "==").decode()
        claims = json.loads(payload)
        # Check our internal expiry field
        if "_exp" in claims and time.time() > claims["_exp"]:
            return None
        return claims
    except Exception:
        return None


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
        claims = read_session_cookie(cookie_value, self.cfg) if cookie_value else None

        if claims is None:
            login_url = f"/auth/login?next={request.url.path}"
            return RedirectResponse(login_url, status_code=302)

        request.state.user_claims = claims
        return await call_next(request)


# ---------------------------------------------------------------------------
# Auth HTTP routes
# ---------------------------------------------------------------------------

async def route_login(request: Request) -> Response:
    """Initiate OIDC flow: generate state + PKCE verifier, redirect to IdP."""
    oidc: OIDCClient = request.app.state.oidc_client
    cfg: dict = request.app.state.auth_cfg

    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    next_url = request.query_params.get("next", "/")

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
        max_age=300,  # 5 minutes to complete the flow
    )
    return response


async def route_callback(request: Request) -> Response:
    """Handle IdP callback: verify state, exchange code, set session cookie."""
    oidc: OIDCClient = request.app.state.oidc_client
    cfg: dict = request.app.state.auth_cfg

    code = request.query_params.get("code")
    returned_state = request.query_params.get("state")
    error = request.query_params.get("error")
    error_description = request.query_params.get("error_description", "")

    if error or not code:
        msg = error_description or error or "no authorization code received"
        return Response(f"Authentication error: {msg}", status_code=400)

    # Verify the pending cookie (CSRF protection)
    pending_signed = request.cookies.get("fl_pending", "")
    raw = _verify(pending_signed, cfg["cookie_secret"])
    if raw is None:
        return Response("Invalid or missing state cookie (possible CSRF).", status_code=400)

    try:
        pending = json.loads(base64.urlsafe_b64decode(raw + "==").decode())
    except Exception:
        return Response("Malformed state cookie.", status_code=400)

    if pending.get("state") != returned_state:
        return Response("State mismatch — authorization request may have been tampered with.", status_code=400)

    # Exchange authorization code for tokens
    try:
        token_resp = await oidc.exchange_code(code, pending["cv"])
    except httpx.HTTPStatusError as exc:
        return Response(f"Token exchange failed: {exc.response.text}", status_code=502)

    claims = oidc.parse_id_token(token_resp)
    if not claims:
        return Response("Failed to decode id_token from provider.", status_code=502)

    # Set session cookie
    max_age: int = cfg.get("cookie_max_age", 86400)
    claims["_exp"] = int(time.time()) + max_age
    cookie_value = make_session_cookie(claims, cfg)

    next_url = pending.get("next", "/")
    response = RedirectResponse(next_url, status_code=302)
    response.set_cookie(
        cfg.get("cookie_name", "fl_session"),
        cookie_value,
        httponly=True,
        samesite="lax",
        max_age=max_age,
    )
    response.delete_cookie("fl_pending")
    return response


async def route_logout(request: Request) -> Response:
    """Clear session cookie and redirect to application root."""
    cfg: dict = request.app.state.auth_cfg
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie(cfg.get("cookie_name", "fl_session"))
    return response
