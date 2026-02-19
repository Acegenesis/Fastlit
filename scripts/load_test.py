"""Basic WS load test for Fastlit.

Usage:
  python scripts/load_test.py --url ws://127.0.0.1:8501/ws --clients 50 --seconds 30
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import time
from dataclasses import dataclass
from typing import Any

try:
    import websockets
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency 'websockets'. Install with: pip install websockets"
    ) from exc


INTERACTIVE_TYPES = {
    "slider",
    "text_input",
    "text_area",
    "checkbox",
    "selectbox",
    "radio",
    "number_input",
    "multiselect",
    "date_input",
    "time_input",
    "toggle",
    "select_slider",
}


@dataclass
class Stats:
    clients_started: int = 0
    clients_finished: int = 0
    events_sent: int = 0
    errors: int = 0
    latencies_ms: list[float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.latencies_ms is None:
            self.latencies_ms = []


def _collect_widget_ids(tree: dict[str, Any] | None) -> list[str]:
    if not tree:
        return []
    ids: list[str] = []
    stack = [tree]
    while stack:
        node = stack.pop()
        if node.get("type") in INTERACTIVE_TYPES:
            nid = node.get("id")
            if isinstance(nid, str):
                ids.append(nid)
        children = node.get("children")
        if isinstance(children, list):
            stack.extend(children)
    return ids


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    idx = int(round((len(vals) - 1) * p))
    return vals[max(0, min(idx, len(vals) - 1))]


async def run_client(
    *,
    url: str,
    duration_s: float,
    send_interval_s: float,
    stats: Stats,
) -> None:
    stats.clients_started += 1
    started = time.perf_counter()

    try:
        async with websockets.connect(url, max_size=16 * 1024 * 1024) as ws:
            first = await ws.recv()
            msg = json.loads(first)
            widgets = _collect_widget_ids(msg.get("tree"))
            if not widgets:
                widgets = ["__noop__"]

            while (time.perf_counter() - started) < duration_s:
                wid = random.choice(widgets)
                value = random.random()
                payload = {
                    "type": "widget_event",
                    "id": wid,
                    "value": value,
                    "noRerun": False,
                }
                t0 = time.perf_counter()
                await ws.send(json.dumps(payload))
                stats.events_sent += 1

                # Wait one server message (patch/full/error).
                try:
                    await ws.recv()
                    t1 = time.perf_counter()
                    stats.latencies_ms.append((t1 - t0) * 1000)
                except Exception:
                    stats.errors += 1
                    break

                await asyncio.sleep(send_interval_s)
    except Exception:
        stats.errors += 1
    finally:
        stats.clients_finished += 1


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="ws://127.0.0.1:8501/ws")
    parser.add_argument("--clients", type=int, default=25)
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--interval-ms", type=float, default=200.0)
    args = parser.parse_args()

    stats = Stats()
    interval_s = max(0.01, args.interval_ms / 1000.0)

    tasks = [
        asyncio.create_task(
            run_client(
                url=args.url,
                duration_s=args.seconds,
                send_interval_s=interval_s,
                stats=stats,
            )
        )
        for _ in range(max(1, args.clients))
    ]
    await asyncio.gather(*tasks)

    p50 = _percentile(stats.latencies_ms, 0.50)
    p95 = _percentile(stats.latencies_ms, 0.95)
    p99 = _percentile(stats.latencies_ms, 0.99)
    print(
        json.dumps(
            {
                "clients_started": stats.clients_started,
                "clients_finished": stats.clients_finished,
                "events_sent": stats.events_sent,
                "errors": stats.errors,
                "latency_ms_p50": round(p50, 2),
                "latency_ms_p95": round(p95, 2),
                "latency_ms_p99": round(p99, 2),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
