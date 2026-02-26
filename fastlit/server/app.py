"""Starlette ASGI application: HTTP routes + WebSocket endpoint."""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket

from fastlit.server import metrics
from fastlit.server.dataframe_store import get_slice as get_dataframe_slice
from fastlit.server.websocket_handler import handle_websocket

# Will be set by CLI before the app starts
_script_path: str = ""
_static_dir: str = ""

# Custom component static file registry: name → abs build directory
_component_paths: dict[str, str] = {}


def register_component_path(name: str, path: str) -> None:
    """Register a component's built frontend directory for static serving."""
    _component_paths[name] = path

# Lifecycle hook registries (B3)
_startup_handlers: list = []
_shutdown_handlers: list = []
_server_started: bool = False
_registered_startup_keys: set = set()  # deduplicate by qualname across reruns


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach baseline security headers to HTTP responses."""

    def __init__(
        self,
        app,
        *,
        csp_policy: str | None = None,
        csp_report_only: bool = False,
        permissions_policy: str | None = None,
        hsts_seconds: int = 0,
    ) -> None:
        super().__init__(app)
        self._csp_policy = csp_policy
        self._csp_report_only = csp_report_only
        self._permissions_policy = permissions_policy
        self._hsts_seconds = max(0, int(hsts_seconds))

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        if self._permissions_policy:
            response.headers.setdefault("Permissions-Policy", self._permissions_policy)
        if self._hsts_seconds > 0 and request.url.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                f"max-age={self._hsts_seconds}; includeSubDomains",
            )
        # SAMEORIGIN allows our own path-based component iframes (/_components/*)
        # while still blocking cross-origin framing of the main app.
        if not path.startswith("/_components/"):
            response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        if self._csp_policy and not path.startswith("/_components/"):
            csp_header = (
                "Content-Security-Policy-Report-Only"
                if self._csp_report_only
                else "Content-Security-Policy"
            )
            response.headers.setdefault(csp_header, self._csp_policy)
        return response


class HTTPRateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory per-IP request rate limiter for HTTP routes."""

    def __init__(
        self,
        app,
        *,
        max_requests_per_minute: int,
        exempt_prefixes: tuple[str, ...] = (),
    ) -> None:
        super().__init__(app)
        self._max_requests_per_minute = max(0, int(max_requests_per_minute))
        self._exempt_prefixes = exempt_prefixes
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        if self._max_requests_per_minute <= 0:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(prefix) for prefix in self._exempt_prefixes):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        retry_after = 0

        with self._lock:
            hits = self._hits.get(client_ip)
            if hits is None:
                hits = deque()
                self._hits[client_ip] = hits

            cutoff = now - 60.0
            while hits and hits[0] < cutoff:
                hits.popleft()

            if len(hits) >= self._max_requests_per_minute:
                retry_after = max(1, int(60.0 - (now - hits[0])))
            else:
                hits.append(now)

            if not hits:
                self._hits.pop(client_ip, None)

        if retry_after > 0:
            metrics.record_http_rate_limited(1)
            return JSONResponse(
                {"error": "HTTP rate limit exceeded"},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Set cache headers for static assets and SPA shell responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.method not in {"GET", "HEAD"}:
            return response

        path = request.url.path
        content_type = response.headers.get("content-type", "").lower()

        # Vite emits fingerprinted files under /assets/*, safe for long immutable cache.
        if path.startswith("/assets/"):
            response.headers.setdefault(
                "Cache-Control",
                "public, max-age=31536000, immutable",
            )
            return response

        # Component bundles/pages are often not fingerprinted (especially in dev
        # and local demos). Force revalidation to avoid stale iframe code.
        if path.startswith("/_components/"):
            response.headers.setdefault("Cache-Control", "no-cache")
            return response

        # HTML shell should be revalidated to pick up new deployments quickly.
        if "text/html" in content_type:
            response.headers.setdefault("Cache-Control", "no-cache")

        return response


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _default_csp_policy() -> str:
    directives = [
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-ancestors 'self'",
        "img-src 'self' data: blob: https:",
        "media-src 'self' data: blob:",
        "font-src 'self' data: https:",
        # Allow remote+inline style/script for iframe embeds generated by
        # Bokeh/PyDeck (their HTML payloads include inline bootstrap code and
        # CDN-hosted assets).
        "style-src 'self' 'unsafe-inline' https:",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval' blob: https:",
        "connect-src 'self' https: ws: wss:",
        "worker-src 'self' blob:",
        "frame-src 'self' blob: https:",
        "form-action 'self'",
    ]
    return "; ".join(directives)


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


async def component_file_endpoint(request: Request) -> Response:
    """Serve static files for path-based custom components.

    Handles requests to /_components/{name}/{file_path}.
    Prevents path traversal attacks.
    """
    import mimetypes

    name: str = request.path_params.get("name", "")
    file_path: str = request.path_params.get("file_path", "index.html") or "index.html"

    base = _component_paths.get(name)
    if base is None:
        return Response(f"Component '{name}' not registered.", status_code=404)

    # Resolve and sanitize path — prevent directory traversal
    base_path = Path(base).resolve(strict=False)
    requested_path = (base_path / file_path.lstrip("/\\")).resolve(strict=False)
    try:
        requested_path.relative_to(base_path)
    except ValueError:
        return Response("Forbidden", status_code=403)

    if not requested_path.is_file():
        # SPA fallback: serve index.html for sub-paths
        index_fallback = base_path / "index.html"
        if index_fallback.is_file():
            return FileResponse(str(index_fallback), media_type="text/html")
        return Response("Not found", status_code=404)

    mime, _ = mimetypes.guess_type(str(requested_path))
    return FileResponse(str(requested_path), media_type=mime or "application/octet-stream")


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
    # Custom component static assets (path-based components)
    routes.append(Route("/_components/{name}/{file_path:path}", component_file_endpoint))
    routes.append(Route("/_components/{name}", component_file_endpoint))

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
    app.add_middleware(CacheControlMiddleware)

    http_rate_limit = max(
        0, int(os.environ.get("FASTLIT_HTTP_RATE_LIMIT_PER_MINUTE", "0"))
    )
    if http_rate_limit > 0:
        exempt_raw = os.environ.get(
            "FASTLIT_HTTP_RATE_LIMIT_EXEMPT",
            "/assets/,/_components/",
        )
        exempt_prefixes = tuple(
            p.strip() for p in exempt_raw.split(",") if p.strip()
        )
        app.add_middleware(
            HTTPRateLimitMiddleware,
            max_requests_per_minute=http_rate_limit,
            exempt_prefixes=exempt_prefixes,
        )

    enable_csp = _env_flag("FASTLIT_ENABLE_CSP", default=True)
    csp_policy = os.environ.get("FASTLIT_CSP", "").strip()
    if enable_csp and not csp_policy:
        csp_policy = _default_csp_policy()
    if not enable_csp:
        csp_policy = None

    app.add_middleware(
        SecurityHeadersMiddleware,
        csp_policy=csp_policy,
        csp_report_only=_env_flag("FASTLIT_CSP_REPORT_ONLY", default=False),
        permissions_policy=os.environ.get(
            "FASTLIT_PERMISSIONS_POLICY",
            "camera=(self), microphone=(self), geolocation=(), payment=()",
        ).strip()
        or None,
        hsts_seconds=max(0, int(os.environ.get("FASTLIT_HSTS_SECONDS", "0"))),
    )

    trusted_hosts = os.environ.get("FASTLIT_TRUSTED_HOSTS", "").strip()
    if trusted_hosts:
        allowed_hosts = [h.strip() for h in trusted_hosts.split(",") if h.strip()]
        if allowed_hosts:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    return app
