"""DataFrame display widget with virtualization support."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable

from fastlit.ui.base import _emit_node


@dataclass
class DataframeSelection:
    """Selected row positions from st.dataframe(on_select=...)."""

    rows: list[int]


def dataframe(
    data: Any,
    *,
    width: int | str = "stretch",
    height: int | str = "auto",
    use_container_width: bool | None = None,
    hide_index: bool | None = None,
    column_order: list[str] | None = None,
    column_config: dict | None = None,
    row_height: int | None = None,
    placeholder: str | None = None,
    toolbar: bool = True,
    downloadable: bool = True,
    persist_view: bool = True,
    max_rows: int | None = None,
    on_select: str | Callable[[DataframeSelection], None] | None = None,
    selection_mode: str = "multi-row",
    key: str | None = None,
) -> DataframeSelection | None:
    """Display a DataFrame with virtualized scrolling.

    Args:
        data: A pandas DataFrame, dict, list, or other tabular data.
        width: "stretch" (default), "content", or a fixed pixel width.
        height: "auto" (default), "content", or a fixed pixel height.
        use_container_width: Legacy alias for width="stretch".
        hide_index: If True, hides the row index column.
        column_order: Ordered list of columns to display.
        column_config: Dict of column configurations.
        row_height: Fixed row height in pixels.
        placeholder: Placeholder text when the dataset is empty.
        toolbar: If True, show the grid toolbar.
        downloadable: If True, expose CSV export for the current view.
        persist_view: If True, persist the grid view state in sessionStorage.
        max_rows: Maximum number of rows to serialize for display.
            If None, uses FASTLIT_MAX_DF_ROWS (default: 50_000).
        on_select: None (default), "rerun", or a callable callback.
        selection_mode: "single-row" or "multi-row" (used when on_select is set).
        key: Optional key for stable identity.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        >>> st.dataframe(df)
    """
    if selection_mode not in {"single-row", "multi-row"}:
        raise ValueError("selection_mode must be 'single-row' or 'multi-row'")
    if on_select is not None and on_select != "rerun" and not callable(on_select):
        raise ValueError("on_select must be None, 'rerun', or a callable")

    hide_index_value = bool(hide_index)
    width_value, use_container_width_value = _resolve_width(width, use_container_width)
    resolved_max_rows = (
        _default_max_dataframe_rows()
        if max_rows is None
        else max(1, int(max_rows))
    )
    columns, rows, index, total_rows, truncated = _serialize_dataframe_preview(
        data, hide_index_value, resolved_max_rows
    )
    normalized_column_order = _normalize_column_order(columns, column_order)
    serialized_column_config = _serialize_column_config(column_config)
    source_id = _maybe_register_server_source(
        data=data,
        columns=columns,
        rows=rows,
        index=index,
        hide_index=hide_index_value,
        total_rows=total_rows,
        preview_rows=len(rows),
    )

    props = {
        "columns": columns,
        "rows": rows,
        "width": width_value,
        "height": height,
        "useContainerWidth": use_container_width_value,
        "rowHeight": row_height,
        "placeholder": placeholder,
        "toolbar": toolbar,
        "downloadable": downloadable,
        "persistView": persist_view,
        "totalRows": total_rows,
        "truncated": truncated,
    }

    if normalized_column_order:
        props["columnOrder"] = normalized_column_order
    if serialized_column_config:
        props["columnConfig"] = serialized_column_config
    if not hide_index_value and index is not None:
        props["index"] = index
    if source_id is not None:
        props["sourceId"] = source_id
        props["windowSize"] = _default_dataframe_window_size()

    if on_select is None:
        _emit_node("dataframe", props, key=key)
        return None

    from fastlit.runtime.context import get_current_session

    props["selectable"] = True
    props["selectionMode"] = selection_mode

    node = _emit_node("dataframe", props, key=key, is_widget=True)
    session = get_current_session()
    session._force_full_render_widget_ids.add(node.id)
    rows_selected = _normalize_selection_rows(
        session.widget_store.get(node.id), selection_mode
    )
    node.props["selectedRows"] = rows_selected
    selection = DataframeSelection(rows=rows_selected)

    if callable(on_select):
        prev_key = f"_dfsel_prev_{node.id}"
        if prev_key not in session.widget_store:
            session.widget_store[prev_key] = rows_selected
        elif session.widget_store.get(prev_key) != rows_selected:
            session.widget_store[prev_key] = rows_selected
            try:
                on_select(selection)
            except TypeError:
                on_select()

    return selection


def _default_max_dataframe_rows() -> int:
    """Default preview row cap for dataframe rendering."""
    try:
        value = int(os.environ.get("FASTLIT_MAX_DF_ROWS", "50000"))
    except ValueError:
        value = 50000
    return max(1, value)


def _normalize_selection_rows(
    stored: Any,
    selection_mode: str,
) -> list[int]:
    """Normalize frontend selection payload to a sorted list of row positions."""
    raw = stored
    if isinstance(stored, dict):
        raw = stored.get("rows", [])

    rows: list[int] = []
    seen: set[int] = set()
    candidates: list[Any]
    if isinstance(raw, str):
        candidates = [part.strip() for part in raw.split(",") if part.strip()]
    elif isinstance(raw, (list, tuple, set)):
        candidates = list(raw)
    else:
        candidates = [raw]

    for item in candidates:
        if isinstance(item, bool):
            continue
        if isinstance(item, int):
            idx = item
        elif isinstance(item, str) and item.isdigit():
            idx = int(item)
        else:
            continue
        if idx < 0 or idx in seen:
            continue
        seen.add(idx)
        rows.append(idx)

    rows.sort()
    if selection_mode == "single-row":
        return rows[:1]
    return rows


def _default_dataframe_window_size() -> int:
    """Window size used by frontend server-side dataframe pagination."""
    try:
        value = int(os.environ.get("FASTLIT_DF_WINDOW_SIZE", "300"))
    except ValueError:
        value = 300
    return max(50, min(value, 5000))


def _editor_allows_truncation() -> bool:
    raw = os.environ.get("FASTLIT_ALLOW_TRUNCATED_EDITOR", "0")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_width(
    width: int | str,
    use_container_width: bool | None,
) -> tuple[int | str, bool]:
    if use_container_width is True:
        return "stretch", True
    if use_container_width is False and width == "stretch":
        return "content", False
    width_value = width
    use_container_width_value = width_value == "stretch"
    return width_value, use_container_width_value


def _serialize_column_config(column_config: dict | None) -> dict[str, Any] | None:
    if not column_config:
        return None
    return {
        str(key): value.to_dict() if hasattr(value, "to_dict") else value
        for key, value in column_config.items()
    }


def _invoke_callback(
    callback: Callable | None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> None:
    if callback is None:
        return
    callback(*args, **kwargs)


def data_editor(
    data: Any,
    *,
    width: int | str = "stretch",
    height: int | str = "auto",
    use_container_width: bool | None = None,
    hide_index: bool | None = None,
    column_order: list[str] | None = None,
    column_config: dict | None = None,
    num_rows: str = "fixed",
    disabled: bool | list[str] = False,
    row_height: int | None = None,
    placeholder: str | None = None,
    toolbar: bool = True,
    downloadable: bool = True,
    persist_view: bool = True,
    key: str | None = None,
    on_change: Callable | None = None,
    args: list | tuple | None = None,
    kwargs: dict | None = None,
) -> Any:
    """Display an editable DataFrame.

    Args:
        data: A pandas DataFrame, dict, list, or other tabular data.
        width: "stretch" (default), "content", or a fixed pixel width.
        height: "auto" (default), "content", or a fixed pixel height.
        use_container_width: Legacy alias for width="stretch".
        hide_index: If True, hides the row index column.
        column_order: List of column names in display order.
        column_config: Dict of column configurations.
        num_rows: "fixed" or "dynamic" (allow adding/deleting rows).
        disabled: If True, all columns disabled. If list, those columns disabled.
        row_height: Fixed row height in pixels.
        placeholder: Placeholder text when the dataset is empty.
        toolbar: If True, show the grid toolbar.
        downloadable: If True, allow exporting the current edited view as CSV.
        persist_view: If True, persist the editor view state in sessionStorage.
        key: Optional key for stable identity.
        on_change: Callback when data changes.
        args: Positional arguments passed to on_change.
        kwargs: Keyword arguments passed to on_change.

    Returns:
        The edited DataFrame (or original data type).
    """
    from fastlit.runtime.context import get_current_session

    session = get_current_session()
    hide_index_value = bool(hide_index)
    rerun_on_change = True
    width_value, use_container_width_value = _resolve_width(width, use_container_width)
    callback_args = tuple(args or ())
    callback_kwargs = dict(kwargs or {})

    # Convert data to serializable format
    columns, rows, index = _serialize_dataframe(data, hide_index_value)
    total_rows = len(rows)
    max_rows_cap = _default_max_dataframe_rows()
    editor_allows_truncation = _editor_allows_truncation()
    rows, index, truncated = _truncate_rows(rows, index, max_rows_cap)
    if truncated and not editor_allows_truncation:
        raise ValueError(
            "st.data_editor received more rows than the editable limit allows. "
            f"Detected {total_rows} rows, limit is {max_rows_cap}. "
            "Set FASTLIT_ALLOW_TRUNCATED_EDITOR=1 to allow explicit truncation."
        )

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
        "width": width_value,
        "useContainerWidth": use_container_width_value,
        "editable": True,
        "numRows": num_rows,
        "disabledColumns": disabled_cols,
        "rerunOnChange": rerun_on_change,
        "rowHeight": row_height,
        "placeholder": placeholder,
        "toolbar": toolbar,
        "downloadable": downloadable,
        "persistView": persist_view,
        "totalRows": total_rows,
        "truncated": truncated,
    }

    normalized_column_order = _normalize_column_order(columns, column_order)
    if normalized_column_order:
        props["columnOrder"] = normalized_column_order

    if not hide_index_value and index is not None:
        props["index"] = index

    if column_config:
        props["columnConfig"] = _serialize_column_config(column_config)

    node = _emit_node(
        "data_editor",
        props,
        key=key,
        is_widget=True,
        no_rerun=not rerun_on_change,
    )
    session._force_full_render_widget_ids.add(node.id)

    # Get edited data from widget store
    stored = session.widget_store.get(node.id)

    if stored is not None:
        stored_rows, stored_index = _extract_editor_payload(
            stored,
            fallback_rows=rows,
            fallback_index=index,
            hide_index=hide_index_value,
        )
        node.props["rows"] = stored_rows
        node.props["totalRows"] = len(stored_rows)
        node.props["truncated"] = False
        if not hide_index_value and stored_index is not None:
            node.props["index"] = stored_index
        # Call on_change callback when data changed (A3: was silently ignored before)
        if on_change is not None:
            prev_key = f"_de_prev_{node.id}"
            if prev_key not in session.widget_store:
                # Seed baseline without firing callback on first render.
                session.widget_store[prev_key] = stored
            elif session.widget_store.get(prev_key) != stored:
                session.widget_store[prev_key] = stored
                _invoke_callback(on_change, callback_args, callback_kwargs)
        # Return edited data in original format
        return _deserialize_to_original(
            stored,
            data,
            columns=columns,
            fallback_index=index,
            hide_index=hide_index_value,
        )

    return data


def _normalize_column_order(
    columns: list[dict[str, Any]],
    column_order: list[str] | None,
) -> list[str] | None:
    """Return a normalized display order without dropping unspecified columns."""
    if not column_order:
        return None

    available = [str(col.get("name", "")) for col in columns]
    seen: set[str] = set()
    ordered: list[str] = []
    for name in column_order:
        if name in available and name not in seen:
            ordered.append(name)
            seen.add(name)

    for name in available:
        if name not in seen:
            ordered.append(name)

    return ordered or None


def _extract_editor_payload(
    stored: Any,
    *,
    fallback_rows: list[list[Any]],
    fallback_index: list[Any] | None,
    hide_index: bool,
) -> tuple[list[list[Any]], list[Any] | None]:
    """Normalize data_editor widget payloads from old and new frontend versions."""
    if isinstance(stored, dict):
        rows = stored.get("rows", fallback_rows)
        index = stored.get("index", fallback_index)
    else:
        rows = stored
        index = fallback_index

    normalized_rows = rows if isinstance(rows, list) else fallback_rows
    normalized_index = None if hide_index else (
        index if isinstance(index, list) else fallback_index
    )
    return normalized_rows, normalized_index


def _deserialize_to_original(
    stored: Any,
    original: Any,
    *,
    columns: list[dict[str, Any]],
    fallback_index: list[Any] | None,
    hide_index: bool,
) -> Any:
    """Convert stored edited data back to the original input shape."""
    edited_rows, edited_index = _extract_editor_payload(
        stored,
        fallback_rows=[],
        fallback_index=fallback_index,
        hide_index=hide_index,
    )
    col_names = [c["name"] for c in columns]

    try:
        import pandas as pd

        if isinstance(original, pd.DataFrame):
            edited_df = pd.DataFrame(edited_rows, columns=col_names)
            edited_df = _restore_pandas_dtypes(edited_df, original)
            if not hide_index:
                edited_df.index = _restore_index_values(
                    edited_index,
                    original.index.tolist(),
                    len(edited_df),
                )
            return edited_df
    except ImportError:
        pass

    if isinstance(original, dict):
        return {
            name: [row[idx] if idx < len(row) else None for row in edited_rows]
            for idx, name in enumerate(col_names)
        }

    if isinstance(original, list) and original and isinstance(original[0], dict):
        return [dict(zip(col_names, row)) for row in edited_rows]

    if isinstance(original, list):
        return [list(row) for row in edited_rows]

    return [dict(zip(col_names, row)) for row in edited_rows]


def _restore_pandas_dtypes(edited_df: Any, original_df: Any) -> Any:
    """Best-effort dtype restoration for edited pandas DataFrames."""
    try:
        import pandas as pd
        from pandas.api.types import (
            is_bool_dtype,
            is_datetime64_any_dtype,
            is_float_dtype,
            is_integer_dtype,
        )
    except ImportError:
        return edited_df

    for col_name in original_df.columns:
        if col_name not in edited_df.columns:
            continue
        source = original_df[col_name]
        target = edited_df[col_name]

        try:
            if is_bool_dtype(source.dtype):
                edited_df[col_name] = target.map(_coerce_bool_value)
                continue

            if is_integer_dtype(source.dtype):
                numeric = pd.to_numeric(target, errors="coerce")
                if numeric.isna().any():
                    edited_df[col_name] = numeric.astype("Int64")
                else:
                    edited_df[col_name] = numeric.astype(source.dtype)
                continue

            if is_float_dtype(source.dtype):
                edited_df[col_name] = pd.to_numeric(target, errors="coerce").astype(source.dtype)
                continue

            if is_datetime64_any_dtype(source.dtype):
                edited_df[col_name] = pd.to_datetime(target, errors="coerce")
                continue

            if str(source.dtype) == "category":
                edited_df[col_name] = target.astype("category")
        except Exception:
            edited_df[col_name] = target

    return edited_df


def _coerce_bool_value(value: Any) -> Any:
    """Normalize mixed frontend values to booleans when possible."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off", ""}:
            return False
    return bool(value)


def _restore_index_values(
    edited_index: list[Any] | None,
    original_index: list[Any],
    row_count: int,
) -> list[Any]:
    """Best-effort restoration of edited index values."""
    if isinstance(edited_index, list) and len(edited_index) == row_count:
        return edited_index
    if len(original_index) == row_count:
        return original_index
    return list(range(row_count))


def table(
    data: Any,
    *,
    width: int | str = "stretch",
    height: int | str = "auto",
    placeholder: str | None = None,
    row_height: int | None = None,
    key: str | None = None,
) -> None:
    """Display a static table (no virtualization, for small data).

    Args:
        data: A pandas DataFrame, dict, list, or other tabular data.
        width: "stretch" (default), "content", or a fixed pixel width.
        height: "auto" (default), "content", or a fixed pixel height.
        placeholder: Placeholder text when the table is empty.
        row_height: Fixed row height in pixels.
        key: Optional key for stable identity.
    """
    columns, rows, index = _serialize_dataframe(data, hide_index=True)
    total_rows = len(rows)
    rows, _, truncated = _truncate_rows(rows, None, _default_max_dataframe_rows())

    props = {
        "columns": columns,
        "rows": rows,
        "static": True,
        "width": width,
        "height": height,
        "placeholder": placeholder,
        "rowHeight": row_height,
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

    column_names = [str(col.get("name", "")) for col in columns]

    # Pandas path: keep raw dataframe server-side and query lazily.
    try:
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            positioned = data.copy()
            positioned["__fastlit_position__"] = list(range(len(data)))

            def query_fn(query):
                view = _query_pandas_dataframe(
                    positioned,
                    columns=columns,
                    search=query.search,
                    sorts=query.sorts,
                    filters=query.filters,
                )
                safe_offset = max(0, min(query.offset, len(view)))
                safe_end = min(len(view), safe_offset + query.limit)
                sliced = view.iloc[safe_offset:safe_end]
                out_rows = [
                    [_to_json_safe(v) for v in row]
                    for row in sliced[[str(col.get("name", "")) for col in columns]].itertuples(index=False, name=None)
                ]
                out_index = None if hide_index else [_to_json_safe(v) for v in sliced.index.tolist()]
                out_positions = [_to_json_safe(v) for v in sliced["__fastlit_position__"].tolist()]
                return {
                    "offset": safe_offset,
                    "limit": query.limit,
                    "totalRows": len(view),
                    "rows": out_rows,
                    "index": out_index,
                    "positions": out_positions,
                    "columns": columns,
                }

            return register_source(
                columns=columns,
                rows=None,
                index=None,
                slice_fn=None,
                total_rows=total_rows,
                query_fn=query_fn,
                schema_version=_schema_version(columns),
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

    def generic_query_fn(query):
        queried_rows, queried_index, queried_positions = _query_materialized_rows(
            columns=columns,
            rows=full_rows,
            index_values=full_index,
            search=query.search,
            sorts=query.sorts,
            filters=query.filters,
        )
        safe_offset = max(0, min(query.offset, len(queried_rows)))
        safe_end = min(len(queried_rows), safe_offset + query.limit)
        return {
            "offset": safe_offset,
            "limit": query.limit,
            "totalRows": len(queried_rows),
            "rows": queried_rows[safe_offset:safe_end],
            "index": None if queried_index is None else queried_index[safe_offset:safe_end],
            "positions": queried_positions[safe_offset:safe_end],
            "columns": columns,
        }

    return register_source(
        columns=columns,
        rows=full_rows,
        index=full_index,
        total_rows=total_rows,
        query_fn=generic_query_fn,
        schema_version=_schema_version(columns),
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
            return [_to_json_safe(item) for item in value.tolist()]
        if isinstance(value, np.bool_):
            return bool(value)
    except ImportError:
        pass

    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(item) for item in value]

    # Handle datetime
    if hasattr(value, "isoformat"):
        return value.isoformat()

    # Check if already JSON-safe
    if isinstance(value, (str, int, float, bool)):
        return value

    # Fallback to string
    return str(value)


def _schema_version(columns: list[dict[str, Any]]) -> str:
    return json.dumps(
        [
            {
                "name": str(col.get("name", "")),
                "type": str(col.get("type", "")),
            }
            for col in columns
        ],
        sort_keys=True,
        separators=(",", ":"),
    )


def _query_pandas_dataframe(
    df: Any,
    *,
    columns: list[dict[str, Any]],
    search: str,
    sorts: tuple[Any, ...],
    filters: tuple[Any, ...],
) -> Any:
    try:
        import pandas as pd
    except ImportError:
        return df

    view = df
    column_names = [str(col.get("name", "")) for col in columns if str(col.get("name", ""))]
    search_value = (search or "").strip()
    if search_value:
        mask = pd.Series(False, index=view.index)
        lowered_search = search_value.lower()
        for col in column_names:
            if col not in view.columns:
                continue
            series = view[col]
            mask = mask | series.map(
                lambda value: lowered_search in _searchable_text(value)
            )
        view = view[mask]

    for flt in filters:
        column_name = getattr(flt, "column", None)
        op = getattr(flt, "op", "")
        if not column_name or column_name not in view.columns:
            continue
        series = view[column_name]
        mask = series.map(lambda value: _matches_filter(value, op, getattr(flt, "value", None)))
        view = view[mask]

    if sorts:
        by: list[str] = []
        ascending: list[bool] = []
        for sort in sorts:
            column_name = getattr(sort, "column", None)
            direction = getattr(sort, "direction", "asc")
            if not column_name or column_name not in view.columns:
                continue
            by.append(column_name)
            ascending.append(direction != "desc")
        if by:
            try:
                view = view.sort_values(by=by, ascending=ascending, kind="stable")
            except TypeError:
                sort_keys = [
                    view[column].map(lambda value: _sort_key(value))
                    for column in by
                ]
                temp_df = view.assign(**{f"__fastlit_sort_{idx}": sort_keys[idx] for idx in range(len(by))})
                temp_names = [f"__fastlit_sort_{idx}" for idx in range(len(by))]
                temp_df = temp_df.sort_values(by=temp_names, ascending=ascending, kind="stable")
                view = temp_df.drop(columns=temp_names)
    return view


def _query_materialized_rows(
    *,
    columns: list[dict[str, Any]],
    rows: list[list[Any]],
    index_values: list[Any] | None,
    search: str,
    sorts: tuple[Any, ...],
    filters: tuple[Any, ...],
) -> tuple[list[list[Any]], list[Any] | None, list[int]]:
    column_names = [str(col.get("name", "")) for col in columns]
    items: list[tuple[int, list[Any], Any]] = []
    for row_idx, row in enumerate(rows):
        idx_value = index_values[row_idx] if index_values is not None and row_idx < len(index_values) else None
        items.append((row_idx, row, idx_value))

    search_value = (search or "").strip().lower()
    if search_value:
        items = [
            item
            for item in items
            if any(search_value in _searchable_text(value) for value in item[1])
        ]

    if filters:
        next_items: list[tuple[int, list[Any], Any]] = []
        for item in items:
            row_map = {
                column_names[idx]: item[1][idx] if idx < len(item[1]) else None
                for idx in range(len(column_names))
            }
            if all(
                _matches_filter(row_map.get(getattr(flt, "column", "")), getattr(flt, "op", ""), getattr(flt, "value", None))
                for flt in filters
                if getattr(flt, "column", "")
            ):
                next_items.append(item)
        items = next_items

    if sorts:
        for sort in reversed(sorts):
            column_name = getattr(sort, "column", "")
            if column_name not in column_names:
                continue
            column_idx = column_names.index(column_name)
            reverse = getattr(sort, "direction", "asc") == "desc"
            items.sort(
                key=lambda item: _sort_key(item[1][column_idx] if column_idx < len(item[1]) else None),
                reverse=reverse,
            )

    queried_rows = [item[1] for item in items]
    queried_index = [item[2] for item in items] if index_values is not None else None
    queried_positions = [int(item[0]) for item in items]
    return queried_rows, queried_index, queried_positions


def _searchable_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, (int, float, bool)):
        return str(value).lower()
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    if isinstance(value, (list, tuple, set)):
        return " ".join(_searchable_text(item) for item in value)
    return str(value).lower()


def _sort_key(value: Any) -> tuple[int, Any]:
    if value is None:
        return (1, "")
    if isinstance(value, bool):
        return (0, int(value))
    if isinstance(value, (int, float)):
        return (0, value)
    if isinstance(value, str):
        return (0, value.lower())
    if isinstance(value, (list, tuple, set)):
        return (0, json.dumps([_to_json_safe(item) for item in value], ensure_ascii=False))
    if isinstance(value, dict):
        return (0, json.dumps(_to_json_safe(value), ensure_ascii=False, sort_keys=True))
    return (0, str(value).lower())


def _matches_filter(value: Any, op: str, filter_value: Any) -> bool:
    if op == "":
        return True
    if op == "is_empty":
        return _is_empty_value(value)
    if op == "not_empty":
        return not _is_empty_value(value)
    if op == "is_true":
        return value is True
    if op == "is_false":
        return value is False

    if op in {"contains", "not_contains", "equals", "not_equals"}:
        haystack = _searchable_text(value)
        needle = _searchable_text(filter_value)
        if op == "contains":
            return needle in haystack
        if op == "not_contains":
            return needle not in haystack
        if op == "equals":
            return haystack == needle
        return haystack != needle

    if op in {"gt", "gte", "lt", "lte"}:
        numeric = _coerce_number(value)
        if numeric is None:
            return False
        rhs = _coerce_number(filter_value)
        if rhs is None:
            return True
        if op == "gt":
            return numeric > rhs
        if op == "gte":
            return numeric >= rhs
        if op == "lt":
            return numeric < rhs
        return numeric <= rhs

    if op == "between":
        if isinstance(filter_value, (list, tuple)) and len(filter_value) == 2:
            numeric = _coerce_number(value)
            low_number = _coerce_number(filter_value[0])
            high_number = _coerce_number(filter_value[1])
            if numeric is not None and low_number is not None and high_number is not None:
                return low_number <= numeric <= high_number
            lhs = _coerce_datetime(value)
            low = _coerce_datetime(filter_value[0])
            high = _coerce_datetime(filter_value[1])
            if lhs is not None and low is not None and high is not None:
                return low <= lhs <= high
        return True

    if op in {"before", "on_or_before", "after", "on_or_after"}:
        lhs = _coerce_datetime(value)
        rhs = _coerce_datetime(filter_value)
        if lhs is None or rhs is None:
            return False
        if op == "before":
            return lhs < rhs
        if op == "on_or_before":
            return lhs <= rhs
        if op == "after":
            return lhs > rhs
        return lhs >= rhs

    if op == "contains_any":
        items = _normalize_list_like(value)
        filter_items = _normalize_list_like(filter_value)
        return any(item in items for item in filter_items)

    if op == "contains_all":
        items = _normalize_list_like(value)
        filter_items = _normalize_list_like(filter_value)
        return all(item in items for item in filter_items)

    return True


def _normalize_list_like(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        if raw.startswith("[") and raw.endswith("]"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in raw.split(",") if item.strip()]
    return [value]


def _coerce_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _coerce_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        try:
            return str(value.isoformat())
        except Exception:
            return None
    if isinstance(value, str):
        raw = value.strip()
        return raw or None
    return str(value)


def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False
