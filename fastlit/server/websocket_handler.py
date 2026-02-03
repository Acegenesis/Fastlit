"""WebSocket handler: manages the lifecycle of a client connection."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import traceback

from starlette.websockets import WebSocket

from fastlit.runtime.protocol import WidgetEvent
from fastlit.runtime.session import Session, RerunException

logger = logging.getLogger("fastlit.ws")
# Enable debug logging for timing
logging.basicConfig(level=logging.DEBUG)


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
            t0 = time.perf_counter()
            raw = await websocket.receive_text()
            t1 = time.perf_counter()
            msg = json.loads(raw)

            if msg.get("type") != "widget_event":
                logger.warning("Unknown message type: %s", msg.get("type"))
                continue

            # Apply this event
            event = WidgetEvent.from_dict(msg)
            session.widget_store[event.id] = event.value
            should_rerun = not event.no_rerun
            logger.info("[TIMING] Received event id=%s noRerun=%s (waited %.3fms)",
                       event.id[-20:], event.no_rerun, (t1-t0)*1000)

            # Drain already-buffered messages (no artificial wait)
            # Events that arrived while script was running get coalesced naturally
            drained = 0
            while True:
                try:
                    raw = await asyncio.wait_for(
                        websocket.receive_text(), timeout=0
                    )
                    queued = json.loads(raw)
                    if queued.get("type") == "widget_event":
                        ev = WidgetEvent.from_dict(queued)
                        session.widget_store[ev.id] = ev.value
                        drained += 1
                        # If any event requires a rerun, do it
                        if not ev.no_rerun:
                            should_rerun = True
                    else:
                        logger.warning("Unknown message type: %s", queued.get("type"))
                except asyncio.TimeoutError:
                    break

            if drained > 0:
                logger.info("[TIMING] Drained %d additional messages", drained)

            # Skip rerun if all events were no_rerun (e.g., navigation-only)
            if not should_rerun:
                logger.debug("[TIMING] Skipping rerun (no_rerun=true)")
                continue

            # Now run the script once with all the latest values applied
            try:
                t2 = time.perf_counter()
                result = session.run()
                t3 = time.perf_counter()
                await websocket.send_json(result.to_dict())
                t4 = time.perf_counter()
                logger.info("[TIMING] Rerun took %.3fms, send took %.3fms (rev=%d)",
                           (t3-t2)*1000, (t4-t3)*1000, session.rev)
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
