"""Auth (Beta) page for the Fastlit demo."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Auth (Beta)",
    "icon": "🔐",
    "order": 140,
}

st.title("🔐 Auth (Beta)")
st.caption("OIDC authentication — `st.user`, `st.require_login()`, `st.logout()`")

st.warning(
    "**Beta feature** — The implementation is complete (Authorization Code + PKCE, "
    "HMAC-signed cookies) but has not been validated against a live IdP. "
    "API and behaviour may change.",
    icon="⚠️",
)

st.divider()

# -------------------------------------------------------------------------
# Overview
# -------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Overview")
    st.markdown("""
    Fastlit integrates **OpenID Connect** at the server level — compatible with any
    OIDC provider (Google, Azure AD, Okta, Keycloak, Dex…) via auto-discovery
    (`/.well-known/openid-configuration`).

    Auth is **opt-in**: without an `[auth]` section in `secrets.toml`, the app
    runs normally and all auth calls are no-ops.

    **Install the extra:**
    ```bash
    pip install "fastlit[auth]"
    ```
    """)

st.divider()

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("`secrets.toml` configuration")
    with st.expander("📖 All options", expanded=True):
        st.markdown("""
        | Key | Required | Description |
        |---|---|---|
        | `provider` | yes | Always `"oidc"` |
        | `issuer_url` | yes | OIDC issuer (e.g. `https://accounts.google.com`) |
        | `client_id` | yes | OAuth2 client ID |
        | `client_secret` | yes* | OAuth2 client secret (*optional for public clients) |
        | `redirect_uri` | yes | Must match IdP registration (e.g. `http://localhost:8501/auth/callback`) |
        | `cookie_secret` | yes | HMAC signing key, min 32 chars |
        | `scopes` | no | Default: `["openid", "profile", "email"]` |
        | `cookie_name` | no | Default: `fl_session` |
        | `cookie_max_age` | no | Default: `86400` (24 h) |
        """)
    st.code("""
[auth]
provider = "oidc"
issuer_url = "https://accounts.google.com"
client_id = "your-client-id"
client_secret = "your-client-secret"
redirect_uri = "http://localhost:8501/auth/callback"
cookie_secret = "change-me-32-chars-minimum!!!!!"
scopes = ["openid", "profile", "email"]
""", language="toml")

st.divider()

# -------------------------------------------------------------------------
# st.require_login
# -------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("`st.require_login()`")
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Signature:** `st.require_login() -> None`

        Call at the top of any page that requires authentication. If the user
        has no valid session cookie, raises an internal exception that redirects
        to `/auth/login?next=<current_path>`.

        When auth is not configured (no `[auth]` in `secrets.toml`), this is a no-op.
        """)
    st.code("""
import fastlit as st

st.require_login()   # ← redirect to /auth/login if not authenticated

st.title("Protected page")
st.write(f"Welcome, {st.user.name}!")
""", language="python")

st.divider()

# -------------------------------------------------------------------------
# st.user
# -------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("`st.user`")
    with st.expander("📖 Documentation", expanded=False):
        st.markdown(r"""
        Lazy proxy that reads OIDC claims from the current session.

        | Property | OIDC claim | Type |
        |---|---|---|
        | `st.user.is_logged_in` | — | `bool` |
        | `st.user.email` | `email` | `str \\| None` |
        | `st.user.name` | `name` / `preferred_username` | `str \\| None` |
        | `st.user.sub` | `sub` | `str \\| None` |
        | `st.user.<claim>` | any | `Any` |

        All claims from the ID token are accessible as attributes.
        When auth is disabled or the user is not logged in, all properties
        return `None` / `False`.
        """)
    col_code, col_live = st.columns([1, 1])
    with col_code:
        st.code("""
import fastlit as st

# Check login status
if st.user.is_logged_in:
st.success(f"Logged in as {st.user.email}")
else:
st.info("Not authenticated (auth disabled or not logged in)")

# Access any OIDC claim
st.write("Name:", st.user.name)
st.write("Subject:", st.user.sub)
st.write("Picture:", st.user.picture)   # if provided by IdP
""", language="python")
    with col_live:
        st.markdown("**Live values** (in this session):")
        if st.user.is_logged_in:
            st.success(f"Logged in as `{st.user.email}`")
            st.json({
                "is_logged_in": st.user.is_logged_in,
                "email": st.user.email,
                "name": st.user.name,
                "sub": st.user.sub,
            })
        else:
            st.info("Not authenticated — auth is disabled in this demo (no `[auth]` in secrets.toml).")
            st.json({
                "is_logged_in": False,
                "email": None,
                "name": None,
                "sub": None,
            })

st.divider()

# -------------------------------------------------------------------------
# st.logout
# -------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("`st.logout()`")
    with st.expander("📖 Documentation", expanded=False):
        st.markdown("""
        **Signature:** `st.logout() -> None`

        Clears the session cookie and redirects to `/auth/logout` → then to `/`.
        Typically called inside a button handler.
        """)
    st.code("""
import fastlit as st

st.require_login()

if st.button("Sign out", type="secondary"):
st.logout()
""", language="python")

st.divider()

# -------------------------------------------------------------------------
# Auth flow diagram
# -------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Auth flow")
    st.markdown("""
    ```
    Browser          Fastlit server         IdP (Google/Azure/…)
        │                   │                        │
        │── GET /page ──────►│                        │
        │                   │ (no valid cookie)       │
        │◄─ 302 /auth/login─│                        │
        │                   │                        │
        │── GET /auth/login ►│                        │
        │                   │ generate state+PKCE     │
        │◄─ 302 IdP URL ───►│────── redirect ────────►│
        │                   │                        │
        │◄──────────────────────────────────────────►│
        │          user authenticates at IdP         │
        │                   │                        │
        │── GET /auth/callback?code=… ──────────────►│
        │                   │◄── token response ─────│
        │                   │  parse id_token claims  │
        │◄─ 302 /page ──────│  set fl_session cookie  │
        │    (with cookie)  │                        │
        │── GET /page ──────►│                        │
        │                   │  verify cookie HMAC     │
        │◄─ 200 (app) ──────│  attach user_claims     │
    ```
    """)

st.divider()

# -------------------------------------------------------------------------
# Providers
# -------------------------------------------------------------------------
with st.container(border=True):
    st.subheader("Provider examples")
    provider = st.selectbox(
        "Select provider",
        ["Google", "Azure AD", "Okta", "Keycloak (self-hosted)"],
        key="auth_provider_select",
    )
    configs = {
        "Google": """[auth]
provider = "oidc"
issuer_url = "https://accounts.google.com"
client_id = "XXXXXXX.apps.googleusercontent.com"
client_secret = "GOCSPX-XXXXXXXXXXXXXXX"
redirect_uri = "http://localhost:8501/auth/callback"
cookie_secret = "change-me-32-chars-minimum!!!!!"
scopes = ["openid", "profile", "email"]""",
        "Azure AD": """[auth]
provider = "oidc"
issuer_url = "https://login.microsoftonline.com/<tenant-id>/v2.0"
client_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_secret = "your-client-secret"
redirect_uri = "http://localhost:8501/auth/callback"
cookie_secret = "change-me-32-chars-minimum!!!!!"
scopes = ["openid", "profile", "email"]""",
        "Okta": """[auth]
provider = "oidc"
issuer_url = "https://your-org.okta.com"
client_id = "your-client-id"
client_secret = "your-client-secret"
redirect_uri = "http://localhost:8501/auth/callback"
cookie_secret = "change-me-32-chars-minimum!!!!!"
scopes = ["openid", "profile", "email"]""",
        "Keycloak (self-hosted)": """[auth]
provider = "oidc"
issuer_url = "http://localhost:8080/realms/myrealm"
client_id = "fastlit"
client_secret = "your-client-secret"
redirect_uri = "http://localhost:8501/auth/callback"
cookie_secret = "change-me-32-chars-minimum!!!!!"
scopes = ["openid", "profile", "email"]""",
    }
    st.code(configs[provider], language="toml")

