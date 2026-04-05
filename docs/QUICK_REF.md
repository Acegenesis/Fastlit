# Quick Reference

## Essential Commands
```bash
# Backend
pip install -e .
pip install ".[dataframe,sql,auth,dev]"

# Frontend
cd frontend
npm install

# Run
fastlit run examples/app.py
fastlit run examples/app.py --dev

# Build
fastlit build

# Checks
fastlit doctor
pytest
ruff check .
mypy fastlit tests

# Docs
python scripts/generate_api_reference.py
```

## Important Facts
- Python 3.11+ required
- Dev mode proxies Vite through the backend URL
- Auth config lives in `secrets.toml` under `[auth]`
- Auth uses `redirect_uri`
- Auth is beta
- CLI flags use `--host` and `--port`

## First Files To Open
- `README.md`
- `examples/app.py`
- `fastlit/__init__.py`
- `fastlit/server/app.py`
- `fastlit/runtime/session.py`
- `fastlit/ui/dataframe.py`
- `fastlit/ui/fragment.py`
- `fastlit/runtime/page_discovery.py`

## Useful Example Pages
- `examples/pages/data_display.py`
- `examples/pages/streaming_fragments.py`
- `examples/pages/page_system.py`
- `examples/pages/auth_beta.py`
- `examples/pages/state_control.py`
- `examples/pages/custom_components.py`
