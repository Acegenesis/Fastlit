import json
import time
from concurrent.futures import ThreadPoolExecutor

from fastlit.server import dataframe_store as dataframe_store_module
from fastlit.server.app import _parse_dataframe_filters
from fastlit.server.dataframe_store import DataframeQuery, DataframeSort, _SOURCES, get_slice, register_source


def setup_function() -> None:
    _SOURCES.clear()


def test_parse_dataframe_filters_rejects_unknown_ops() -> None:
    filters = _parse_dataframe_filters(
        '[{"column":"Name","op":"contains","value":"a"},{"column":"Name","op":"__hack__","value":"b"}]'
    )

    assert len(filters) == 1
    assert filters[0].op == "contains"


def test_get_slice_ignores_invalid_sort_columns() -> None:
    source_id = register_source(
        columns=[{"name": "Name"}, {"name": "Score"}],
        rows=[["Alice", 90], ["Bob", 80]],
        total_rows=2,
    )

    payload = get_slice(
        source_id,
        DataframeQuery(
            offset=0,
            limit=10,
            sorts=(DataframeSort(column="Missing", direction="desc"),),
        ),
    )

    assert payload is not None
    assert [row[0] for row in payload["rows"]] == ["Alice", "Bob"]


def test_get_slice_prunes_expired_sources_on_read(monkeypatch) -> None:
    monkeypatch.setattr(dataframe_store_module, "_TTL_SECONDS", 0)
    source_id = register_source(
        columns=[{"name": "Name"}],
        rows=[["Alice"]],
        total_rows=1,
    )

    created_at = _SOURCES[source_id].last_access
    monkeypatch.setattr(dataframe_store_module.time, "time", lambda: created_at + 10_000.0)

    payload = get_slice(source_id, DataframeQuery(offset=0, limit=10))

    assert payload is None
    assert source_id not in _SOURCES


def test_register_source_evicts_lru_when_memory_budget_exceeded(monkeypatch) -> None:
    first_id = register_source(
        columns=[{"name": "Name"}],
        rows=[["Alice" * 20]],
        total_rows=1,
    )
    first_size = _SOURCES[first_id].estimated_bytes
    monkeypatch.setattr(dataframe_store_module, "_MAX_TOTAL_BYTES", first_size + max(32, first_size // 2))
    second_id = register_source(
        columns=[{"name": "Name"}],
        rows=[["Bob" * 20]],
        total_rows=1,
    )

    assert second_id in _SOURCES
    assert first_id not in _SOURCES


def test_get_slice_deduplicates_concurrent_query_fn_calls() -> None:
    calls = {"count": 0}
    gate = dataframe_store_module.threading.Event()

    def query_fn(query: DataframeQuery) -> dict:
        calls["count"] += 1
        gate.wait(timeout=1.0)
        return {
            "offset": query.offset,
            "limit": query.limit,
            "totalRows": 1,
            "rows": [["Alice"]],
            "index": [0],
            "positions": [0],
        }

    source_id = register_source(
        columns=[{"name": "Name"}],
        rows=None,
        total_rows=1,
        query_fn=query_fn,
    )
    query = DataframeQuery(offset=0, limit=10)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(get_slice, source_id, query) for _ in range(4)]
        gate.set()
        payloads = [future.result(timeout=2.0) for future in futures]

    assert calls["count"] == 1
    assert all(payload is not None for payload in payloads)
    assert payloads[0]["rows"] == [["Alice"]]


def test_estimate_payload_bytes_is_fast_for_large_payload() -> None:
    """Estimation must complete under 5ms for a 5000-row payload."""
    from fastlit.server.dataframe_store import _estimate_payload_bytes

    large_payload = {
        "columns": [{"name": f"col{i}"} for i in range(10)],
        "rows": [[f"val_{r}_{c}" for c in range(10)] for r in range(5000)],
        "total_rows": 5000,
    }

    t0 = time.perf_counter()
    size = _estimate_payload_bytes(large_payload)
    elapsed = time.perf_counter() - t0

    assert size > 0
    assert elapsed < 0.005, f"estimation took {elapsed*1000:.1f}ms — too slow"


def test_estimate_payload_bytes_returns_reasonable_estimate() -> None:
    """Sample-based estimate should be within 50% of the exact value for uniform rows."""
    from fastlit.server.dataframe_store import _estimate_payload_bytes

    payload = {
        "columns": [{"name": "a"}, {"name": "b"}],
        "rows": [[f"value_{r}", r] for r in range(100)],
        "total_rows": 100,
    }
    exact = len(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    estimated = _estimate_payload_bytes(payload)

    # Within 50% of exact (sample-based estimates are approximate)
    assert 0.5 * exact <= estimated <= 2.0 * exact, (
        f"estimate {estimated} is too far from exact {exact}"
    )


def test_copy_payload_preserves_structure() -> None:
    """_copy_payload must return an independent copy with same data."""
    from fastlit.server.dataframe_store import _copy_payload

    payload = {
        "columns": [{"name": "a"}],
        "rows": [["x", 1], ["y", 2]],
        "total_rows": 2,
        "_fastlitMeta": {"cacheHit": False, "elapsedMs": 1.0},
    }
    copied = _copy_payload(payload)

    assert copied == payload
    assert copied is not payload
    assert copied["rows"] is not payload["rows"]
    # Mutating a row in the copy must not affect the original
    copied["rows"][0][0] = "mutated"
    assert payload["rows"][0][0] == "x"
