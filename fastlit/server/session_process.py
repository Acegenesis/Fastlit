"""Supervised per-session worker process runtime."""

from __future__ import annotations

import asyncio
import multiprocessing as mp
import threading
import time
import traceback
from multiprocessing.connection import Connection
from typing import Any, Awaitable, Callable, cast

from fastlit.runtime.protocol import PatchOp, RenderFull, RenderPatch
from fastlit.runtime.session import Session
from fastlit.server.dataframe_store import DataframeQuery, get_slice as get_dataframe_slice


def _apply_events_to_session(session: Session, events: list[dict[str, Any]]) -> None:
    for event in events:
        path = event.get("path")
        if path is not None:
            session.set_current_path(path)
        session.widget_store[event["id"]] = event.get("value")


def _result_to_dict(result: RenderFull | RenderPatch | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return _plain_ipc_value(result.to_dict())


def _plain_ipc_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _plain_ipc_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_plain_ipc_value(item) for item in value]
    if isinstance(value, tuple):
        return [_plain_ipc_value(item) for item in value]
    if isinstance(value, set):
        return [_plain_ipc_value(item) for item in value]
    return value


def _run_session_command(
    session: Session,
    op_name: str,
    payload: dict[str, Any],
) -> RenderFull | RenderPatch | None:
    if op_name == "run":
        return session.run(
            force_full_render=bool(payload.get("force_full_render", False)),
            progressive=bool(payload.get("progressive", False)),
        )
    if op_name == "run_fragment":
        return session.run_fragment(str(payload["fragment_id"]))
    if op_name == "run_fragments":
        fragment_ids = [str(item) for item in payload.get("fragment_ids", [])]
        return session.run_fragments(fragment_ids)
    raise ValueError(f"Unsupported worker operation: {op_name}")


def _worker_main(conn: Connection, script_path: str, session_id: str) -> None:
    session = Session(script_path)
    session.session_id = session_id

    while True:
        try:
            command = conn.recv()
        except EOFError:
            break

        command_id = int(command.get("commandId", 0))
        op = str(command.get("op", ""))

        if op == "shutdown":
            conn.send({"type": "ack", "commandId": command_id})
            break

        if op == "sync_snapshot":
            session.restore_snapshot(command["snapshot"])
            conn.send({"type": "ack", "commandId": command_id})
            continue

        if op == "apply_events":
            _apply_events_to_session(session, list(command.get("events", [])))
            conn.send({"type": "ack", "commandId": command_id})
            continue

        if op == "execute":
            events = list(command.get("events", []))
            if events:
                _apply_events_to_session(session, events)

            payload = dict(command.get("payload", {}))
            result_box: dict[str, Any] = {}
            error_box: dict[str, BaseException] = {}
            traceback_box: dict[str, str] = {}

            def _target() -> None:
                try:
                    result_box["result"] = _run_session_command(
                        session,
                        str(command.get("commandName", "")),
                        payload,
                    )
                except BaseException as exc:  # noqa: BLE001
                    error_box["error"] = exc
                    traceback_box["traceback"] = traceback.format_exc()

            worker = threading.Thread(target=_target, daemon=True)
            worker.start()

            while worker.is_alive():
                for event in session.drain_runtime_events():
                    conn.send(
                        {
                            "type": "runtime_event",
                            "commandId": command_id,
                            "event": event,
                        }
                    )
                worker.join(timeout=0.01)

            for event in session.drain_runtime_events():
                conn.send(
                    {
                        "type": "runtime_event",
                        "commandId": command_id,
                        "event": event,
                    }
                )

            if error_box:
                exc = error_box["error"]
                conn.send(
                    {
                        "type": "result",
                        "commandId": command_id,
                        "ok": False,
                        "error": str(exc),
                        "traceback": traceback_box.get("traceback", ""),
                    }
                )
                continue

            conn.send(
                {
                    "type": "result",
                    "commandId": command_id,
                    "ok": True,
                    "result": _result_to_dict(result_box.get("result")),
                    "snapshot": session.snapshot_state(),
                    "pendingRedirect": session.consume_pending_browser_redirect(),
                }
            )
            continue

        if op == "query_dataframe":
            try:
                payload = get_dataframe_slice(
                    str(command.get("sourceId", "")),
                    cast(DataframeQuery, command.get("query")),
                )
            except BaseException as exc:  # noqa: BLE001
                conn.send(
                    {
                        "type": "result",
                        "commandId": command_id,
                        "ok": False,
                        "error": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                )
                continue

            conn.send(
                {
                    "type": "result",
                    "commandId": command_id,
                    "ok": True,
                    "payload": _plain_ipc_value(payload),
                }
            )
            continue

        if op == "drain_streams":
            deferred = session._deferred_streams[:]
            session._deferred_streams.clear()
            for node_id, gen in deferred:
                try:
                    for chunk in gen:
                        if chunk is None:
                            continue
                        conn.send(
                            {
                                "type": "stream_chunk",
                                "commandId": command_id,
                                "nodeId": node_id,
                                "chunk": str(chunk),
                            }
                        )
                except BaseException as exc:  # noqa: BLE001
                    conn.send(
                        {
                            "type": "stream_error",
                            "commandId": command_id,
                            "nodeId": node_id,
                            "error": str(exc),
                        }
                    )
                finally:
                    conn.send(
                        {
                            "type": "stream_end",
                            "commandId": command_id,
                            "nodeId": node_id,
                        }
                    )
            conn.send({"type": "stream_complete", "commandId": command_id})
            continue

        conn.send(
            {
                "type": "result",
                "commandId": command_id,
                "ok": False,
                "error": f"Unknown worker op: {op}",
                "traceback": "",
            }
        )


class SessionProcessError(RuntimeError):
    """Base class for process worker failures."""


class SessionProcessExecutionError(SessionProcessError):
    """Raised when user code fails inside the worker process."""

    def __init__(self, message: str, *, worker_traceback: str = "") -> None:
        super().__init__(message)
        self.worker_traceback = worker_traceback


class SessionProcessCrashedError(SessionProcessError):
    """Raised when the worker process exits unexpectedly."""


class SessionProcessWorker:
    """Persistent subprocess that executes a session safely outside the main loop."""

    def __init__(self, *, script_path: str, session_id: str) -> None:
        self._script_path = script_path
        self._session_id = session_id
        self._ctx = mp.get_context("spawn")
        self._process: Any | None = None
        self._conn: Any | None = None
        self._next_command_id = 1
        self.requires_full_run = True

    def is_alive(self) -> bool:
        return self._process is not None and self._process.is_alive()

    def _start_process(self) -> None:
        if self.is_alive():
            return
        parent_conn, child_conn = self._ctx.Pipe()
        process = self._ctx.Process(
            target=_worker_main,
            args=(child_conn, self._script_path, self._session_id),
            daemon=True,
            name=f"fastlit-session-{self._session_id}",
        )
        process.start()
        child_conn.close()
        self._process = process
        self._conn = parent_conn

    def _next_id(self) -> int:
        command_id = self._next_command_id
        self._next_command_id += 1
        return command_id

    def _send(self, payload: dict[str, Any]) -> None:
        if self._conn is None:
            raise SessionProcessCrashedError("Session worker is not connected")
        self._conn.send(payload)

    async def _wait_for_message(
        self,
        *,
        command_id: int,
        timeout_seconds: float,
        handler: Callable[[dict[str, Any]], Awaitable[bool] | bool],
        reset_timeout_on_message: bool = False,
    ) -> None:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout_seconds
        while True:
            if self._conn is None:
                raise SessionProcessCrashedError("Session worker pipe closed")
            if self._conn.poll():
                message = self._conn.recv()
                if int(message.get("commandId", 0)) != command_id:
                    continue
                if reset_timeout_on_message:
                    deadline = loop.time() + timeout_seconds
                should_stop = handler(message)
                if asyncio.iscoroutine(should_stop):
                    should_stop = await should_stop
                if should_stop:
                    return
                continue
            if not self.is_alive():
                raise SessionProcessCrashedError("Session worker exited unexpectedly")
            if loop.time() >= deadline:
                raise asyncio.TimeoutError()
            await asyncio.sleep(0.01)

    async def sync_snapshot(self, snapshot: dict[str, Any]) -> None:
        self._start_process()
        command_id = self._next_id()
        self._send({"op": "sync_snapshot", "commandId": command_id, "snapshot": snapshot})

        async def _handle(message: dict[str, Any]) -> bool:
            return message.get("type") == "ack"

        await self._wait_for_message(
            command_id=command_id,
            timeout_seconds=10.0,
            handler=_handle,
        )
        self.requires_full_run = True

    async def apply_events(self, events: list[dict[str, Any]], *, timeout_seconds: float) -> None:
        if not events:
            return
        if not self.is_alive():
            raise SessionProcessCrashedError("Session worker is not running")
        command_id = self._next_id()
        self._send({"op": "apply_events", "commandId": command_id, "events": events})

        async def _handle(message: dict[str, Any]) -> bool:
            return message.get("type") == "ack"

        await self._wait_for_message(
            command_id=command_id,
            timeout_seconds=timeout_seconds,
            handler=_handle,
            reset_timeout_on_message=True,
        )

    async def execute(
        self,
        *,
        command_name: str,
        payload: dict[str, Any] | None,
        events: list[dict[str, Any]],
        timeout_seconds: float,
        on_runtime_event: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> tuple[dict[str, Any] | None, dict[str, Any], str | None]:
        if not self.is_alive():
            raise SessionProcessCrashedError("Session worker is not running")

        if self.requires_full_run and command_name != "run":
            command_name = "run"
            payload = {"force_full_render": False, "progressive": False}

        command_id = self._next_id()
        terminal: dict[str, Any] = {}
        self._send(
            {
                "op": "execute",
                "commandId": command_id,
                "commandName": command_name,
                "payload": payload or {},
                "events": events,
            }
        )

        async def _handle(message: dict[str, Any]) -> bool:
            message_type = message.get("type")
            if message_type == "runtime_event":
                await on_runtime_event(message["event"])
                return False
            if message_type == "result":
                terminal.update(message)
                return True
            return False

        await self._wait_for_message(
            command_id=command_id,
            timeout_seconds=timeout_seconds,
            handler=_handle,
            reset_timeout_on_message=True,
        )

        if not terminal.get("ok", False):
            raise SessionProcessExecutionError(
                str(terminal.get("error", "Worker execution failed")),
                worker_traceback=str(terminal.get("traceback", "")),
            )

        if command_name == "run":
            self.requires_full_run = False

        return (
            terminal.get("result"),
            dict(terminal["snapshot"]),
            cast(str | None, terminal.get("pendingRedirect")),
        )

    async def query_dataframe(
        self,
        *,
        source_id: str,
        query: DataframeQuery,
        timeout_seconds: float,
    ) -> dict[str, Any] | None:
        if not self.is_alive():
            raise SessionProcessCrashedError("Session worker is not running")

        command_id = self._next_id()
        terminal: dict[str, Any] = {}
        self._send(
            {
                "op": "query_dataframe",
                "commandId": command_id,
                "sourceId": source_id,
                "query": query,
            }
        )

        async def _handle(message: dict[str, Any]) -> bool:
            if message.get("type") == "result":
                terminal.update(message)
                return True
            return False

        await self._wait_for_message(
            command_id=command_id,
            timeout_seconds=timeout_seconds,
            handler=_handle,
            reset_timeout_on_message=True,
        )

        if not terminal.get("ok", False):
            raise SessionProcessExecutionError(
                str(terminal.get("error", "Worker dataframe query failed")),
                worker_traceback=str(terminal.get("traceback", "")),
            )

        payload = terminal.get("payload")
        return cast(dict[str, Any] | None, payload)

    async def drain_streams(
        self,
        *,
        timeout_seconds: float,
        on_stream_chunk: Callable[[str, str], Awaitable[None]],
        on_stream_end: Callable[[str], Awaitable[None]],
        on_stream_error: Callable[[str, str], Awaitable[None]],
    ) -> None:
        if not self.is_alive():
            raise SessionProcessCrashedError("Session worker is not running")
        command_id = self._next_id()
        self._send({"op": "drain_streams", "commandId": command_id})

        async def _handle(message: dict[str, Any]) -> bool:
            message_type = message.get("type")
            if message_type == "stream_chunk":
                await on_stream_chunk(str(message["nodeId"]), str(message["chunk"]))
                return False
            if message_type == "stream_end":
                await on_stream_end(str(message["nodeId"]))
                return False
            if message_type == "stream_error":
                await on_stream_error(
                    str(message["nodeId"]),
                    str(message.get("error", "Stream error")),
                )
                return False
            return message_type == "stream_complete"

        await self._wait_for_message(
            command_id=command_id,
            timeout_seconds=timeout_seconds,
            handler=_handle,
            reset_timeout_on_message=True,
        )

    async def restart(self, snapshot: dict[str, Any]) -> None:
        self.close()
        await self.sync_snapshot(snapshot)

    def close(self) -> None:
        process = self._process
        conn = self._conn
        self._process = None
        self._conn = None
        self.requires_full_run = True

        if process is None:
            return

        if conn is not None:
            try:
                command_id = self._next_id()
                conn.send({"op": "shutdown", "commandId": command_id})
            except Exception:
                pass

        process.join(timeout=0.5)
        if process.is_alive():
            process.terminate()
            process.join(timeout=1.0)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
