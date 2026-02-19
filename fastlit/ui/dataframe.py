"""DataFrame display widget with virtualization support."""

from __future__ import annotations

import os
from typing import Any

from fastlit.ui.base import _emit_node


def dataframe(
    data: Any,
    *,
    height: int | None = None,
    use_container_width: bool = True,
    hide_index: bool = False,
    max_rows: int | None = None,
    key: str | None = None,
) -> None:
    """Display a DataFrame with virtualized scrolling.

    Args:
        data: A pandas DataFrame, dict, list, or other tabular data.
        height: Fixed height in pixels. If None, auto-sizes up to 400px.
        use_container_width: If True, stretches to container width.
        hide_index: If True, hides the row index column.
        max_rows: Maximum number of rows to serialize for display.
            If None, uses FASTLIT_MAX_DF_ROWS (default: 50_000).
        key: Optional key for stable identity.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        >>> st.dataframe(df)
    """
    resolved_max_rows = (
        _default_max_dataframe_rows()
        if max_rows is None
        else max(1, int(max_rows))
    )
    columns, rows, index, total_rows, truncated = _serialize_dataframe_preview(
        data, hide_index, resolved_max_rows
    )
    source_id = _maybe_register_server_source(
        data=data,
        columns=columns,
        rows=rows,
        index=index,
        hide_index=hide_index,
        total_rows=total_rows,
        preview_rows=len(rows),
    )

    props = {
        "columns": columns,
        "rows": rows,
        "height": height,
        "useContainerWidth": use_container_width,
        "totalRows": total_rows,
        "truncated": truncated,
    }

    if not hide_index and index is not None:
        props["index"] = index
    if source_id is not None:
        props["sourceId"] = source_id
        props["windowSize"] = _default_dataframe_window_size()

    _emit_node("dataframe", props, key=key)


def _default_max_dataframe_rows() -> int:
    """Default preview row cap for dataframe rendering."""
    try:
        value = int(os.environ.get("FASTLIT_MAX_DF_ROWS", "50000"))
    except ValueError:
        value = 50000
    return max(1, value)


def _default_dataframe_window_size() -> int:
    """Window size used by frontend server-side dataframe pagination."""
    try:
        value = int(os.environ.get("FASTLIT_DF_WINDOW_SIZE", "300"))
    except ValueError:
        value = 300
    return max(50, min(value, 5000))


def data_editor(
    data: Any,
    *,
    width: int | None = None,
    height: int | None = None,
    use_container_width: bool = True,
    hide_index: bool | None = None,
    column_order: list[str] | None = None,
    column_config: dict | None = None,
    num_rows: str = "fixed",
    disabled: bool | list[str] = False,
    key: str | None = None,
    on_change: Any = None,
) -> Any:
    """Display an editable DataFrame.

    Args:
        data: A pandas DataFrame, dict, list, or other tabular data.
        width: Fixed width in pixels.
        height: Fixed height in pixels. If None, auto-sizes.
        use_container_width: If True, stretches to container width.
        hide_index: If True, hides the row index column.
        column_order: List of column names in display order.
        column_config: Dict of column configurations.
        num_rows: "fixed" or "dynamic" (allow adding/deleting rows).
        disabled: If True, all columns disabled. If list, those columns disabled.
        key: Optional key for stable identity.
        on_change: Callback when data changes.

    Returns:
        The edited DataFrame (or original data type).
    """
    from fastlit.runtime.context import get_current_session

    # Convert data to serializable format
    columns, rows, index = _serialize_dataframe(data, hide_index or False)
    total_rows = len(rows)
    max_rows_cap = _default_max_dataframe_rows()
    rows, index, truncated = _truncate_rows(rows, index, max_rows_cap)

    # Apply column order if specified
    if column_order:
        col_indices = {c["name"]: i for i, c in enumerate(columns)}
        new_columns = []
        new_col_map = []
        for name in column_order:
            if name in col_indices:
                new_columns.append(columns[col_indices[name]])
                new_col_map.append(col_indices[name])
        columns = new_columns
        rows = [[row[i] for i in new_col_map] for row in rows]

    # Determine which columns are disabled
    disabled_cols = []
    if disabled is True:
        disabled_cols = [c["name"] for c in columns]
    elif isinstance(disabled, list):
        disabled_cols = disabled

    props = {
        "columns": columns,
        "rows": rows,
        "height": height,
        "width": width,
        "useContainerWidth": use_container_width,
        "editable": True,
        "numRows": num_rows,
        "disabledColumns": disabled_cols,
        "rerunOnChange": on_change is not None,
        "totalRows": total_rows,
        "truncated": truncated,
    }

    if not (hide_index or False) and index is not None:
        props["index"] = index

    if column_config:
        # Serialize Column objects to dictionaries
        props["columnConfig"] = {
            k: v.to_dict() if hasattr(v, 'to_dict') else v 
            for k, v in column_config.items()
        }

    node = _emit_node("data_editor", props, key=key, is_widget=True, no_rerun=True)

    # Get edited data from widget store
    session = get_current_session()
    stored = session.widget_store.get(node.id)

    if stored is not None:
        # Call on_change callback when data changed (A3: was silently ignored before)
        if on_change is not None:
            prev_key = f"_de_prev_{node.id}"
            prev = session.widget_store.get(prev_key)
            if prev != stored:
                session.widget_store[prev_key] = stored
                on_change()
        # Return edited data in original format
        return _deserialize_to_original(stored, data, columns)

    return data


def _deserialize_to_original(stored: dict, original: Any, columns: list) -> Any:
    """Convert stored edited data back to original format."""
    edited_rows = stored.get("rows", [])

    try:
        import pandas as pd

        if isinstance(original, pd.DataFrame):
            # Reconstruct DataFrame
            col_names = [c["name"] for c in columns]
            return pd.DataFrame(edited_rows, columns=col_names)
    except ImportError:
        pass

    # For dict/list, return as list of dicts
    col_names = [c["name"] for c in columns]
    return [dict(zip(col_names, row)) for row in edited_rows]


def table(
    data: Any,
    *,
    key: str | None = None,
) -> None:
    """Display a static table (no virtualization, for small data).

    Args:
        data: A pandas DataFrame, dict, list, or other tabular data.
        key: Optional key for stable identity.
    """
    columns, rows, index = _serialize_dataframe(data, hide_index=True)
    total_rows = len(rows)
    rows, _, truncated = _truncate_rows(rows, None, _default_max_dataframe_rows())

    props = {
        "columns": columns,
        "rows": rows,
        "static": True,
        "totalRows": total_rows,
        "truncated": truncated,
    }

    _emit_node("table", props, key=key)


def _serialize_dataframe(
    data: Any,
    hide_index: bool = False,
) -> tuple[list[dict], list[list], list | None]:
    """Convert various data types to columns + rows format.

    Returns:
        Tuple of (columns, rows, index) where:
        - columns: List of {"name": str, "type": str}
        - rows: List of row arrays (each row is a list of values)
        - index: List of index values (or None if hidden)
    """
    # Try pandas DataFrame
    try:
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            columns, rows, index, _, _ = _serialize_pandas(
                data, hide_index, max_rows=None
            )
            return columns, rows, index
    except ImportError:
        pass

    # Try dict of lists (column-oriented)
    if isinstance(data, dict):
        return _serialize_dict(data)

    # Try list of dicts (row-oriented)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return _serialize_list_of_dicts(data)

    # Try list of lists
    if isinstance(data, list):
        return _serialize_list_of_lists(data)

    # Fallback: convert to string
    return [{"name": "value", "type": "string"}], [[str(data)]], None


def _serialize_dataframe_preview(
    data: Any,
    hide_index: bool,
    max_rows: int,
) -> tuple[list[dict], list[list], list | None, int, bool]:
    """Serialize data for display with an upper row bound."""
    try:
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            return _serialize_pandas(data, hide_index, max_rows=max_rows)
    except ImportError:
        pass

    columns, rows, index = _serialize_dataframe(data, hide_index)
    total_rows = len(rows)
    if total_rows > max_rows:
        rows = rows[:max_rows]
        if index is not None:
            index = index[:max_rows]
        return columns, rows, index, total_rows, True
    return columns, rows, index, total_rows, False


def _maybe_register_server_source(
    *,
    data: Any,
    columns: list[dict[str, Any]],
    rows: list[list[Any]],
    index: list | None,
    hide_index: bool,
    total_rows: int,
    preview_rows: int,
) -> str | None:
    """Register a server-side source for large tables to support window fetches."""
    if total_rows <= preview_rows:
        return None
    if os.environ.get("FASTLIT_ENABLE_DF_SERVER_PAGING", "1") in {"0", "false", "False"}:
        return None

    try:
        from fastlit.server.dataframe_store import register_source
    except Exception:
        return None

    # Pandas path: keep raw dataframe server-side and slice lazily.
    try:
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            def slice_fn(start: int, end: int):
                view = data.iloc[start:end]
                out_rows = [[_to_json_safe(v) for v in row] for row in view.itertuples(index=False, name=None)]
                out_index = None if hide_index else [_to_json_safe(v) for v in view.index.tolist()]
                return out_rows, out_index

            return register_source(
                columns=columns,
                rows=None,
                index=None,
                slice_fn=slice_fn,
                total_rows=total_rows,
            )
    except ImportError:
        pass

    # Generic path: rows already materialized as a list.
    full_rows = rows
    full_index = index if not hide_index else None
    if total_rows > len(rows):
        try:
            _cols, full_rows, generic_index = _serialize_dataframe(data, hide_index)
            full_index = generic_index if not hide_index else None
        except Exception:
            # Fallback to preview rows only if full serialization fails.
            full_rows = rows
            full_index = index if not hide_index else None

    return register_source(
        columns=columns,
        rows=full_rows,
        index=full_index,
        total_rows=total_rows,
    )


def _truncate_rows(
    rows: list[list[Any]],
    index: list | None,
    max_rows: int,
) -> tuple[list[list[Any]], list | None, bool]:
    """Truncate rows/index to max_rows and report whether truncation occurred."""
    if len(rows) <= max_rows:
        return rows, index, False
    new_rows = rows[:max_rows]
    new_index = index[:max_rows] if index is not None else None
    return new_rows, new_index, True


def _serialize_pandas(
    df: Any,  # pandas.DataFrame
    hide_index: bool,
    *,
    max_rows: int | None = None,
) -> tuple[list[dict], list[list], list | None, int, bool]:
    """Serialize a pandas DataFrame."""
    total_rows = len(df)
    truncated = False
    view = df
    if max_rows is not None and total_rows > max_rows:
        view = df.iloc[:max_rows]
        truncated = True

    columns = []
    for col in view.columns:
        dtype = str(view[col].dtype)
        col_type = _dtype_to_type(dtype)
        columns.append({"name": str(col), "type": col_type})

    # Serialize row-by-row without materializing the full dataframe first.
    rows: list[list[Any]] = []
    for row in view.itertuples(index=False, name=None):
        rows.append([_to_json_safe(v) for v in row])

    # Index
    index = None
    if not hide_index:
        index = [_to_json_safe(v) for v in view.index.tolist()]

    return columns, rows, index, total_rows, truncated


def _serialize_dict(data: dict) -> tuple[list[dict], list[list], list | None]:
    """Serialize a dict of lists (column-oriented)."""
    columns = [{"name": str(k), "type": "auto"} for k in data.keys()]

    # Get max length
    max_len = max((len(v) if isinstance(v, list) else 1) for v in data.values())

    rows = []
    for i in range(max_len):
        row = []
        for v in data.values():
            if isinstance(v, list):
                row.append(_to_json_safe(v[i]) if i < len(v) else None)
            else:
                row.append(_to_json_safe(v) if i == 0 else None)
        rows.append(row)

    # Generate row indices
    index = list(range(max_len))

    return columns, rows, index


def _serialize_list_of_dicts(data: list[dict]) -> tuple[list[dict], list[list], list | None]:
    """Serialize a list of dicts (row-oriented)."""
    # Collect all keys
    all_keys = []
    seen = set()
    for row in data:
        for k in row.keys():
            if k not in seen:
                all_keys.append(k)
                seen.add(k)

    columns = [{"name": str(k), "type": "auto"} for k in all_keys]

    rows = []
    for row_dict in data:
        row = [_to_json_safe(row_dict.get(k)) for k in all_keys]
        rows.append(row)

    # Generate row indices
    index = list(range(len(data)))

    return columns, rows, index


def _serialize_list_of_lists(data: list) -> tuple[list[dict], list[list], list | None]:
    """Serialize a list of lists."""
    if not data:
        return [], [], None

    # Infer column count from first row
    first = data[0]
    if isinstance(first, (list, tuple)):
        num_cols = len(first)
    else:
        num_cols = 1
        data = [[item] for item in data]

    columns = [{"name": str(i), "type": "auto"} for i in range(num_cols)]
    rows = [[_to_json_safe(v) for v in row] for row in data]

    # Generate row indices
    index = list(range(len(data)))

    return columns, rows, index


def _dtype_to_type(dtype: str) -> str:
    """Map pandas dtype to simple type string."""
    dtype = dtype.lower()
    if "int" in dtype:
        return "integer"
    if "float" in dtype:
        return "number"
    if "bool" in dtype:
        return "boolean"
    if "datetime" in dtype or "timestamp" in dtype:
        return "datetime"
    if "date" in dtype:
        return "date"
    return "string"


def _to_json_safe(value: Any) -> Any:
    """Convert value to JSON-serializable type."""
    if value is None:
        return None

    # Handle pandas NA/NaT
    try:
        import pandas as pd

        if pd.isna(value):
            return None
    except (ImportError, TypeError, ValueError):
        pass

    # Handle numpy types
    try:
        import numpy as np

        if isinstance(value, (np.integer, np.floating)):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.bool_):
            return bool(value)
    except ImportError:
        pass

    # Handle datetime
    if hasattr(value, "isoformat"):
        return value.isoformat()

    # Check if already JSON-safe
    if isinstance(value, (str, int, float, bool)):
        return value

    # Fallback to string
    return str(value)
