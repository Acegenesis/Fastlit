"""Starlette ASGI application: HTTP routes + WebSocket endpoint."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import FileResponse, HTMLResponse, JSONResponse
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket

from fastlit.server import metrics
from fastlit.server.dataframe_store import get_slice as get_dataframe_slice
from fastlit.server.websocket_handler import handle_websocket

# Will be set by CLI before the app starts
_script_path: str = ""
_static_dir: str = ""

# Lifecycle hook registries (B3)
_startup_handlers: list = []
_shutdown_handlers: list = []
_server_started: bool = False
_registered_startup_keys: set = set()  # deduplicate by qualname across reruns


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline security headers to HTTP responses."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Frame-Options", "DENY")
        return response


def register_startup(fn) -> None:
    """Register a startup handler (called by @st.on_startup).

    If the server has already started (i.e., the handler is registered during
    a session rerun rather than at import time), the handler is called
    immediately. Handlers are deduplicated by qualname to avoid multiple calls
    on successive reruns.
    """
    import logging
    fn_key = f"{getattr(fn, '__module__', '')}:{getattr(fn, '__qualname__', id(fn))}"
    if fn_key in _registered_startup_keys:
        return
    _registered_startup_keys.add(fn_key)
    _startup_handlers.append(fn)

    if _server_started:
        # Lifespan already ran — call immediately in the current sync context
        try:
            import asyncio
            if asyncio.iscoroutinefunction(fn):
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(fn())
            else:
                fn()
        except Exception as exc:
            logging.getLogger("fastlit.app").error("startup handler error: %s", exc)


def register_shutdown(fn) -> None:
    """Register a shutdown handler (called by @st.on_shutdown)."""
    _shutdown_handlers.append(fn)


def set_script_path(path: str) -> None:
    global _script_path
    _script_path = path


def set_static_dir(path: str) -> None:
    global _static_dir
    _static_dir = path


async def homepage(request):
    """Serve the frontend SPA entry point."""
    index_path = os.path.join(_static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    # Fallback: minimal HTML that loads the frontend
    return HTMLResponse(
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fastlit</title>
</head>
<body>
    <div id="root"></div>
    <script>
        document.getElementById('root').innerHTML =
            '<p style="font-family:sans-serif;padding:2rem;">Frontend not built. Run: cd frontend && npm install && npm run build</p>';
    </script>
</body>
</html>""",
        status_code=200,
    )


async def ws_endpoint(websocket: WebSocket):
    """WebSocket endpoint for client connections."""
    await handle_websocket(websocket, _script_path)


async def metrics_endpoint(request):
    """Expose in-memory runtime metrics as JSON."""
    return JSONResponse(metrics.snapshot())


async def dataframe_slice_endpoint(request):
    """Serve server-side dataframe row windows."""
    source_id = request.path_params.get("source_id", "")
    try:
        offset = int(request.query_params.get("offset", "0"))
        limit = int(request.query_params.get("limit", "200"))
    except ValueError:
        return JSONResponse({"error": "invalid offset/limit"}, status_code=400)

    data = get_dataframe_slice(source_id, offset, limit)
    if data is None:
        return JSONResponse({"error": "unknown dataframe source"}, status_code=404)
    return JSONResponse(data)


@asynccontextmanager
async def _lifespan(app: Starlette) -> AsyncIterator[None]:
    """ASGI lifespan: run startup/shutdown hooks (B3)."""
    global _server_started
    import asyncio

    for fn in _startup_handlers:
        if asyncio.iscoroutinefunction(fn):
            await fn()
        else:
            fn()

    _server_started = True
    yield
    _server_started = False
    # Clear dedup set so hooks re-register correctly after hot reload
    _registered_startup_keys.clear()

    for fn in _shutdown_handlers:
        if asyncio.iscoroutinefunction(fn):
            await fn()
        else:
            fn()


def create_app(script_path: str | None = None, static_dir: str | None = None) -> Starlette:
    """Create and configure the Starlette ASGI app.

    When called by uvicorn factory=True (hot reload), script_path is read
    from the FASTLIT_SCRIPT_PATH environment variable set by the CLI.
    """
    # Suppress noisy third-party loggers — run here so it applies to the
    # uvicorn worker process (not just the parent CLI process).
    import logging as _logging
    for _noisy in ("matplotlib", "matplotlib.font_manager", "PIL", "pydeck", "bokeh"):
        _logging.getLogger(_noisy).setLevel(_logging.WARNING)

    if script_path is None:
        script_path = os.environ.get("FASTLIT_SCRIPT_PATH", "")

    set_script_path(script_path)

    # Resolve static directory
    if static_dir is None:
        # Default: look for built frontend assets next to the server package
        static_dir = os.path.join(os.path.dirname(__file__), "static")
    set_static_dir(static_dir)

    # Build routes list
    routes = [WebSocketRoute("/ws", ws_endpoint)]

    if os.environ.get("FASTLIT_ENABLE_METRICS", "1") not in {"0", "false", "False"}:
        routes.append(Route("/_fastlit/metrics", metrics_endpoint))
    routes.append(Route("/_fastlit/dataframe/{source_id}", dataframe_slice_endpoint))

    # Mount static files if the directory exists
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.isdir(assets_dir):
        routes.append(Mount("/assets", StaticFiles(directory=assets_dir), name="static"))

    # Catch-all route for SPA — must be last, serves index.html for all paths
    # This allows client-side routing with clean URLs like /layouts, /widgets
    routes.append(Route("/{path:path}", homepage))
    routes.append(Route("/", homepage))

    app = Starlette(routes=routes, lifespan=_lifespan)
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(SecurityHeadersMiddleware)

    trusted_hosts = os.environ.get("FASTLIT_TRUSTED_HOSTS", "").strip()
    if trusted_hosts:
        allowed_hosts = [h.strip() for h in trusted_hosts.split(",") if h.strip()]
        if allowed_hosts:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    return app
