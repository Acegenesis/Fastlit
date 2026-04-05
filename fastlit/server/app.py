"""Starlette ASGI application: HTTP routes + WebSocket endpoint."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
import uuid
from collections import deque
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import AsyncIterator
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket
from websockets import connect as ws_connect
from websockets.exceptions import ConnectionClosed

from fastlit.runtime.dataframe_arrow import (
    ARROW_STREAM_MEDIA_TYPE,
    serialize_arrow_frame,
)
from fastlit.runtime.script_runner import check_script_loadable
from fastlit.cache import clear_resource_caches
from fastlit.server import metrics
from fastlit.server.dataframe_store import (
    DataframeFilter,
    DataframeQuery,
    DataframeSort,
    extract_session_id,
    get_slice as get_dataframe_slice,
)
from fastlit.server.logging_config import bind_log_context, configure_logging
from fastlit.server.session_process import SessionProcessCrashedError, SessionProcessExecutionError
from fastlit.server.session_store import InMemorySessionStore
from fastlit.server.websocket_handler import handle_websocket

# Will be set by CLI before the app starts
_script_path: str = ""
_static_dir: str = ""

# Custom component static file registry: name → abs build directory
_component_paths: dict[str, str] = {}
logger = logging.getLogger("fastlit.app")


def register_component_path(name: str, path: str) -> None:
    """Register a component's built frontend directory for static serving."""
    _component_paths[name] = path

# Lifecycle hook registries (B3)
_startup_handlers: list = []
_shutdown_handlers: list = []
_server_started: bool = False
_registered_startup_keys: set = set()  # deduplicate by qualname across reruns
_VALID_FILTER_OPS = frozenset(
    {
        "after",
        "before",
        "between",
        "contains",
        "contains_all",
        "contains_any",
        "equals",
        "gt",
        "gte",
        "is_empty",
        "is_false",
        "is_true",
        "lt",
        "lte",
        "not_contains",
        "not_empty",
        "not_equals",
        "on_or_after",
        "on_or_before",
    }
)
_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "content-encoding",
}


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind a request id to logs and response headers."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", "").strip() or uuid.uuid4().hex
        request.state.request_id = request_id
        with bind_log_context(request_id=request_id):
            response = await call_next(request)
        response.headers.setdefault("X-Request-ID", request_id)
        return response


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
        is_dev_vite_proxy = (
            response.headers.get("X-Fastlit-Dev-Proxy", "").strip().lower() == "vite"
        )
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
        if self._csp_policy and not path.startswith("/_components/") and not is_dev_vite_proxy:
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


class _StaticCacheMiddleware(BaseHTTPMiddleware):
    """Unified cache-control middleware for all response types.

    - ``/assets/*``      → ``public, max-age=31536000, immutable``
      Vite emits content-hashed filenames here, safe for a permanent cache.
    - ``/_components/*`` → ``no-cache``
      Component bundles are often not fingerprinted; force revalidation to
      avoid serving stale iframe code.
    - ``/`` and ``/index.html`` (or any ``text/html`` response) → ``no-cache``
      The SPA shell must be revalidated on each deployment.
    Only applies to ``GET`` / ``HEAD`` requests.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.method not in {"GET", "HEAD"}:
            return response

        path = request.url.path
        content_type = response.headers.get("content-type", "").lower()

        # Vite fingerprinted assets — immutable long-lived cache.
        if path.startswith("/assets/") and response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return response

        # Component bundles/pages — force revalidation.
        if path.startswith("/_components/"):
            response.headers.setdefault("Cache-Control", "no-cache")
            return response

        # SPA shell and any HTML response — always revalidate.
        if path in ("/", "/index.html") or "text/html" in content_type:
            response.headers.setdefault("Cache-Control", "no-cache")

        return response


def _make_cache_control_middleware():
    """Return the static cache middleware class (used for testing)."""
    return _StaticCacheMiddleware


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _default_csp_policy() -> str:
    strict_csp = _env_flag("FASTLIT_CSP_STRICT", default=True)
    script_tokens = [
        "'self'",
        "'wasm-unsafe-eval'",
        "blob:",
    ]
    if not strict_csp:
        script_tokens.extend(["'unsafe-eval'", "https:"])
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
        f"script-src {' '.join(script_tokens)}",
        "connect-src 'self' https: ws: wss:",
        "worker-src 'self' blob:",
        "frame-src 'self' blob: https:",
        "form-action 'self'",
    ]
    return "; ".join(directives)


def _should_use_secure_cookies(request: Request) -> bool:
    if _env_flag("FASTLIT_FORCE_SECURE_COOKIES", default=False):
        return True
    if request.url.scheme == "https":
        return True
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    if forwarded_proto:
        return forwarded_proto.split(",", 1)[0].strip().lower() == "https"
    return False


def _clean_request_url(request: Request, key_to_remove: str) -> str:
    query_items = [
        (key, value)
        for key, value in request.query_params.multi_items()
        if key != key_to_remove
    ]
    path = request.url.path or "/"
    if not query_items:
        return path
    return f"{path}?{urlencode(query_items, doseq=True)}"


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


def _dev_server_url() -> str:
    return os.environ.get("FASTLIT_DEV_SERVER_URL", "").strip().rstrip("/")


def _copy_proxy_request_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    for key, value in request.headers.items():
        lower = key.lower()
        if lower in _HOP_BY_HOP_HEADERS or lower == "host":
            continue
        if lower == "accept-encoding":
            continue
        headers[key] = value
    return headers


def _copy_proxy_response_headers(headers) -> dict[str, str]:
    copied: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in _HOP_BY_HOP_HEADERS:
            continue
        copied[key] = value
    return copied


def _fetch_dev_server_response(
    *,
    url: str,
    method: str,
    headers: dict[str, str],
    body: bytes | None,
) -> tuple[int, dict[str, str], bytes]:
    request = UrlRequest(url, data=body if body else None, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10.0) as upstream:
            return upstream.status, _copy_proxy_response_headers(upstream.headers), upstream.read()
    except HTTPError as exc:
        return exc.code, _copy_proxy_response_headers(exc.headers), exc.read()
    except URLError as exc:
        raise RuntimeError(f"Failed to proxy request to Vite dev server: {exc}") from exc


async def _proxy_dev_server_http(request: Request) -> Response:
    dev_server_url = _dev_server_url()
    if not dev_server_url:
        return Response("Vite dev server URL is not configured.", status_code=503)

    path = request.url.path or "/"
    query = request.url.query
    target = f"{dev_server_url}{path}"
    if query:
        target = f"{target}?{query}"

    body = await request.body()
    try:
        status_code, headers, payload = await asyncio.to_thread(
            _fetch_dev_server_response,
            url=target,
            method=request.method,
            headers=_copy_proxy_request_headers(request),
            body=body or None,
        )
    except RuntimeError as exc:
        return Response(str(exc), status_code=502)

    response = Response(payload, status_code=status_code, headers=headers)
    response.headers["X-Fastlit-Dev-Proxy"] = "vite"
    return response


async def homepage(request):
    """Serve the frontend SPA entry point."""
    ws_token = request.query_params.get("fastlit_ws_token")
    if ws_token:
        response = RedirectResponse(
            _clean_request_url(request, "fastlit_ws_token"),
            status_code=307,
        )
        response.set_cookie(
            "fastlit_ws_token",
            ws_token,
            path="/",
            httponly=True,
            samesite="lax",
            secure=_should_use_secure_cookies(request),
        )
        return response

    if _env_flag("FASTLIT_DEV_MODE", default=False):
        return await _proxy_dev_server_http(request)

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
    <div id="root">
        <p>Frontend not built. Run: cd frontend && npm install && npm run build</p>
    </div>
</body>
</html>""",
        status_code=200,
    )


async def ws_endpoint(websocket: WebSocket):
    """WebSocket endpoint for client connections."""
    await handle_websocket(websocket, _script_path)


async def vite_hmr_proxy_endpoint(websocket: WebSocket):
    """Proxy Vite HMR WebSocket through the backend dev URL."""
    if not _env_flag("FASTLIT_DEV_MODE", default=False):
        await websocket.close(code=1008, reason="Vite HMR proxy is only available in dev mode")
        return

    dev_server_url = _dev_server_url()
    if not dev_server_url:
        await websocket.close(code=1011, reason="Vite dev server URL is not configured")
        return

    target_url = dev_server_url.replace("http://", "ws://", 1).replace(
        "https://", "wss://", 1
    ) + "/_vite_hmr"
    query = websocket.url.query
    if query:
        target_url = f"{target_url}?{query}"

    await websocket.accept()
    try:
        async with ws_connect(target_url) as upstream:
            async def browser_to_vite() -> None:
                while True:
                    message = await websocket.receive()
                    message_type = message.get("type")
                    if message_type == "websocket.disconnect":
                        break
                    text = message.get("text")
                    data = message.get("bytes")
                    if text is not None:
                        await upstream.send(text)
                    elif data is not None:
                        await upstream.send(data)

            async def vite_to_browser() -> None:
                while True:
                    payload = await upstream.recv()
                    if isinstance(payload, bytes):
                        await websocket.send_bytes(payload)
                    else:
                        await websocket.send_text(payload)

            forward_client = asyncio.create_task(browser_to_vite())
            forward_vite = asyncio.create_task(vite_to_browser())
            done, pending = await asyncio.wait(
                {forward_client, forward_vite},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                task.result()
    except (ConnectionClosed, OSError):
        pass
    finally:
        await websocket.close()


async def metrics_endpoint(_request: Request):
    """Expose in-memory runtime metrics as JSON."""
    return JSONResponse(metrics.snapshot())


async def prometheus_metrics_endpoint(_request: Request) -> Response:
    """Expose runtime metrics in Prometheus text format."""
    return Response(metrics.prometheus_text(), media_type="text/plain; version=0.0.4")


async def health_endpoint(_request: Request) -> Response:
    """Basic liveness endpoint."""
    snap = metrics.snapshot()
    return JSONResponse({"status": "ok", "uptime_seconds": snap["uptime_seconds"]})


async def ready_endpoint(_request: Request) -> Response:
    """Readiness endpoint that verifies the configured app script is loadable."""
    ready, error = check_script_loadable(_script_path)
    if ready:
        return JSONResponse({"status": "ready"})
    return JSONResponse(
        {"status": "error", "error": error or "script not ready"},
        status_code=503,
    )


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

    # Resolve and sanitize path — prevent directory traversal (including symlinks)
    base_path = Path(base).resolve(strict=True)
    # Normalize first to collapse .. before resolving, preventing symlink bypass
    raw_requested = (base_path / file_path.lstrip("/\\"))
    try:
        requested_path = raw_requested.resolve(strict=True)
        requested_path.relative_to(base_path)
    except (ValueError, OSError):
        return Response("Forbidden", status_code=403)

    if not requested_path.is_file():
        # SPA fallback: serve index.html for sub-paths
        index_fallback = base_path / "index.html"
        if index_fallback.is_file():
            return FileResponse(str(index_fallback), media_type="text/html")
        return Response("Not found", status_code=404)

    mime, _ = mimetypes.guess_type(str(requested_path))
    return FileResponse(str(requested_path), media_type=mime or "application/octet-stream")


async def _get_process_dataframe_slice(
    request: Request,
    *,
    source_id: str,
    query: DataframeQuery,
) -> dict[str, object] | None:
    session_id = extract_session_id(source_id)
    if session_id is None:
        return None

    session_store = getattr(getattr(request.app, "state", None), "session_store", None)
    if session_store is None:
        return None

    record = await session_store.get(session_id)
    if record is None:
        return None

    worker = getattr(record, "process_worker", None)
    if worker is None:
        return None

    try:
        payload = await worker.query_dataframe(
            source_id=source_id,
            query=query,
            timeout_seconds=float(os.environ.get("FASTLIT_RUN_TIMEOUT_SECONDS", "60")),
        )
    except (asyncio.TimeoutError, SessionProcessCrashedError, SessionProcessExecutionError) as exc:
        logger.warning(
            "process dataframe query failed source_id=%s session_id=%s error=%s",
            source_id,
            session_id,
            exc,
        )
        return None

    record.last_activity = time.monotonic()
    return payload


async def dataframe_slice_endpoint(request):
    """Serve server-side dataframe row windows."""
    source_id = request.path_params.get("source_id", "")
    response_format = request.query_params.get("format", "json").strip().lower()
    try:
        offset = int(request.query_params.get("offset", "0"))
        limit = int(request.query_params.get("limit", "200"))
    except ValueError:
        return JSONResponse({"error": "invalid offset/limit"}, status_code=400)
    search = request.query_params.get("search", "")
    try:
        sorts = _parse_dataframe_sorts(request.query_params.get("sort", ""))
        filters = _parse_dataframe_filters(request.query_params.get("filters", ""))
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    query = DataframeQuery(
        offset=offset,
        limit=limit,
        search=search,
        sorts=tuple(sorts),
        filters=tuple(filters),
    )
    data = await asyncio.to_thread(get_dataframe_slice, source_id, query)
    if data is None:
        data = await _get_process_dataframe_slice(
            request,
            source_id=source_id,
            query=query,
        )
    if data is None:
        return JSONResponse({"error": "unknown dataframe source"}, status_code=404)
    meta = data.pop("_fastlitMeta", {}) if isinstance(data, dict) else {}
    logger.debug(
        "dataframe query source_id=%s offset=%s limit=%s search_len=%s sort_count=%s filter_count=%s transport=%s schema_version=%s cache_hit=%s elapsed_ms=%s result_rows=%s total_rows=%s",
        source_id,
        offset,
        limit,
        len(search),
        len(sorts),
        len(filters),
        response_format,
        data.get("schemaVersion"),
        meta.get("cacheHit"),
        meta.get("elapsedMs"),
        len(data.get("rows", [])) if isinstance(data.get("rows"), list) else 0,
        data.get("totalRows"),
    )
    if response_format == "arrow":
        arrow_payload = serialize_arrow_frame(
            columns=data.get("columns", []),
            rows=data.get("rows", []),
            index=data.get("index"),
            positions=data.get("positions"),
        )
        if arrow_payload is not None:
            headers = {
                "X-Fastlit-Offset": str(data.get("offset", 0)),
                "X-Fastlit-Limit": str(data.get("limit", 0)),
                "X-Fastlit-Total-Rows": str(data.get("totalRows", 0)),
                "X-Fastlit-Transport": "arrow",
            }
            schema_version = data.get("schemaVersion")
            if schema_version:
                headers["X-Fastlit-Schema-Version"] = str(schema_version)
            return Response(
                arrow_payload,
                media_type=ARROW_STREAM_MEDIA_TYPE,
                headers=headers,
            )
    return JSONResponse(data)


def _parse_dataframe_sorts(raw: str) -> list[DataframeSort]:
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid sort payload") from exc
    if not isinstance(payload, list):
        raise ValueError("sort payload must be a list")
    sorts: list[DataframeSort] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        column = str(item.get("column", "")).strip()
        direction = str(item.get("direction", "asc")).strip().lower()
        if not column:
            continue
        if direction not in {"asc", "desc"}:
            direction = "asc"
        sorts.append(DataframeSort(column=column, direction=direction))
    return sorts


def _parse_dataframe_filters(raw: str) -> list[DataframeFilter]:
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid filters payload") from exc
    if not isinstance(payload, list):
        raise ValueError("filters payload must be a list")
    filters: list[DataframeFilter] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        column = str(item.get("column", "")).strip()
        op = str(item.get("op", "")).strip()
        if not column or not op:
            continue
        if op not in _VALID_FILTER_OPS:
            logger.warning("Ignoring invalid dataframe filter op=%s column=%s", op, column)
            continue
        filters.append(DataframeFilter(column=column, op=op, value=item.get("value")))
    return filters


@asynccontextmanager
async def _lifespan(app: Starlette) -> AsyncIterator[None]:
    """ASGI lifespan: run startup/shutdown hooks (B3)."""
    global _server_started
    cleanup_task: asyncio.Task | None = None

    async def _session_cleanup_loop() -> None:
        session_store = getattr(app.state, "session_store", None)
        if session_store is None:
            return
        timeout_seconds = max(
            60.0,
            float(os.environ.get("FASTLIT_SESSION_TIMEOUT_SECONDS", "3600")),
        )
        while True:
            await asyncio.sleep(60.0)
            stale = await session_store.evict_idle(idle_seconds=timeout_seconds)
            for record in stale:
                metrics.record_session_timeout(1)
                metrics.on_session_closed()
                logger.info(
                    "Closing idle session %s after %.0fs",
                    record.session.session_id,
                    timeout_seconds,
                )
                with suppress(Exception):
                    await record.websocket.close(code=1001, reason="Session idle timeout")

    for fn in _startup_handlers:
        if asyncio.iscoroutinefunction(fn):
            await fn()
        else:
            fn()

    _server_started = True
    cleanup_task = asyncio.create_task(_session_cleanup_loop())
    yield
    _server_started = False
    # Clear dedup set so hooks re-register correctly after hot reload
    _registered_startup_keys.clear()

    if cleanup_task is not None:
        cleanup_task.cancel()
        await asyncio.gather(cleanup_task, return_exceptions=True)

    for fn in _shutdown_handlers:
        if asyncio.iscoroutinefunction(fn):
            await fn()
        else:
            fn()
    await clear_resource_caches()


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
    configure_logging()

    if script_path is None:
        script_path = os.environ.get("FASTLIT_SCRIPT_PATH", "")

    set_script_path(script_path)

    # Resolve static directory
    if static_dir is None:
        # Default: look for built frontend assets next to the server package
        static_dir = os.path.join(os.path.dirname(__file__), "static")
    set_static_dir(static_dir)

    # Load auth config from secrets.toml (optional — auth disabled if absent)
    _auth_cfg: dict = {}
    try:
        from fastlit.ui.secrets import _load_secrets as _ls
        _auth_cfg = dict(_ls().get("auth", {}))
    except Exception:
        pass

    # Build routes list
    routes = [WebSocketRoute("/ws", ws_endpoint)]
    if _env_flag("FASTLIT_DEV_MODE", default=False):
        routes.append(WebSocketRoute("/_vite_hmr", vite_hmr_proxy_endpoint))

    # Auth routes (must appear before the SPA catch-all)
    if _auth_cfg:
        from fastlit.server.auth import route_login, route_callback, route_logout
        routes += [
            Route("/auth/login", route_login),
            Route("/auth/callback", route_callback),
            Route("/auth/logout", route_logout),
        ]

    if os.environ.get("FASTLIT_ENABLE_METRICS", "1") not in {"0", "false", "False"}:
        routes.append(Route("/_fastlit/metrics", metrics_endpoint))
        routes.append(Route("/_fastlit/metrics/prometheus", prometheus_metrics_endpoint))
    routes.append(Route("/_fastlit/health", health_endpoint))
    routes.append(Route("/_fastlit/ready", ready_endpoint))
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
    app.state.session_store = InMemorySessionStore()

    app.state.auth_cfg = _auth_cfg

    # Attach auth state so route handlers and middleware can access config
    if _auth_cfg:
        from fastlit.server.auth import OIDCClient, AuthMiddleware, InMemoryAuthSessionStore
        _oidc = OIDCClient(_auth_cfg)
        app.state.oidc_client = _oidc
        app.state.auth_session_store = InMemoryAuthSessionStore()

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.add_middleware(_StaticCacheMiddleware)

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

    if not _env_flag("FASTLIT_DEV_MODE", default=False):
        enable_csp = _env_flag("FASTLIT_ENABLE_CSP", default=True)
        csp_policy: str | None = os.environ.get("FASTLIT_CSP", "").strip()
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

    # AuthMiddleware added last = outermost layer (runs before all other middleware)
    if _auth_cfg:
        app.add_middleware(AuthMiddleware, cfg=_auth_cfg, oidc=_oidc)

    return app
