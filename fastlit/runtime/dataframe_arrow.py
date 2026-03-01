"""Apache Arrow helpers for DataFrame transport."""

from __future__ import annotations

import base64
import json
import os
from typing import Any


ARROW_STREAM_MEDIA_TYPE = "application/vnd.apache.arrow.stream"
_INDEX_COLUMN = "__fastlit_index__"
_POSITION_COLUMN = "__fastlit_position__"


def arrow_transport_enabled() -> bool:
    """Return whether Arrow transport is enabled."""
    raw = os.environ.get("FASTLIT_ENABLE_ARROW_TRANSPORT", "1")
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def arrow_transport_available() -> bool:
    """Return whether pyarrow is available and transport is enabled."""
    if not arrow_transport_enabled():
        return False
    try:
        import pyarrow  # noqa: F401
    except ImportError:
        return False
    return True


def default_arrow_min_rows() -> int:
    """Return the minimum row count before Arrow transport is preferred."""
    try:
        value = int(os.environ.get("FASTLIT_DF_ARROW_MIN_ROWS", "1000"))
    except ValueError:
        value = 1000
    return max(1, value)


def default_arrow_preview_rows(default_window_size: int) -> int:
    """Return the preview window size used before fetching more rows via Arrow."""
    try:
        value = int(
            os.environ.get("FASTLIT_DF_ARROW_PREVIEW_ROWS", str(default_window_size))
        )
    except ValueError:
        value = default_window_size
    return max(50, min(value, 5000))


def encode_arrow_frame_base64(
    *,
    columns: list[dict[str, Any]],
    rows: list[list[Any]],
    index: list[Any] | None = None,
    positions: list[int] | None = None,
) -> str | None:
    """Encode tabular data to an Arrow IPC stream and return a base64 payload."""
    payload = serialize_arrow_frame(
        columns=columns,
        rows=rows,
        index=index,
        positions=positions,
    )
    if payload is None:
        return None
    return base64.b64encode(payload).decode("ascii")


def serialize_arrow_frame(
    *,
    columns: list[dict[str, Any]],
    rows: list[list[Any]],
    index: list[Any] | None = None,
    positions: list[int] | None = None,
) -> bytes | None:
    """Serialize row-oriented data into an Arrow IPC byte stream."""
    if not arrow_transport_available():
        return None

    try:
        import pyarrow as pa
        import pyarrow.ipc as ipc
    except ImportError:
        return None

    column_names = [str(column.get("name", "")) for column in columns]
    arrays: dict[str, Any] = {}

    for idx, name in enumerate(column_names):
        values = [row[idx] if idx < len(row) else None for row in rows]
        arrays[name] = _build_arrow_array(pa, values)

    if index is not None:
        arrays[_INDEX_COLUMN] = _build_arrow_array(pa, index)
    if positions is not None:
        arrays[_POSITION_COLUMN] = _build_arrow_array(pa, positions)

    try:
        table = pa.table(arrays)
        sink = pa.BufferOutputStream()
        with ipc.new_stream(sink, table.schema) as writer:
            writer.write_table(table)
        return sink.getvalue().to_pybytes()
    except Exception:
        return None


def _build_arrow_array(pa: Any, values: list[Any]) -> Any:
    try:
        return pa.array(values)
    except Exception:
        fallback_values = [_coerce_arrow_value(value) for value in values]
        try:
            return pa.array(fallback_values)
        except Exception:
            return pa.array(
                [
                    None
                    if value is None
                    else json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list, tuple, set))
                    else str(value)
                    for value in fallback_values
                ],
                type=pa.string(),
            )


def _coerce_arrow_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {str(key): _coerce_arrow_value(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_coerce_arrow_value(item) for item in value]

    if isinstance(value, (bytes, bytearray)):
        return bytes(value)

    if isinstance(value, memoryview):
        return value.tobytes()

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    return str(value)
