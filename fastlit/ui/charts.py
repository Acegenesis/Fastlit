"""Chart display functions for Fastlit.

Provides Streamlit-compatible chart functions:
- st.line_chart, st.bar_chart, st.area_chart, st.scatter_chart
- st.map
- st.plotly_chart, st.altair_chart, st.vega_lite_chart
- st.pyplot, st.bokeh_chart, st.graphviz_chart, st.pydeck_chart
"""

from __future__ import annotations

from typing import Any, Sequence, TYPE_CHECKING

from fastlit.ui.base import _emit_node

if TYPE_CHECKING:
    import pandas as pd


def _prepare_chart_data(
    data: Any,
    *,
    x: str | None = None,
    y: str | Sequence[str] | None = None,
    color: str | None = None,
) -> dict:
    """Convert data to chart-ready format.

    Returns dict with:
    - data: list of {x, y, series?} records
    - xKey: x axis key name
    - yKeys: list of y axis key names
    - series: list of series names (for multi-line)
    """
    # Handle pandas DataFrame
    try:
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            return _prepare_pandas_chart(data, x=x, y=y, color=color)
    except ImportError:
        pass

    # Handle dict of lists (column-oriented)
    if isinstance(data, dict):
        return _prepare_dict_chart(data, x=x, y=y)

    # Handle list of dicts
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return _prepare_list_chart(data, x=x, y=y)

    # Handle simple list (single series)
    if isinstance(data, (list, tuple)):
        return {
            "data": [{"x": i, "y": v} for i, v in enumerate(data)],
            "xKey": "x",
            "yKeys": ["y"],
        }

    return {"data": [], "xKey": "x", "yKeys": ["y"]}


def _prepare_pandas_chart(
    df: "pd.DataFrame",
    *,
    x: str | None = None,
    y: str | Sequence[str] | None = None,
    color: str | None = None,
) -> dict:
    """Prepare pandas DataFrame for charting."""
    import pandas as pd  # noqa: F811 - runtime import after TYPE_CHECKING

    # Determine x column
    if x is None:
        # Use index as x
        x_values = df.index.tolist()
        x_key = "index"
    else:
        x_values = df[x].tolist()
        x_key = x

    # Determine y columns
    if y is None:
        # Use all numeric columns
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if x in numeric_cols:
            numeric_cols.remove(x)
        y_cols = numeric_cols if numeric_cols else df.columns.tolist()[:1]
    elif isinstance(y, str):
        y_cols = [y]
    else:
        y_cols = list(y)

    # Build data records
    records = []
    for i, x_val in enumerate(x_values):
        record = {x_key: _to_chart_value(x_val)}
        for col in y_cols:
            record[col] = _to_chart_value(df[col].iloc[i])
        records.append(record)

    return {
        "data": records,
        "xKey": x_key,
        "yKeys": y_cols,
    }


def _prepare_dict_chart(
    data: dict,
    *,
    x: str | None = None,
    y: str | Sequence[str] | None = None,
) -> dict:
    """Prepare dict of lists for charting."""
    keys = list(data.keys())
    if not keys:
        return {"data": [], "xKey": "x", "yKeys": ["y"]}

    # Determine x key
    x_key = x if x else keys[0]
    x_values = data.get(x_key, list(range(len(next(iter(data.values()))))))

    # Determine y keys
    if y is None:
        y_cols = [k for k in keys if k != x_key]
    elif isinstance(y, str):
        y_cols = [y]
    else:
        y_cols = list(y)

    if not y_cols:
        y_cols = keys[:1]

    # Build records
    records = []
    for i, x_val in enumerate(x_values if isinstance(x_values, list) else [x_values]):
        record = {x_key: _to_chart_value(x_val)}
        for col in y_cols:
            vals = data.get(col, [])
            record[col] = _to_chart_value(vals[i] if i < len(vals) else None)
        records.append(record)

    return {
        "data": records,
        "xKey": x_key,
        "yKeys": y_cols,
    }


def _prepare_list_chart(
    data: list[dict],
    *,
    x: str | None = None,
    y: str | Sequence[str] | None = None,
) -> dict:
    """Prepare list of dicts for charting."""
    if not data:
        return {"data": [], "xKey": "x", "yKeys": ["y"]}

    keys = list(data[0].keys())

    # Determine x key
    x_key = x if x else keys[0]

    # Determine y keys
    if y is None:
        y_cols = [k for k in keys if k != x_key]
    elif isinstance(y, str):
        y_cols = [y]
    else:
        y_cols = list(y)

    if not y_cols:
        y_cols = keys[:1]

    # Convert records
    records = []
    for row in data:
        record = {x_key: _to_chart_value(row.get(x_key))}
        for col in y_cols:
            record[col] = _to_chart_value(row.get(col))
        records.append(record)

    return {
        "data": records,
        "xKey": x_key,
        "yKeys": y_cols,
    }


def _to_chart_value(value: Any) -> Any:
    """Convert value to chart-safe type."""
    if value is None:
        return None

    # Handle pandas NA
    try:
        import pandas as pd

        if pd.isna(value):
            return None
    except (ImportError, TypeError):
        pass

    # Handle numpy types
    try:
        import numpy as np

        if isinstance(value, (np.integer, np.floating)):
            return value.item()
    except ImportError:
        pass

    # Handle datetime
    if hasattr(value, "isoformat"):
        return value.isoformat()

    if isinstance(value, (int, float, str, bool)):
        return value

    return str(value)


# ---------------------------------------------------------------------------
# Simple Charts (Recharts-based)
# ---------------------------------------------------------------------------


def line_chart(
    data: Any,
    *,
    x: str | None = None,
    y: str | Sequence[str] | None = None,
    color: str | Sequence[str] | None = None,
    width: int | None = None,
    height: int | None = None,
    use_container_width: bool = True,
) -> None:
    """Display a line chart.

    Args:
        data: DataFrame, dict, or list of values.
        x: Column name for x-axis. If None, uses index.
        y: Column name(s) for y-axis. If None, uses all numeric columns.
        color: Color(s) for the lines.
        width: Chart width in pixels.
        height: Chart height in pixels (default 300).
        use_container_width: If True, use full container width.
    """
    chart_data = _prepare_chart_data(data, x=x, y=y)
    colors = _normalize_colors(color, len(chart_data["yKeys"]))

    _emit_node(
        "line_chart",
        {
            **chart_data,
            "colors": colors,
            "width": width,
            "height": height or 300,
            "useContainerWidth": use_container_width,
        },
    )


def bar_chart(
    data: Any,
    *,
    x: str | None = None,
    y: str | Sequence[str] | None = None,
    color: str | Sequence[str] | None = None,
    width: int | None = None,
    height: int | None = None,
    use_container_width: bool = True,
    horizontal: bool = False,
) -> None:
    """Display a bar chart.

    Args:
        data: DataFrame, dict, or list of values.
        x: Column name for x-axis.
        y: Column name(s) for y-axis.
        color: Color(s) for the bars.
        width: Chart width in pixels.
        height: Chart height in pixels (default 300).
        use_container_width: If True, use full container width.
        horizontal: If True, display horizontal bars.
    """
    chart_data = _prepare_chart_data(data, x=x, y=y)
    colors = _normalize_colors(color, len(chart_data["yKeys"]))

    _emit_node(
        "bar_chart",
        {
            **chart_data,
            "colors": colors,
            "width": width,
            "height": height or 300,
            "useContainerWidth": use_container_width,
            "horizontal": horizontal,
        },
    )


def area_chart(
    data: Any,
    *,
    x: str | None = None,
    y: str | Sequence[str] | None = None,
    color: str | Sequence[str] | None = None,
    width: int | None = None,
    height: int | None = None,
    use_container_width: bool = True,
    stack: bool = False,
) -> None:
    """Display an area chart.

    Args:
        data: DataFrame, dict, or list of values.
        x: Column name for x-axis.
        y: Column name(s) for y-axis.
        color: Color(s) for the areas.
        width: Chart width in pixels.
        height: Chart height in pixels (default 300).
        use_container_width: If True, use full container width.
        stack: If True, stack the areas.
    """
    chart_data = _prepare_chart_data(data, x=x, y=y)
    colors = _normalize_colors(color, len(chart_data["yKeys"]))

    _emit_node(
        "area_chart",
        {
            **chart_data,
            "colors": colors,
            "width": width,
            "height": height or 300,
            "useContainerWidth": use_container_width,
            "stack": stack,
        },
    )


def scatter_chart(
    data: Any,
    *,
    x: str | None = None,
    y: str | None = None,
    color: str | None = None,
    size: str | None = None,
    width: int | None = None,
    height: int | None = None,
    use_container_width: bool = True,
) -> None:
    """Display a scatter chart.

    Args:
        data: DataFrame, dict, or list of values.
        x: Column name for x-axis.
        y: Column name for y-axis.
        color: Color for the points or column for color encoding.
        size: Column name for point size.
        width: Chart width in pixels.
        height: Chart height in pixels (default 300).
        use_container_width: If True, use full container width.
    """
    chart_data = _prepare_chart_data(data, x=x, y=y)

    _emit_node(
        "scatter_chart",
        {
            **chart_data,
            "color": color or "#8884d8",
            "sizeKey": size,
            "width": width,
            "height": height or 300,
            "useContainerWidth": use_container_width,
        },
    )


def _normalize_colors(
    color: str | Sequence[str] | None, count: int
) -> list[str]:
    """Normalize color input to list of colors."""
    default_colors = [
        "#8884d8",
        "#82ca9d",
        "#ffc658",
        "#ff7300",
        "#00C49F",
        "#FFBB28",
        "#FF8042",
        "#0088FE",
    ]

    if color is None:
        return default_colors[:count]
    if isinstance(color, str):
        return [color] * count
    return list(color)[:count]


# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------


def map(
    data: Any = None,
    *,
    latitude: str | None = None,
    longitude: str | None = None,
    color: str | None = None,
    size: str | None = None,
    zoom: int | None = None,
    use_container_width: bool = True,
    height: int | None = None,
) -> None:
    """Display a map with points.

    Args:
        data: DataFrame or list with lat/lon columns.
        latitude: Column name for latitude (default: "lat" or "latitude").
        longitude: Column name for longitude (default: "lon" or "longitude").
        color: Color for markers.
        size: Column name for marker size.
        zoom: Initial zoom level.
        use_container_width: If True, use full container width.
        height: Map height in pixels (default 400).
    """
    points = _prepare_map_data(data, latitude=latitude, longitude=longitude)

    _emit_node(
        "map",
        {
            "points": points,
            "color": color or "#FF5733",
            "sizeKey": size,
            "zoom": zoom,
            "height": height or 400,
            "useContainerWidth": use_container_width,
        },
    )


def _prepare_map_data(
    data: Any,
    *,
    latitude: str | None = None,
    longitude: str | None = None,
) -> list[dict]:
    """Convert data to list of {lat, lon} points."""
    if data is None:
        return []

    # Auto-detect lat/lon columns
    lat_col = latitude
    lon_col = longitude

    try:
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            cols = data.columns.tolist()

            if lat_col is None:
                for c in ["lat", "latitude", "LAT", "Latitude"]:
                    if c in cols:
                        lat_col = c
                        break

            if lon_col is None:
                for c in ["lon", "lng", "longitude", "LON", "Longitude"]:
                    if c in cols:
                        lon_col = c
                        break

            if lat_col and lon_col:
                points = []
                for _, row in data.iterrows():
                    lat = row.get(lat_col)
                    lon = row.get(lon_col)
                    if lat is not None and lon is not None:
                        points.append({
                            "lat": float(lat),
                            "lon": float(lon),
                        })
                return points
    except ImportError:
        pass

    # Handle list of dicts
    if isinstance(data, list):
        points = []
        for row in data:
            if isinstance(row, dict):
                lat = row.get(lat_col or "lat") or row.get("latitude")
                lon = row.get(lon_col or "lon") or row.get("longitude") or row.get("lng")
                if lat is not None and lon is not None:
                    points.append({"lat": float(lat), "lon": float(lon)})
        return points

    return []


# ---------------------------------------------------------------------------
# External Library Charts
# ---------------------------------------------------------------------------


def plotly_chart(
    figure_or_data: Any,
    *,
    use_container_width: bool = True,
    theme: str | None = "streamlit",
    key: str | None = None,
) -> None:
    """Display a Plotly chart.

    Args:
        figure_or_data: A Plotly figure or dict/list of traces.
        use_container_width: If True, use full container width.
        theme: Chart theme ("streamlit" or None).
        key: Optional key for stable identity.
    """
    # Convert Plotly figure to JSON
    spec = _plotly_to_spec(figure_or_data)

    _emit_node(
        "plotly_chart",
        {
            "spec": spec,
            "useContainerWidth": use_container_width,
            "theme": theme,
        },
        key=key,
    )


def _plotly_to_spec(figure_or_data: Any) -> dict:
    """Convert Plotly figure to JSON spec."""
    # Handle Plotly Figure object
    if hasattr(figure_or_data, "to_json"):
        import json

        return json.loads(figure_or_data.to_json())

    # Handle dict (already a spec)
    if isinstance(figure_or_data, dict):
        return figure_or_data

    # Handle list of traces
    if isinstance(figure_or_data, list):
        return {"data": figure_or_data, "layout": {}}

    return {"data": [], "layout": {}}


def altair_chart(
    altair_chart: Any,
    *,
    use_container_width: bool = True,
    theme: str | None = "streamlit",
    key: str | None = None,
) -> None:
    """Display an Altair chart.

    Args:
        altair_chart: An Altair chart object.
        use_container_width: If True, use full container width.
        theme: Chart theme.
        key: Optional key.
    """
    # Convert Altair chart to Vega-Lite spec
    spec = _altair_to_spec(altair_chart)

    _emit_node(
        "vega_lite_chart",
        {
            "spec": spec,
            "useContainerWidth": use_container_width,
            "theme": theme,
        },
        key=key,
    )


def vega_lite_chart(
    data: Any = None,
    spec: dict | None = None,
    *,
    use_container_width: bool = True,
    theme: str | None = "streamlit",
    key: str | None = None,
) -> None:
    """Display a Vega-Lite chart.

    Args:
        data: Data for the chart.
        spec: Vega-Lite specification.
        use_container_width: If True, use full container width.
        theme: Chart theme.
        key: Optional key.
    """
    chart_spec = spec or {}

    # Embed data if provided
    if data is not None:
        chart_spec = {**chart_spec, "data": {"values": _data_to_values(data)}}

    _emit_node(
        "vega_lite_chart",
        {
            "spec": chart_spec,
            "useContainerWidth": use_container_width,
            "theme": theme,
        },
        key=key,
    )


def _altair_to_spec(chart: Any) -> dict:
    """Convert Altair chart to Vega-Lite spec."""
    if hasattr(chart, "to_dict"):
        return chart.to_dict()
    return {}


def _data_to_values(data: Any) -> list[dict]:
    """Convert data to list of records for Vega-Lite."""
    try:
        import pandas as pd

        if isinstance(data, pd.DataFrame):
            return data.to_dict(orient="records")
    except ImportError:
        pass

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # Column-oriented to records
        keys = list(data.keys())
        if not keys:
            return []
        length = len(data[keys[0]]) if isinstance(data[keys[0]], list) else 1
        return [
            {k: (data[k][i] if isinstance(data[k], list) else data[k]) for k in keys}
            for i in range(length)
        ]

    return []


def pyplot(
    fig: Any = None,
    *,
    clear_figure: bool = True,
    use_container_width: bool = True,
    key: str | None = None,
) -> None:
    """Display a Matplotlib figure.

    Args:
        fig: Matplotlib figure. If None, uses current figure.
        clear_figure: If True, clear the figure after rendering.
        use_container_width: If True, use full container width.
        key: Optional key.
    """
    import base64
    import io

    try:
        import matplotlib.pyplot as plt

        if fig is None:
            fig = plt.gcf()

        # Render to PNG
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")

        if clear_figure:
            plt.clf()

        _emit_node(
            "pyplot",
            {
                "image": f"data:image/png;base64,{img_base64}",
                "useContainerWidth": use_container_width,
            },
            key=key,
        )
    except ImportError:
        _emit_node(
            "text",
            {"text": "Error: matplotlib is not installed"},
        )


def bokeh_chart(
    figure: Any,
    *,
    use_container_width: bool = True,
    key: str | None = None,
) -> None:
    """Display a Bokeh chart.

    Args:
        figure: Bokeh figure.
        use_container_width: If True, use full container width.
        key: Optional key.
    """
    try:
        from bokeh.embed import json_item

        spec = json_item(figure)

        _emit_node(
            "bokeh_chart",
            {
                "spec": spec,
                "useContainerWidth": use_container_width,
            },
            key=key,
        )
    except ImportError:
        _emit_node(
            "text",
            {"text": "Error: bokeh is not installed"},
        )


def graphviz_chart(
    figure_or_dot: Any,
    *,
    use_container_width: bool = True,
    key: str | None = None,
) -> None:
    """Display a Graphviz chart.

    Args:
        figure_or_dot: Graphviz graph object or DOT string.
        use_container_width: If True, use full container width.
        key: Optional key.
    """
    # Convert to DOT string
    if hasattr(figure_or_dot, "source"):
        dot = figure_or_dot.source
    elif isinstance(figure_or_dot, str):
        dot = figure_or_dot
    else:
        dot = str(figure_or_dot)

    _emit_node(
        "graphviz_chart",
        {
            "dot": dot,
            "useContainerWidth": use_container_width,
        },
        key=key,
    )


def pydeck_chart(
    pydeck_obj: Any = None,
    *,
    use_container_width: bool = True,
    key: str | None = None,
) -> None:
    """Display a PyDeck chart.

    Args:
        pydeck_obj: PyDeck Deck object.
        use_container_width: If True, use full container width.
        key: Optional key.
    """
    if pydeck_obj is None:
        return

    try:
        spec = pydeck_obj.to_json() if hasattr(pydeck_obj, "to_json") else {}

        _emit_node(
            "pydeck_chart",
            {
                "spec": spec,
                "useContainerWidth": use_container_width,
            },
            key=key,
        )
    except Exception:
        _emit_node(
            "text",
            {"text": "Error: Could not render PyDeck chart"},
        )
