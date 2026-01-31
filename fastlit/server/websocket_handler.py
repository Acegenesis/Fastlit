"""WebSocket handler: manages the lifecycle of a client connection."""

from __future__ import annotations

import json
import logging
import traceback

from starlette.websockets import WebSocket

from fastlit.runtime.protocol import WidgetEvent
from fastlit.runtime.session import Session, RerunException

logger = logging.getLogger("fastlit.ws")


async def handle_websocket(websocket: WebSocket, script_path: str) -> None:
    """Handle a single WebSocket connection."""
    await websocket.accept()

    session = Session(script_path)
    logger.info("Session %s connected", session.session_id)

    try:
        # Initial render — run the script and send the full tree
        result = session.run()
        await websocket.send_json(result.to_dict())
        logger.debug("Sent initial render (rev=%d)", session.rev)

        # Event loop — wait for widget events, rerun, send patches
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "widget_event":
                event = WidgetEvent.from_dict(msg)
                logger.debug("Widget event: %s = %r", event.id, event.value)

                try:
                    result = session.handle_widget_event(event.id, event.value)
                    await websocket.send_json(result.to_dict())
                    logger.debug("Sent patch (rev=%d)", session.rev)
                except Exception as exc:
                    logger.error("Error during rerun: %s", exc)
                    error_msg = {
                        "type": "error",
                        "message": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                    await websocket.send_json(error_msg)
            else:
                logger.warning("Unknown message type: %s", msg.get("type"))

    except Exception as exc:
        logger.info("Session %s disconnected: %s", session.session_id, exc)
    finally:
        logger.info("Session %s closed", session.session_id)
