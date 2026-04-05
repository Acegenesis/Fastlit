import asyncio
import time
from types import SimpleNamespace

from fastlit.server import auth


def test_read_session_cookie_valid_and_invalid() -> None:
    cfg = {"cookie_secret": "secret"}
    cookie = auth.make_session_cookie("session-123", cfg)
    assert auth.read_session_cookie(cookie, cfg) == "session-123"
    assert auth.read_session_cookie(cookie + "tampered", cfg) is None


def test_resolve_auth_claims_uses_server_side_session_store() -> None:
    cfg = {"cookie_secret": "secret"}
    app = SimpleNamespace(state=SimpleNamespace())
    store = auth.InMemoryAuthSessionStore()
    app.state.auth_session_store = store

    session_id = store.create({"sub": "user"}, ttl_seconds=60)
    cookie = auth.make_session_cookie(session_id, cfg)

    claims = auth.resolve_auth_claims(cookie, cfg, app)

    assert claims == {"sub": "user"}


def test_sanitize_next_url_rejects_external_redirects() -> None:
    assert auth._sanitize_next_url("https://evil.example") == "/"
    assert auth._sanitize_next_url("//evil.example") == "/"
    assert auth._sanitize_next_url("dashboard") == "/"
    assert auth._sanitize_next_url("/dashboard?tab=1") == "/dashboard?tab=1"


def test_parse_id_token_unverified_fallback(monkeypatch) -> None:
    monkeypatch.setenv("FASTLIT_AUTH_SKIP_JWT_VERIFY", "1")
    monkeypatch.setenv("FASTLIT_DEV_MODE", "1")
    client = auth.OIDCClient(
        {
            "issuer_url": "https://issuer.example",
            "client_id": "client-id",
            "redirect_uri": "https://app.example/auth/callback",
        }
    )
    token = "a.eyJzdWIiOiAidXNlciJ9.c"

    claims = asyncio.run(client.parse_id_token({"id_token": token}))

    assert claims == {"sub": "user"}


def test_parse_id_token_verifies_with_jwks(monkeypatch) -> None:
    class DummyJWT:
        @staticmethod
        def get_unverified_header(token: str) -> dict[str, str]:
            assert token == "header.payload.sig"
            return {"kid": "kid-1"}

        @staticmethod
        def decode(token: str, *, key, algorithms, audience, issuer):
            assert token == "header.payload.sig"
            assert key == "signing-key"
            assert algorithms == ["RS256", "ES256"]
            assert audience == "client-id"
            assert issuer == "https://issuer.example"
            return {"sub": "verified-user"}

    class DummyJWK:
        def __init__(self, key: str) -> None:
            self.key = key

        @classmethod
        def from_dict(cls, payload: dict) -> "DummyJWK":
            assert payload["kid"] == "kid-1"
            return cls("signing-key")

    async def fake_metadata() -> dict[str, str]:
        return {
            "issuer": "https://issuer.example",
            "jwks_uri": "https://issuer.example/jwks",
        }

    async def fake_jwks() -> dict[str, list[dict[str, str]]]:
        return {"keys": [{"kid": "kid-1"}]}

    monkeypatch.delenv("FASTLIT_AUTH_SKIP_JWT_VERIFY", raising=False)
    monkeypatch.setattr(auth, "jwt", DummyJWT)
    monkeypatch.setattr(auth, "PyJWK", DummyJWK)

    client = auth.OIDCClient(
        {
            "issuer_url": "https://issuer.example",
            "client_id": "client-id",
            "redirect_uri": "https://app.example/auth/callback",
        }
    )
    monkeypatch.setattr(client, "_metadata", fake_metadata)
    monkeypatch.setattr(client, "_jwks_document", fake_jwks)

    claims = asyncio.run(client.parse_id_token({"id_token": "header.payload.sig"}))

    assert claims == {"sub": "verified-user"}
