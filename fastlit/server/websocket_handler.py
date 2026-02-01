"""WebSocket handler: manages the lifecycle of a client connection."""

from __future__ import annotations

import asyncio
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

        # Event loop
        while True:
            # Wait for at least one message
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") != "widget_event":
                logger.warning("Unknown message type: %s", msg.get("type"))
                continue

            # Apply this event
            event = WidgetEvent.from_dict(msg)
            session.widget_store[event.id] = event.value

            # Drain already-buffered messages (no artificial wait)
            # Events that arrived while script was running get coalesced naturally
            while True:
                try:
                    raw = await asyncio.wait_for(
                        websocket.receive_text(), timeout=0
                    )
                    queued = json.loads(raw)
                    if queued.get("type") == "widget_event":
                        ev = WidgetEvent.from_dict(queued)
                        session.widget_store[ev.id] = ev.value
                    else:
                        logger.warning("Unknown message type: %s", queued.get("type"))
                except asyncio.TimeoutError:
                    break

            # Now run the script once with all the latest values applied
            try:
                result = session.run()
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

    except Exception as exc:
        logger.info("Session %s disconnected: %s", session.session_id, exc)
    finally:
        logger.info("Session %s closed", session.session_id)
