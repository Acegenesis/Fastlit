# Documentation Index

## Start Here
- `README.md` - current product overview, feature status, install, and operations
- `docs/API_REFERENCE.md` - generated API signatures
- `docs/QUICK_REF.md` - commands and high-signal entry points

## Product Surfaces
- Runtime overview: `fastlit/runtime/session.py`, `fastlit/runtime/script_runner.py`, `fastlit/runtime/diff.py`
- Routing and page discovery: `fastlit/runtime/page_discovery.py`, `fastlit/ui/layout.py`
- Server and middleware: `fastlit/server/app.py`
- Authentication: `fastlit/server/auth.py`
- Dataframe and editor backend: `fastlit/ui/dataframe.py`
- Components API: `fastlit/components/v1.py`

## Frontend
- App shell: `frontend/src/App.tsx`
- Runtime patches and websocket: `frontend/src/runtime/`
- Node registry: `frontend/src/registry/`
- Data surfaces: `frontend/src/components/data/`
- Layout components: `frontend/src/components/layout/`

## Examples
- Demo entrypoint: `examples/app.py`
- Text/widgets/layout: `examples/pages/text_elements.py`, `examples/pages/input_widgets.py`, `examples/pages/layout.py`
- Data: `examples/pages/data_display.py`
- Streaming and fragments: `examples/pages/streaming_fragments.py`
- Deferred loading: `examples/pages/progressive_loading.py`
- Routing system: `examples/pages/page_system.py`
- Auth beta: `examples/pages/auth_beta.py`
- Components: `examples/pages/custom_components.py`
- State, query params, connections: `examples/pages/state_control.py`

## Maintenance
- Regenerate API docs: `python scripts/generate_api_reference.py`
- Frontend build: `fastlit build`
- Local checks: `fastlit doctor`, `pytest`, `ruff check .`, `mypy fastlit tests`

## Notes
- Treat `README.md` as the canonical human-facing summary.
- Treat `claude.md` as the compact assistant context.
- Do not document speculative features here as if they already ship.
