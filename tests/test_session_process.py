import asyncio
from pathlib import Path

from fastlit.runtime.session import Session
from fastlit.server.session_process import SessionProcessWorker


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_session_process_worker_executes_full_run(tmp_path: Path) -> None:
    script_path = tmp_path / "worker_app.py"
    _write(
        script_path,
        """
import fastlit as st

st.text("hello from worker")
""".strip(),
    )

    session = Session(str(script_path))
    worker = SessionProcessWorker(
        script_path=str(script_path),
        session_id=session.session_id,
    )

    async def _exercise() -> None:
        await worker.sync_snapshot(session.snapshot_state())

        async def _on_runtime_event(_event: dict) -> None:
            return None

        result, snapshot, pending_redirect = await worker.execute(
            command_name="run",
            payload={"force_full_render": False, "progressive": False},
            events=[],
            timeout_seconds=10.0,
            on_runtime_event=_on_runtime_event,
        )

        assert pending_redirect is None
        assert result is not None
        assert result["type"] == "render_full"
        assert snapshot["rev"] == 1
        assert snapshot["previous_tree"] is not None

    try:
        asyncio.run(_exercise())
    finally:
        worker.close()


def test_session_process_worker_stream_timeout_is_idle_based(tmp_path: Path) -> None:
    class _AliveProcess:
        @staticmethod
        def is_alive() -> bool:
            return True

    class _FakeConn:
        def __init__(self, messages: list[tuple[float, dict]]) -> None:
            self._messages = list(messages)

        def send(self, _payload: dict) -> None:
            return None

        def poll(self) -> bool:
            if not self._messages:
                return False
            return asyncio.get_running_loop().time() >= self._messages[0][0]

        def recv(self) -> dict:
            _, message = self._messages.pop(0)
            return message

    worker = SessionProcessWorker(
        script_path=str(tmp_path / "unused.py"),
        session_id="session-test",
    )
    worker._process = _AliveProcess()
    worker._conn = _FakeConn(
        [
            (0.03, {"type": "stream_chunk", "commandId": 1, "nodeId": "node-1", "chunk": "a"}),
            (0.06, {"type": "stream_chunk", "commandId": 1, "nodeId": "node-1", "chunk": "b"}),
            (0.09, {"type": "stream_end", "commandId": 1, "nodeId": "node-1"}),
            (0.12, {"type": "stream_complete", "commandId": 1}),
        ]
    )

    async def _exercise() -> None:
        loop = asyncio.get_running_loop()
        start = loop.time()
        fake_conn = worker._conn
        assert fake_conn is not None
        fake_conn._messages = [
            (start + delay, message)
            for delay, message in fake_conn._messages
        ]

        chunks: list[str] = []
        ended: list[str] = []

        async def _on_stream_chunk(node_id: str, chunk: str) -> None:
            _ = node_id
            chunks.append(chunk)

        async def _on_stream_end(node_id: str) -> None:
            ended.append(node_id)

        async def _on_stream_error(node_id: str, error: str) -> None:
            raise AssertionError(f"Unexpected stream error for {node_id}: {error}")

        await worker.drain_streams(
            timeout_seconds=0.05,
            on_stream_chunk=_on_stream_chunk,
            on_stream_end=_on_stream_end,
            on_stream_error=_on_stream_error,
        )

        assert "".join(chunks) == "ab"
        assert ended == ["node-1"]

    asyncio.run(_exercise())
