# Fastlit

Fastlit is a Python-first app framework with a Streamlit-compatible API and a patch-based runtime.

It preserves the `st.*` programming model, but replaces full-page rerenders with incremental UI updates over WebSocket. This makes interactions more targeted, keeps larger screens responsive, and gives the runtime clearer production boundaries.

## Overview

- Streamlit-compatible API across text, inputs, layout, charts, data, media, chat, state, cache, auth, and components
- Incremental UI patches instead of rerendering the full page on every interaction
- Partial reruns with `@st.fragment` and progressive output with `st.write_stream`
- File-based routing, nested layouts, guards, and page navigation for larger apps
- Production controls for concurrency, rate limiting, security headers, and runtime metrics

## Quickstart

Install:

```bash
pip install fastlit
```

Create `app.py`:

```python
import fastlit as st

st.set_page_config(page_title="Fastlit", layout="wide")
st.title("Hello Fastlit")

name = st.text_input("Name")
value = st.slider("Value", 0, 100, 42)

if st.button("Run"):
    st.success(f"Hello {name or 'world'} - value={value}")
```

Run:

```bash
fastlit run app.py
```

Development mode:

```bash
fastlit run app.py --dev
```

`--dev` starts backend autoreload and the frontend dev server with HMR.

## Installation

Requirements:

- Python 3.11+

Optional extras:

```bash
pip install "fastlit[dataframe]"   # pandas + pyarrow
pip install "fastlit[sql]"         # sqlalchemy + pandas
pip install "fastlit[auth]"        # httpx
pip install "fastlit[dev]"         # watchfiles + pytest
```

With `pyarrow` installed, `st.dataframe` can use Arrow transport and server-paged row windows for larger datasets.

## Programming Model

Fastlit keeps the Streamlit authoring model, but changes how updates are executed:

1. A widget updates the local client-side store immediately.
2. The browser sends an async event to the backend.
3. Fastlit reruns the full app or only the affected fragment subtree.
4. The runtime computes a patch against the previous UI tree.
5. The client reconciles the tree while preserving local widget state.

## Capabilities

### App Structure

- Familiar `st.*` API
- Sidebar navigation with `st.sidebar.navigation()`
- File-based multi-page apps with a sibling `pages/` directory
- Nested routes, dynamic segments, catch-all routes, and page metadata
- Layout composition with `st.page_outlet()`
- Route helpers such as `st.page_path(...)` and `st.switch_page(...)`

### Runtime

- Incremental diff/patch protocol over WebSocket
- Fragment reruns with `@st.fragment`
- Progressive streaming with `st.write_stream`
- `st.session_state`, `st.query_params`, and fragment-aware reruns
- Background execution with `st.run_in_thread(...)`
- Lifecycle hooks with `st.on_startup(...)` and `st.on_shutdown(...)`

### Data and Integrations

- `st.dataframe`, `st.data_editor`, `st.table`
- Virtualized data display with Arrow transport and server-paged row windows
- Fastlit-only data extensions such as `pagination=...`, `on_query=...`, and `data_editor(return_changes=True)`
- Chart support for Plotly, Altair/Vega-Lite, Matplotlib, Bokeh, Graphviz, PyDeck, and maps
- SQL connections through `st.connection(...)`
- Caching via `@st.cache_data` and `@st.cache_resource`
- Custom components through `st.components.v1`

### Authentication

- OIDC support through `st.user`, `st.require_login()`, and `st.logout()`
- Current status: beta

## Frontend Runtime

- State management uses React Context plus a custom external store for widget values
- Per-widget subscriptions use `useSyncExternalStore`, which keeps rerenders localized
- Server patches reconcile UI structure; widget state remains client-side and syncs asynchronously back to the backend
- Heavy or optional surfaces use `React.lazy` and `Suspense`
- Vite code splitting is configured explicitly for heavier dependency groups
- Likely chunks are prefetched during browser idle time
- Expensive chart surfaces can be deferred until they are near the viewport
- Frontend Web Vitals are not instrumented yet; current built-in observability is server-side runtime metrics

## Operating Fastlit

- Session caps, concurrency limits, backlog controls, and run timeouts
- HTTP and WebSocket rate limiting
- Security headers and optional CSP middleware
- Runtime metrics at `/_fastlit/metrics`
- Payload and state guardrails through environment limits such as `FASTLIT_MAX_SESSION_STATE_BYTES`, `FASTLIT_MAX_WIDGET_STORE_BYTES`, and `FASTLIT_MAX_UPLOAD_MB`

Example production profile:

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

## Status

| Surface | Status | Notes |
|---|---|---|
| Core app model, widgets, layout, state, and routing | Primary | Main framework surface exposed across the demo app and API reference |
| Data display and editing | Primary | Includes virtualization, large-data transport paths, and interactive tables |
| Caching, connections, components, and lifecycle hooks | Available | Supported as first-class APIs |
| OIDC authentication | Beta | Implemented but still explicitly marked beta |
| Frontend Web Vitals instrumentation | Not yet implemented | Server-side runtime metrics are available today |

## Streamlit Parity And Fastlit Extensions

| Surface | Feature | Streamlit | Fastlit | Status | Notes |
|---|---|---|---|---|---|
| `st.dataframe` | Virtualized display, sort, filters, selection | Yes | Yes | Parity | Core table interactions are supported on both sides |
| `st.dataframe` | Pagination UI | No native pagination | Yes | Fastlit extension | `pagination=True|"text"|"number"|"icon"` plus `page_size` |
| `st.dataframe` | Manual server query callback | No | Yes | Fastlit extension | `on_query` lets apps fetch rows from DB/API/warehouse backends |
| `st.dataframe` | Arrow/server-backed querying | Yes | Yes | Parity | Fastlit supports Arrow transport and server-backed row fetching |
| `st.data_editor` | Inline editing | Yes | Yes | Parity | Editable tabular surface with typed column config |
| `st.data_editor` | Structured change diff | No public diff object | Yes | Fastlit extension | `return_changes=True` returns `(edited_value, DataEditorChangeSet)` |
| `st.data_editor` | Undo/redo and validation state | Limited | Yes | Fastlit extension | Local undo/redo and column-driven validation |
| `st.table` | Static table rendering | Yes | Yes | Parity | Intended for smaller, static data presentations |

## Multi-Page Apps

Fastlit supports file-based routing out of the box.

Project layout:

```text
app.py
pages/
  index.py
  charts.py
  admin/
    index.py
    users.py
```

`app.py`:

```python
import fastlit as st

st.set_page_config(page_title="My App", layout="wide")
st.sidebar.navigation()
```

This model scales from a simple `app.py` to nested route trees with layouts and guards.

## Examples

The repository includes a full showcase app:

```bash
fastlit run examples/app.py --dev
```

Relevant example areas:

- `examples/pages/text_elements.py`
- `examples/pages/input_widgets.py`
- `examples/pages/data_display.py`
- `examples/pages/streaming_fragments.py`
- `examples/pages/page_system.py`
- `examples/pages/auth_beta.py`
- `examples/pages/advanced_features.py`
- `examples/pages/custom_components.py`
- `examples/pages/state_control.py`

## API Reference

Generated API signatures live in `docs/API_REFERENCE.md`.

Regenerate them from the codebase:

```bash
python scripts/generate_api_reference.py
```

## Development

Install the package in editable mode:

```bash
pip install -e .
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Build frontend assets:

```bash
npm run build
```
