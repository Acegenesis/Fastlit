"""DataFrame display widget with virtualization support."""

from __future__ import annotations

from typing import Any

from fastlit.ui.base import _emit_node


def dataframe(
    data: Any,
    *,
    height: int | None = None,
    use_container_width: bool = True,
    hide_index: bool = False,
    key: str | None = None,
) -> None:
    """Display a DataFrame with virtualized scrolling.

    Args:
        data: A pandas DataFrame, dict, list, or other tabular data.
        height: Fixed height in pixels. If None, auto-sizes up to 400px.
        use_container_width: If True, stretches to container width.
        hide_index: If True, hides the row index column.
        key: Optional key for stable identity.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        >>> st.dataframe(df)
    """
    # Convert data to serializable format
    columns, rows, index = _serialize_dataframe(data, hide_index)

    props = {
        "columns": columns,
        "rows": rows,
        "height": height,
        "useContainerWidth": use_container_width,
    }

    if not hide_index and index is not None:
        props["index"] = index

    _emit_node("dataframe", props, key=key)


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

    props = {
        "columns": columns,
        "rows": rows,
        "static": True,
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
            return _serialize_pandas(data, hide_index)
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


def _serialize_pandas(
    df: Any,  # pandas.DataFrame
    hide_index: bool,
) -> tuple[list[dict], list[list], list | None]:
    """Serialize a pandas DataFrame."""
    columns = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        col_type = _dtype_to_type(dtype)
        columns.append({"name": str(col), "type": col_type})

    # Convert to list of lists for efficient JSON serialization
    rows = df.values.tolist()

    # Handle non-serializable types (e.g., Timestamp)
    for i, row in enumerate(rows):
        rows[i] = [_to_json_safe(v) for v in row]

    # Index
    index = None
    if not hide_index:
        index = [_to_json_safe(v) for v in df.index.tolist()]

    return columns, rows, index


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
