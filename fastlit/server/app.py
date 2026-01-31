"""Starlette ASGI application: HTTP routes + WebSocket endpoint."""

from __future__ import annotations

import os
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import FileResponse, HTMLResponse
from starlette.routing import Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket

from fastlit.server.websocket_handler import handle_websocket

# Will be set by CLI before the app starts
_script_path: str = ""
_static_dir: str = ""


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


def create_app(script_path: str, static_dir: str | None = None) -> Starlette:
    """Create and configure the Starlette ASGI app."""
    set_script_path(script_path)

    # Resolve static directory
    if static_dir is None:
        # Default: look for built frontend assets next to the server package
        static_dir = os.path.join(os.path.dirname(__file__), "static")
    set_static_dir(static_dir)

    routes = [
        WebSocketRoute("/ws", ws_endpoint),
        Route("/", homepage),
    ]

    app = Starlette(routes=routes)

    # Mount static files if the directory exists
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static")

    return app
