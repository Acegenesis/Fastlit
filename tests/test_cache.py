import asyncio
import datetime as dt
from concurrent.futures import ThreadPoolExecutor
import threading

import fastlit as st
from fastlit.cache import clear_resource_caches
from fastlit.ui.widget_value import LiveValue, WidgetValue


def test_cache_data_returns_isolated_copies_for_pandas_dataframe() -> None:
    try:
        import pandas as pd
    except ImportError:
        return

    calls = {"count": 0}

    @st.cache_data
    def load_frame():
        calls["count"] += 1
        return pd.DataFrame({"value": [1, 2, 3]})

    first = load_frame()
    second = load_frame()

    assert calls["count"] == 1
    assert first.equals(second)
    assert first is not second

    first.loc[0, "value"] = 999
    third = load_frame()
    assert third.loc[0, "value"] == 1


def test_cache_data_singleflight_deduplicates_concurrent_calls() -> None:
    calls = {"count": 0}
    gate = threading.Event()

    @st.cache_data
    def load_payload(value: int) -> dict[str, int]:
        calls["count"] += 1
        gate.wait(timeout=1.0)
        return {"value": value}

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(load_payload, 7) for _ in range(8)]
        gate.set()
        results = [future.result(timeout=2.0) for future in futures]

    assert calls["count"] == 1
    assert all(result == {"value": 7} for result in results)


def test_cache_data_rejects_unsupported_argument_types() -> None:
    class Unsupported:
        pass

    @st.cache_data
    def load_value(value):
        return value

    try:
        load_value(Unsupported())
    except TypeError as exc:
        assert "Unsupported cache_data argument type" in str(exc)
    else:
        raise AssertionError("Expected TypeError for unsupported cache_data argument")


def test_cache_data_accepts_widget_value_arguments() -> None:
    calls = {"count": 0}

    @st.cache_data
    def load_value(value):
        calls["count"] += 1
        return value * 2

    first = load_value(WidgetValue(7, "widget-a"))
    second = load_value(WidgetValue(7, "widget-b"))

    assert first == 14
    assert second == 14
    assert calls["count"] == 1


def test_cache_data_accepts_live_value_arguments() -> None:
    calls = {"count": 0}

    @st.cache_data
    def load_value(value):
        calls["count"] += 1
        return value + 1

    spec = {"kind": "widget", "widgetId": "widget-a"}
    first = load_value(LiveValue(3, spec))
    second = load_value(LiveValue(3, {"kind": "widget", "widgetId": "widget-b"}))

    assert first == 4
    assert second == 4
    assert calls["count"] == 1


def test_cache_data_accepts_widget_dates() -> None:
    calls = {"count": 0}

    @st.cache_data
    def load_value(value):
        calls["count"] += 1
        return value._val.isoformat()

    first = load_value(WidgetValue(dt.date(2026, 3, 12), "date-a"))
    second = load_value(WidgetValue(dt.date(2026, 3, 12), "date-b"))

    assert first == "2026-03-12"
    assert second == "2026-03-12"
    assert calls["count"] == 1


def test_cache_resource_cleanup_runs_on_clear_and_shutdown() -> None:
    cleaned: list[str] = []

    @st.cache_resource(cleanup=lambda value: cleaned.append(value["name"]))
    def load_resource():
        return {"name": "db"}

    resource = load_resource()
    assert resource == {"name": "db"}

    load_resource.clear()
    assert cleaned == ["db"]

    load_resource()
    asyncio.run(clear_resource_caches())
    assert cleaned == ["db", "db"]
