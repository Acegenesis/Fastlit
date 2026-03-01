# Fastlit

Streamlit-compatible, Python-first UI framework with a faster runtime model.

Fastlit keeps the familiar `st.*` API, but uses an incremental patch protocol over WebSocket instead of full-page rerenders for every interaction.

## What Fastlit provides

- Streamlit-style API across text, widgets, layout, charts, data, media, chat, state, status, cache, auth, and custom components.
- Incremental UI updates (diff/patch) with bounded event queues and coalescing.
- Fragment reruns with `@st.fragment` and live output streaming with `st.write_stream`.
- Virtualized tables (`st.dataframe`) with optional server-side row windows for large datasets.
- Caching primitives:
  - `@st.cache_data` (TTL + max entries + optional copy behavior)
  - `@st.cache_resource` (shared singleton resources)
- Custom components compatibility layer: `st.components.v1.html`, `iframe`, `declare_component`.
- OIDC auth support (`st.user`, `st.require_login`, `st.logout`) via `secrets.toml`.
- Connection system (`st.connection`, `st.connections`) with built-in SQL connector and custom connector support.
- Runtime and security controls for production:
  - session limits, run timeout, concurrency caps
  - HTTP/WS rate limiting controls
  - CSP/security headers middleware
  - cache-control policies for static assets and components
- Built-in metrics endpoint: `/_fastlit/metrics`.

## Installation

Requirements:
- Python 3.11+

Install package:

```bash
pip install fastlit
```

Optional extras:

```bash
pip install "fastlit[dataframe]"   # pandas + pyarrow
pip install "fastlit[sql]"         # sqlalchemy + pandas
pip install "fastlit[auth]"        # httpx (OIDC auth — beta)
pip install "fastlit[dev]"         # watchfiles
```

## Quick start

Create `app.py`:

```python
import fastlit as st

st.set_page_config(page_title="Fastlit App", layout="wide")
st.title("Hello Fastlit")

name = st.text_input("Your name")
n = st.slider("Pick a number", 0, 100, 42)

if st.button("Run"):
    st.success(f"Hello {name or 'world'} - value={n}")
```

Run:

```bash
fastlit run app.py
```

Development mode (fullstack dev: backend reload + frontend HMR):

```bash
fastlit run app.py --dev
```

With explicit frontend dev server options:

```bash
fastlit run app.py --dev --frontend-port 5173 --frontend-host 127.0.0.1
```

## File-based pages

Fastlit supports file-based multi-page apps out of the box.

Project layout:

```text
app.py
pages/
  index.py
  charts.py
  status_feedback.py
```

`app.py`:

```python
import fastlit as st

st.set_page_config(page_title="My App", layout="wide")
current_page = st.sidebar.navigation()
current_page.run()
```

`pages/charts.py`:

```python
import fastlit as st

PAGE_CONFIG = {
    "title": "Charts",
    "icon": "📈",
    "order": 20,
}

st.title("Charts")
st.write("Auto-discovered from pages/charts.py")
```

Supported page metadata:
- `PAGE_CONFIG = {"title": "...", "icon": "...", "order": 10, "default": True, "hidden": False, "url_path": "..."}`
- Or individual constants: `PAGE_TITLE`, `PAGE_ICON`, `PAGE_ORDER`, `PAGE_DEFAULT`, `PAGE_HIDDEN`, `PAGE_URL_PATH`

By default, the route slug is the filename. For example, `pages/status_feedback.py` maps to `/status_feedback`.
`current_page.run()` renders the selected page inside your current script, so `app.py` can act as a global layout.

In `--dev` mode, Fastlit now:
- starts the Python backend with autoreload
- starts the Vite frontend dev server with HMR
- redirects SPA page requests to the Vite server

Notes:
- Python changes trigger backend reload
- `frontend/src/*`, `frontend/index.html`, and CSS changes use Vite HMR/reload
- `st.components.v1.declare_component(url=...)` keeps its separate dev-server workflow

## Demo app

The full showcase is in:

- `examples/app.py`

Run it:

```bash
fastlit run examples/app.py --dev
```

## API reference

Auto-generated signatures are in:

- `docs/API_REFERENCE.md`

Regenerate from real Python signatures:

```bash
python scripts/generate_api_reference.py
```

## Core API categories

- Text: `st.title`, `st.header`, `st.markdown`, `st.write`, `st.help`, `st.write_stream`, `st.badge`, etc.
- Inputs: buttons, sliders, text inputs, selectors, uploads, camera/audio, feedback, segmented controls.
- Layout: `st.sidebar`, `st.columns`, `st.tabs`, `st.form`, `st.dialog`, `st.popover`, `st.navigation`, `st.Page`, `st.switch_page`.
- Data: `st.dataframe`, `st.data_editor`, `st.table`, column config helpers.
- Charts: native and embedded chart APIs (`plotly`, `altair/vega-lite`, `pyplot`, `bokeh`, `graphviz`, `pydeck`, map).
- Media: `st.image`, `st.audio`, `st.video`, `st.logo`, `st.pdf`.
- Chat: `st.chat_message`, `st.chat_input`.
- State/control: `st.session_state`, `st.query_params`, `st.context`, `st.rerun`, `st.stop`.
- Runtime/lifecycle: `st.run_in_thread`, `st.run_with_session_context`, `st.on_startup`, `st.on_shutdown`.
- Cache: `st.cache_data`, `st.cache_resource`.
- Auth: `st.user`, `st.require_login`, `st.logout`.
- Connections: `st.connection`, `st.connections`.
- Components: `st.components.v1`.

## Auth (OIDC) — Beta

> **Status: Beta — not yet production-tested.**
> The implementation is complete on paper (Authorization Code + PKCE, HMAC-signed cookies, `AuthMiddleware`) but has not been validated against a live IdP. Use with caution and report issues.

Requires the `auth` extra:

```bash
pip install "fastlit[auth]"
```

`secrets.toml`:

```toml
[auth]
provider = "oidc"
issuer_url = "https://accounts.google.com"   # or Azure AD, Okta, Keycloak…
client_id = "your-client-id"
client_secret = "your-client-secret"
redirect_uri = "http://localhost:8501/auth/callback"
cookie_secret = "change-me-32-chars-minimum"
# Optional
scopes = ["openid", "profile", "email"]
cookie_name = "fl_session"    # default
cookie_max_age = 86400        # seconds (default: 24h)
```

In app:

```python
import fastlit as st

st.require_login()   # redirects to /auth/login if not authenticated
st.write("Hello", st.user.name, st.user.email)

if st.button("Sign out"):
    st.logout()
```

Available claims on `st.user`:

| Property | OIDC claim | Description |
|---|---|---|
| `st.user.is_logged_in` | — | `True` if auth cookie is valid |
| `st.user.email` | `email` | User email |
| `st.user.name` | `name` / `preferred_username` | Display name |
| `st.user.sub` | `sub` | Unique subject identifier |
| `st.user.<claim>` | any | Arbitrary claim from the ID token |

Auth flow:
1. Unauthenticated request → redirect to `/auth/login?next=<url>`
2. `/auth/login` → redirect to IdP with PKCE challenge
3. IdP callback → `/auth/callback` → HMAC-signed session cookie → redirect to original URL
4. `/auth/logout` → cookie cleared → redirect to `/`

Without `[auth]` in `secrets.toml`, auth is fully disabled and the app works normally.

## SQL connection example

`secrets.toml`:

```toml
[connections.mydb]
type = "sql"
url = "sqlite:///app.db"
```

In app:

```python
import fastlit as st

conn = st.connection("mydb")
df = conn.query("SELECT 1 AS ok", ttl=30)
st.dataframe(df)
```

## Custom component (`st.components.v1`) example

```python
import fastlit as st

counter = st.components.v1.declare_component(
    "my_counter",
    path="./frontend_build",
)

value = counter(step=1, key="counter", default=0)
st.write("Value:", value)
```

Protocol messages for interactive components:
- parent to child: `streamlit:render`
- child to parent: `streamlit:componentReady`
- child to parent: `streamlit:setComponentValue`
- child to parent: `streamlit:setFrameHeight`

## Production run profile

```bash
fastlit run app.py \
  --host 0.0.0.0 \
  --port 8501 \
  --workers 4 \
  --limit-concurrency 200 \
  --backlog 2048 \
  --max-sessions 300 \
  --max-concurrent-runs 8 \
  --run-timeout-seconds 45
```

Metrics endpoint:

- `GET /_fastlit/metrics`

## Contributor notes

Install editable package:

```bash
pip install -e .
```

Build frontend assets:

```bash
cd frontend
npm install
npm run build
```

Then run demo:

```bash
fastlit run examples/app.py --dev
```

For fullstack dev mode, make sure frontend dependencies are installed first:

```bash
cd frontend
npm install
```
