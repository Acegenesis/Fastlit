from decimal import Decimal

from fastlit.runtime.dataframe_arrow import serialize_arrow_frame
from fastlit.runtime.tree import UINode
from fastlit.server.dataframe_store import DataframeFilter, DataframeQuery, DataframeSort
from fastlit.ui.column_config import (
    AreaChartColumn,
    BarChartColumn,
    CheckboxColumn,
    DateColumn,
    DatetimeColumn,
    ImageColumn,
    JSONColumn,
    LinkColumn,
    MultiselectColumn,
    NumberColumn,
    ProgressColumn,
    SelectboxColumn,
    TextColumn,
    TimeColumn,
)
from fastlit.ui.dataframe import (
    DataEditorChangeSet,
    DataframeQueryResult,
    DataframeElement,
    _deserialize_to_original,
    _extract_editor_changes,
    _normalize_on_query_result,
    _normalize_column_order,
    _normalize_selection_state,
    _query_result_preview_to_serialized,
    _query_materialized_rows,
    _serialize_column_config,
    _serialize_dataframe,
)
from fastlit.ui.text import _format_metric_value, _json_safe_value, _normalize_json_expansion, _normalize_metric_chart_data


def test_column_config_v2_serialization() -> None:
    multi = MultiselectColumn(
        "Tags",
        options=["ops", "viewer"],
        resizable=True,
        min_width=140,
        max_width=320,
        pinned="left",
    ).to_dict()
    assert multi["type"] == "multiselect"
    assert multi["options"] == ["ops", "viewer"]
    assert multi["resizable"] is True
    assert multi["minWidth"] == 140
    assert multi["maxWidth"] == 320
    assert multi["pinned"] == "left"

    json_col = JSONColumn("Payload").to_dict()
    assert json_col["type"] == "json"

    area = AreaChartColumn("Trend", y_min=0, y_max=10).to_dict()
    assert area["type"] == "area_chart"
    assert area["yMin"] == 0
    assert area["yMax"] == 10


def test_column_config_serialization_supports_editor_column_types() -> None:
    assert TextColumn("Name", max_chars=80, validate=r"^[A-Z]").to_dict()["type"] == "text"
    assert NumberColumn("Score", min_value=0, max_value=100, step=0.5).to_dict()["type"] == "number"
    assert CheckboxColumn("Active").to_dict()["type"] == "checkbox"
    assert SelectboxColumn("Role", options=["admin", "user"]).to_dict()["options"] == ["admin", "user"]
    assert DateColumn("Joined", format="YYYY-MM-DD").to_dict()["type"] == "date"
    assert TimeColumn("Focus", format="HH:mm", step=60).to_dict()["type"] == "time"
    assert DatetimeColumn("Reminder", format="YYYY-MM-DD HH:mm").to_dict()["type"] == "datetime"
    assert ProgressColumn("Progress", min_value=0, max_value=100).to_dict()["type"] == "progress"
    assert LinkColumn("Website", display_text="Open").to_dict()["type"] == "link"
    assert ImageColumn("Avatar").to_dict()["type"] == "image"
    assert BarChartColumn("Bars", y_min=0, y_max=10).to_dict()["type"] == "bar_chart"


def test_query_materialized_rows_applies_search_sort_and_filters() -> None:
    columns = [
        {"name": "Name", "type": "text"},
        {"name": "Score", "type": "number"},
        {"name": "Active", "type": "checkbox"},
        {"name": "Tags", "type": "list"},
    ]
    rows = [
        ["Alice", 91, True, ["ops", "admin"]],
        ["Bob", 77, False, ["sales"]],
        ["Charlie", 95, True, ["ml", "viz"]],
        ["Diana", 88, True, ["viewer", "beta"]],
    ]
    query = DataframeQuery(
        offset=0,
        limit=10,
        search="a",
        sorts=[DataframeSort(column="Score", direction="desc")],
        filters=[
            DataframeFilter(column="Active", op="is_true", value=None),
            DataframeFilter(column="Tags", op="contains_any", value=["beta", "viz"]),
        ],
    )

    queried_rows, queried_index, queried_positions = _query_materialized_rows(
        columns=columns,
        rows=rows,
        index_values=None,
        search=query.search,
        sorts=tuple(query.sorts),
        filters=tuple(query.filters),
    )

    assert queried_index is None
    assert queried_positions == [2, 3]
    assert [row[0] for row in queried_rows] == ["Charlie", "Diana"]


def test_deserialize_to_original_dict_preserves_mapping_shape() -> None:
    original = {"Name": ["Alice"], "Score": [91]}
    columns = [{"name": "Name"}, {"name": "Score"}]
    stored = {"rows": [["Alice", 99]]}

    restored = _deserialize_to_original(
        stored,
        original,
        columns=columns,
        fallback_index=None,
        hide_index=True,
    )

    assert restored == {"Name": ["Alice"], "Score": [99]}


def test_normalize_column_order_preserves_omitted_columns() -> None:
    columns = [
        {"name": "Name"},
        {"name": "Age"},
        {"name": "City"},
    ]

    ordered = _normalize_column_order(columns, ["City", "Name"])

    assert ordered == ["City", "Name"]


def test_serialize_column_config_supports_numeric_and_index_keys() -> None:
    columns = [
        {"name": "Name", "_sourceKey": "Name"},
        {"name": "Age", "_sourceKey": "Age"},
    ]

    serialized, index_config = _serialize_column_config(
        {
            1: MultiselectColumn("Age override", options=["x"]).to_dict(),
            "_index": {"label": "Row id", "hidden": True},
        },
        columns=columns,
        index_names=["id"],
    )

    assert serialized == {
        "Age": {
            "type": "multiselect",
            "label": "Age override",
            "width": None,
            "resizable": False,
            "minWidth": None,
            "maxWidth": None,
            "pinned": None,
            "help": None,
            "disabled": False,
            "required": False,
            "default": None,
            "hidden": False,
            "validateMessage": None,
            "validateOn": None,
            "options": ["x"],
        }
    }
    assert index_config["label"] == "Row id"
    assert index_config["hidden"] is True


def test_normalize_selection_state_supports_rows_columns_and_cells() -> None:
    selection = _normalize_selection_state(
        {
            "selection": {
                "rows": [3, 1, 3],
                "columns": ["Score", "Name", "Score"],
                "cells": [
                    {"row": 1, "column": "Name"},
                    {"row": 1, "column": "Name"},
                    {"row": 3, "column": "Score"},
                ],
            }
        },
        ("multi-row", "multi-column", "multi-cell"),
    )

    assert selection.rows == [1, 3]
    assert selection.columns == ["Score", "Name"]
    assert selection.cells == [(1, "Name"), (3, "Score")]


def test_dataframe_element_add_rows_extends_serialized_rows() -> None:
    columns, rows, index = _serialize_dataframe({"Name": ["Alice"]}, hide_index=False)
    node = UINode(
        type="dataframe",
        id="k:test_df",
        props={
            "columns": columns,
            "rows": rows,
            "index": index,
            "totalRows": 1,
        },
    )
    element = DataframeElement(node=node, hide_index=False)

    element.add_rows({"Name": ["Bob", "Charlie"]})

    assert node.props["rows"] == [["Alice"], ["Bob"], ["Charlie"]]
    assert node.props["index"] == [0, 0, 1]
    assert node.props["totalRows"] == 3


def test_serialize_dataframe_supports_to_pandas_protocol() -> None:
    try:
        import pandas as pd
    except ImportError:
        return

    class FakeFrame:
        def to_pandas(self):
            return pd.DataFrame({"Name": ["Alice"], "Score": [99]})

    columns, rows, index = _serialize_dataframe(FakeFrame(), hide_index=False)

    assert [column["name"] for column in columns] == ["Name", "Score"]
    assert rows == [["Alice", 99]]
    assert index == [0]


def test_serialize_arrow_frame_round_trip() -> None:
    try:
        import pyarrow as pa
        import pyarrow.ipc as ipc
    except ImportError:
        return

    payload = serialize_arrow_frame(
        columns=[
            {"name": "Name", "type": "string"},
            {"name": "Score", "type": "number"},
        ],
        rows=[["Alice", 91], ["Bob", 77]],
        index=["row-1", "row-2"],
        positions=[10, 11],
    )

    assert payload is not None

    reader = ipc.open_stream(pa.py_buffer(payload))
    table = reader.read_all()

    assert table.column("Name").to_pylist() == ["Alice", "Bob"]
    assert table.column("Score").to_pylist() == [91, 77]
    assert table.column("__fastlit_index__").to_pylist() == ["row-1", "row-2"]
    assert table.column("__fastlit_position__").to_pylist() == [10, 11]


def test_metric_helpers_format_and_normalize_chart_data() -> None:
    assert _format_metric_value(1234.5, "$,.1f") == "$1,234.5"
    assert _format_metric_value(12.5, "%.1f%%") == "12.5%"
    assert _normalize_metric_chart_data({"a": 1, "b": "skip", "c": 2.5}) == [1.0, 2.5]


def test_metric_named_formats_and_none_value() -> None:
    assert _format_metric_value(None, None) == "\u2014"
    assert _format_metric_value(1234.567, "localized") == "1,234.567"
    assert _format_metric_value(12.345, "percent") == "1,234.50%"
    assert _format_metric_value(1234.567, "dollar") == "$1,234.57"
    assert _format_metric_value(1536, "bytes") == "1.5KB"
    assert _format_metric_value(1250000, "compact") == "1.2M"


def test_metric_chart_data_supports_dataframe_like_protocol() -> None:
    try:
        import pandas as pd
    except ImportError:
        return

    class FakeChartFrame:
        def to_pandas(self):
            return pd.DataFrame({"primary": [1, 2, 3], "secondary": [4, 5, 6]})

    assert _normalize_metric_chart_data(FakeChartFrame()) == [1.0, 2.0, 3.0]


def test_json_expansion_and_safe_value_support_decimal() -> None:
    assert _normalize_json_expansion(True) is True
    assert _normalize_json_expansion(False) is False
    assert _normalize_json_expansion(0) is False
    assert _normalize_json_expansion(2) == 2
    assert _json_safe_value({"price": Decimal("12.50")}) == {"price": 12.5}


def test_normalize_on_query_result_accepts_dict_payloads() -> None:
    result = _normalize_on_query_result(
        {
            "rows": [(1, "Alice")],
            "totalRows": 10,
            "index": ["row-1"],
            "positions": [4],
            "columns": [{"name": "id", "type": "number"}, {"name": "name", "type": "text"}],
            "schemaVersion": "v1",
            "diagnostics": {"source": "manual"},
        }
    )

    assert isinstance(result, DataframeQueryResult)
    assert result.rows == [[1, "Alice"]]
    assert result.total_rows == 10
    assert result.index == ["row-1"]
    assert result.positions == [4]
    assert result.schema_version == "v1"
    assert result.diagnostics == {"source": "manual"}


def test_query_result_preview_can_build_columns_from_rows() -> None:
    result = DataframeQueryResult(
        rows=[[1, "Alice"]],
        total_rows=1,
        columns=None,
    )

    columns, rows, index, total_rows, truncated = _query_result_preview_to_serialized(
        result,
        data=None,
        hide_index=False,
        column_config=None,
    )

    assert [column["name"] for column in columns] == ["Column 1", "Column 2"]
    assert rows == [[1, "Alice"]]
    assert index == [0]
    assert total_rows == 1
    assert truncated is False


def test_extract_editor_changes_returns_structured_payload() -> None:
    changes = _extract_editor_changes(
        {
            "rows": [["Alice", 42]],
            "changes": {
                "addedRows": [{"name": "Bob"}],
                "editedCells": [
                    {"rowId": "0", "column": "Score", "before": 1, "after": 2},
                ],
                "deletedRows": [{"name": "Cara"}],
            },
        },
    )

    assert isinstance(changes, DataEditorChangeSet)
    assert changes.added_rows == [{"name": "Bob"}]
    assert len(changes.edited_cells) == 1
    assert changes.edited_cells[0].row_id == "0"
    assert changes.edited_cells[0].column == "Score"
    assert changes.deleted_rows == [{"name": "Cara"}]
