"""In-memory session store used by the WebSocket runtime."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Protocol

from starlette.websockets import WebSocket

from fastlit.runtime.session import Session


@dataclass(slots=True)
class SessionRecord:
    session: Session
    websocket: WebSocket
    client_ip: str
    request_id: str
    connected_at: float
    last_activity: float
    run_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    process_worker: Any | None = None


class SessionStore(Protocol):
    async def add(
        self,
        session: Session,
        *,
        websocket: WebSocket,
        client_ip: str,
        request_id: str,
    ) -> SessionRecord: ...

    async def get(self, session_id: str) -> SessionRecord | None: ...

    async def count(self) -> int: ...

    async def touch(
        self,
        session_id: str,
        *,
        at: float | None = None,
    ) -> SessionRecord | None: ...

    async def remove(self, session_id: str) -> SessionRecord | None: ...

    async def evict_idle(
        self,
        *,
        idle_seconds: float,
        now: float | None = None,
    ) -> list[SessionRecord]: ...


class InMemorySessionStore:
    """Async in-memory session registry keyed by session id."""

    __slots__ = ("_sessions", "_lock")

    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}
        self._lock = asyncio.Lock()

    async def add(
        self,
        session: Session,
        *,
        websocket: WebSocket,
        client_ip: str,
        request_id: str,
    ) -> SessionRecord:
        now = monotonic()
        record = SessionRecord(
            session=session,
            websocket=websocket,
            client_ip=client_ip,
            request_id=request_id,
            connected_at=now,
            last_activity=now,
        )
        async with self._lock:
            self._sessions[session.session_id] = record
        return record

    async def get(self, session_id: str) -> SessionRecord | None:
        async with self._lock:
            return self._sessions.get(session_id)

    async def count(self) -> int:
        async with self._lock:
            return len(self._sessions)

    async def touch(
        self,
        session_id: str,
        *,
        at: float | None = None,
    ) -> SessionRecord | None:
        timestamp = monotonic() if at is None else float(at)
        async with self._lock:
            record = self._sessions.get(session_id)
            if record:
                record.last_activity = timestamp
            return record

    async def remove(self, session_id: str) -> SessionRecord | None:
        async with self._lock:
            return self._sessions.pop(session_id, None)

    async def evict_idle(
        self,
        *,
        idle_seconds: float,
        now: float | None = None,
    ) -> list[SessionRecord]:
        current_time = monotonic() if now is None else float(now)

        async with self._lock:
            stale_ids = [
                session_id
                for session_id, record in self._sessions.items()
                if current_time - record.last_activity > idle_seconds
            ]
            return [self._sessions.pop(session_id) for session_id in stale_ids]