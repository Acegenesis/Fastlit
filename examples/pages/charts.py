"""Charts page for the Fastlit demo."""

import fastlit as st

PAGE_CONFIG = {
    "title": "Charts",
    "icon": "📈",
    "order": 50,
}

st.title("📈 Charts")
st.caption("Data visualization components")

# Sample data for charts
chart_data = {
    "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "sales": [100, 120, 140, 130, 180, 200],
    "profit": [20, 25, 30, 22, 40, 45],
    "costs": [80, 95, 110, 108, 140, 155],
}

# -------------------------------------------------------------------------
# st.line_chart()
# -------------------------------------------------------------------------
st.header("st.line_chart()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `data` (DataFrame | dict | list): Chart data
    - `x` (str | None): X-axis column (default: index)
    - `y` (str | list[str] | None): Y-axis column(s)
    - `color` (str | list[str] | None): Line color(s)
    - `width`, `height` (int | None): Dimensions
    - `use_container_width` (bool): Full width
    """)

st.code('''chart_data = {
"month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
"sales": [100, 120, 140, 130, 180, 200],
"profit": [20, 25, 30, 22, 40, 45],
}
st.line_chart(chart_data, x="month", y=["sales", "profit"], height=300)''', language="python")

with st.container(border=True):
    st.line_chart(chart_data, x="month", y=["sales", "profit"], height=300)

# -------------------------------------------------------------------------
# st.bar_chart()
# -------------------------------------------------------------------------
st.header("st.bar_chart()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:** Same as st.line_chart() plus:
    - `horizontal` (bool): Horizontal bars
    """)

st.code('''# Vertical bars
st.bar_chart(chart_data, x="month", y="sales", height=250)

# Horizontal bars
st.bar_chart(chart_data, x="month", y="sales", height=250, horizontal=True)''', language="python")

with st.container(border=True):
    col1, col2 = st.columns(2)
    
    with col1:
        st.caption("Vertical bars")
        st.bar_chart(chart_data, x="month", y="sales", height=250)
    
    with col2:
        st.caption("Horizontal bars")
        st.bar_chart(chart_data, x="month", y="sales", height=250, horizontal=True)

# -------------------------------------------------------------------------
# st.area_chart()
# -------------------------------------------------------------------------
st.header("st.area_chart()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:** Same as st.line_chart() plus:
    - `stack` (bool): Stack areas
    """)

st.code('''st.area_chart(chart_data, x="month", y=["sales", "costs"], height=300, stack=True)''', language="python")

with st.container(border=True):
    st.area_chart(chart_data, x="month", y=["sales", "costs"], height=300, stack=True)

# -------------------------------------------------------------------------
# st.scatter_chart()
# -------------------------------------------------------------------------
st.header("st.scatter_chart()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `data`: Chart data
    - `x`, `y` (str): X and Y columns
    - `color` (str | None): Color column for encoding
    - `size` (str | None): Size column for point sizing
    """)

st.code('''scatter_data = {
"x": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
"y": [15, 25, 35, 20, 55, 45, 70, 85, 75, 95],
"size": [10, 20, 15, 30, 25, 35, 40, 45, 50, 55],
}
st.scatter_chart(scatter_data, x="x", y="y", height=300)''', language="python")

with st.container(border=True):
    scatter_data = {
        "x": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        "y": [15, 25, 35, 20, 55, 45, 70, 85, 75, 95],
        "size": [10, 20, 15, 30, 25, 35, 40, 45, 50, 55],
    }
    st.scatter_chart(scatter_data, x="x", y="y", height=300)

# -------------------------------------------------------------------------
# st.map()
# -------------------------------------------------------------------------
st.header("st.map()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `data` (DataFrame | list | None): Data with lat/lon columns
    - `latitude` (str | None): Latitude column name
    - `longitude` (str | None): Longitude column name
    - `color` (str | None): Marker color
    - `size` (str | None): Size column for markers
    - `zoom` (int | None): Initial zoom level
    - `height` (int | None): Map height
    - `use_container_width` (bool): Full width
    """)

st.code('''map_data = [
{"lat": 48.8566, "lon": 2.3522},   # Paris
{"lat": 51.5074, "lon": -0.1278},  # London
{"lat": 52.5200, "lon": 13.4050},  # Berlin
{"lat": 40.4168, "lon": -3.7038},  # Madrid
{"lat": 41.9028, "lon": 12.4964},  # Rome
]
st.map(map_data, zoom=4, height=400)''', language="python")

with st.container(border=True):
    map_data = [
        {"lat": 48.8566, "lon": 2.3522},   # Paris
        {"lat": 51.5074, "lon": -0.1278},  # London
        {"lat": 52.5200, "lon": 13.4050},  # Berlin
        {"lat": 40.4168, "lon": -3.7038},  # Madrid
        {"lat": 41.9028, "lon": 12.4964},  # Rome
    ]
    st.map(map_data, zoom=4, height=400)

# -------------------------------------------------------------------------
# Advanced Charts (Plotly, Altair, etc.)
# -------------------------------------------------------------------------
st.header("Advanced Charts", divider="blue")
st.caption("Integration with popular Python visualization libraries.")

# -------------------------------------------------------------------------
# st.plotly_chart()
# -------------------------------------------------------------------------
st.subheader("st.plotly_chart()")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `figure_or_data`: Plotly Figure or dict of traces
    - `use_container_width` (bool): Fill container width
    - `theme` (str | None): `"streamlit"` or `None`
    - `on_select` (callable | None): Callback with selected point indices
    - `key` (str | None): Stable widget key

    **Returns:** `list[int]` of selected indices when `on_select` is set, else `None`.
    """)

st.code(
    "import plotly.graph_objects as go\n\n"
    "fig = go.Figure()\n"
    "fig.add_trace(go.Scatter(x=[1,2,3,4,5], y=[2,4,3,5,4],\n"
    "                         mode='lines+markers', name='Series A'))\n"
    "fig.add_trace(go.Bar(x=[1,2,3,4,5], y=[1,3,2,4,3], name='Series B'))\n"
    "fig.update_layout(title='Plotly Mixed Chart', height=350)\n"
    "st.plotly_chart(fig)\n\n"
    "# With cross-filtering (on_select):\n"
    "def on_sel(indices):\n"
    "    st.write('Selected:', indices)\n"
    "st.plotly_chart(fig, on_select=on_sel)",
    language="python",
)

with st.container(border=True):
    try:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[1, 2, 3, 4, 5],
            y=[2, 4, 3, 5, 4],
            mode="lines+markers",
            name="Series A",
            line=dict(color="#6366f1", width=2),
            marker=dict(size=8),
        ))
        fig.add_trace(go.Bar(
            x=[1, 2, 3, 4, 5],
            y=[1, 3, 2, 4, 3],
            name="Series B",
            marker_color="#22d3ee",
            opacity=0.7,
        ))
        fig.update_layout(
            title="Plotly Mixed Chart (Scatter + Bar)",
            height=350,
            legend=dict(orientation="h"),
        )
        st.plotly_chart(fig)
    except ImportError:
        st.warning("Install plotly to see this demo: `pip install plotly`")

# -------------------------------------------------------------------------
# st.altair_chart()
# -------------------------------------------------------------------------
st.subheader("st.altair_chart()")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `altair_chart`: An Altair Chart object
    - `use_container_width` (bool): Fill container width
    - `theme` (str | None): `"streamlit"` or `None`
    - `key` (str | None): Stable widget key
    """)

st.code(
    "import altair as alt\n"
    "import pandas as pd\n\n"
    "df = pd.DataFrame({\n"
    "    'month': ['Jan','Feb','Mar','Apr','May','Jun'],\n"
    "    'sales': [120, 145, 132, 178, 165, 190],\n"
    "})\n\n"
    "chart = alt.Chart(df).mark_bar().encode(\n"
    "    x='month',\n"
    "    y='sales',\n"
    "    color=alt.value('#6366f1'),\n"
    ").properties(title='Monthly Sales', height=300)\n\n"
    "st.altair_chart(chart)",
    language="python",
)

with st.container(border=True):
    try:
        import altair as alt
        import pandas as pd
        df_alt = pd.DataFrame({
            "month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "sales": [120, 145, 132, 178, 165, 190],
            "profit": [40, 55, 48, 72, 60, 85],
        })
        chart = alt.Chart(df_alt).mark_bar().encode(
            x=alt.X("month", sort=None),
            y="sales",
            color=alt.value("#6366f1"),
            tooltip=["month", "sales", "profit"],
        ).properties(title="Monthly Sales (Altair)", height=300)
        st.altair_chart(chart)
    except ImportError:
        st.warning("Install altair to see this demo: `pip install altair`")

# -------------------------------------------------------------------------
# st.vega_lite_chart()
# -------------------------------------------------------------------------
st.subheader("st.vega_lite_chart()")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `data`: Data (DataFrame, dict, list) — injected as `data.values` in the spec
    - `spec` (dict): Vega-Lite specification
    - `use_container_width` (bool): Fill container width
    - `theme` (str | None): `"streamlit"` or `None`
    - `key` (str | None): Stable widget key
    """)

st.code(
    "data = [\n"
    "    {'x': 1, 'y': 5}, {'x': 2, 'y': 3},\n"
    "    {'x': 3, 'y': 8}, {'x': 4, 'y': 6},\n"
    "]\n"
    "spec = {\n"
    "    'mark': {'type': 'point', 'filled': True},\n"
    "    'encoding': {\n"
    "        'x': {'field': 'x', 'type': 'quantitative'},\n"
    "        'y': {'field': 'y', 'type': 'quantitative'},\n"
    "        'size': {'value': 100},\n"
    "    },\n"
    "    'height': 300,\n"
    "}\n"
    "st.vega_lite_chart(data, spec)",
    language="python",
)

with st.container(border=True):
    vl_data = [
        {"x": i, "y": (i * 13 % 17) + 2, "cat": "A" if i % 2 == 0 else "B"}
        for i in range(1, 13)
    ]
    vl_spec = {
        "mark": {"type": "point", "filled": True, "size": 80},
        "encoding": {
            "x": {"field": "x", "type": "quantitative", "title": "X value"},
            "y": {"field": "y", "type": "quantitative", "title": "Y value"},
            "color": {"field": "cat", "type": "nominal"},
            "tooltip": [
                {"field": "x", "type": "quantitative"},
                {"field": "y", "type": "quantitative"},
                {"field": "cat", "type": "nominal"},
            ],
        },
        "height": 300,
        "title": "Vega-Lite Scatter (no extra dependencies)",
    }
    st.vega_lite_chart(vl_data, vl_spec)

# -------------------------------------------------------------------------
# st.pyplot()
# -------------------------------------------------------------------------
st.subheader("st.pyplot()")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `fig`: Matplotlib figure. If `None`, uses `plt.gcf()`
    - `clear_figure` (bool): Clear the figure after rendering (default `True`)
    - `use_container_width` (bool): Fill container width
    - `key` (str | None): Stable widget key

    Rendered server-side as PNG — no client dependency on Matplotlib.
    """)

st.code(
    "import matplotlib.pyplot as plt\n"
    "import numpy as np\n\n"
    "fig, ax = plt.subplots(figsize=(8, 4))\n"
    "x = np.linspace(0, 2 * np.pi, 200)\n"
    "ax.plot(x, np.sin(x), label='sin(x)', color='#6366f1')\n"
    "ax.plot(x, np.cos(x), label='cos(x)', color='#22d3ee')\n"
    "ax.set_title('Matplotlib: sin & cos')\n"
    "ax.legend()\n"
    "st.pyplot(fig)",
    language="python",
)

with st.container(border=True):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        fig, ax = plt.subplots(figsize=(8, 4))
        x = np.linspace(0, 2 * np.pi, 200)
        ax.plot(x, np.sin(x), label="sin(x)", color="#6366f1", linewidth=2)
        ax.plot(x, np.cos(x), label="cos(x)", color="#22d3ee", linewidth=2)
        ax.fill_between(x, np.sin(x), alpha=0.1, color="#6366f1")
        ax.set_title("Matplotlib: sin & cos")
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    except ImportError:
        st.warning("Install matplotlib to see this demo: `pip install matplotlib`")

# -------------------------------------------------------------------------
# st.bokeh_chart()
# -------------------------------------------------------------------------
st.subheader("st.bokeh_chart()")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `figure`: Bokeh figure object
    - `use_container_width` (bool): Fill container width
    - `key` (str | None): Stable widget key

    Bokeh renders client-side via BokehJS — interactive zoom/pan included.
    """)

st.code(
    "from bokeh.plotting import figure\n\n"
    "p = figure(title='Bokeh Line Chart', height=300, width=600)\n"
    "p.line([1,2,3,4,5], [6,7,2,4,5],\n"
    "       line_width=2, color='#6366f1', legend_label='Data')\n"
    "p.circle([1,2,3,4,5], [6,7,2,4,5],\n"
    "         size=8, color='#22d3ee', fill_color='white')\n"
    "st.bokeh_chart(p)",
    language="python",
)

with st.container(border=True):
    try:
        from bokeh.plotting import figure as bokeh_figure
        p = bokeh_figure(title="Bokeh Line Chart", height=300, sizing_mode="stretch_width")
        x_vals = [1, 2, 3, 4, 5, 6]
        y_vals = [6, 7, 2, 4, 5, 8]
        p.line(x_vals, y_vals, line_width=2, color="#6366f1", legend_label="Series A")
        p.scatter(x_vals, y_vals, size=8, color="#22d3ee", fill_color="white", line_width=2)
        p.legend.location = "top_left"
        st.bokeh_chart(p)
    except ImportError:
        st.warning("Install bokeh to see this demo: `pip install bokeh`")

# -------------------------------------------------------------------------
# st.graphviz_chart()
# -------------------------------------------------------------------------
st.subheader("st.graphviz_chart()")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `figure_or_dot`: DOT language string or a `graphviz.Graph` / `graphviz.Digraph` object
    - `use_container_width` (bool): Fill container width
    - `key` (str | None): Stable widget key

    Rendered via `@hpcc-js/wasm` — no server-side Graphviz install needed.
    """)

st.code(
    'st.graphviz_chart("""\n'
    "    digraph Pipeline {\n"
    "        rankdir=LR\n"
    '        node [shape=box style=filled fillcolor="#e0e7ff"]\n'
    "        Input -> Preprocess -> Model -> Postprocess -> Output\n"
    "        Preprocess -> Cache\n"
    "        Cache -> Model\n"
    "    }\n"
    '""")',
    language="python",
)

with st.container(border=True):
    st.graphviz_chart("""
        digraph Pipeline {
            rankdir=LR
            node [shape=box style=filled fillcolor="#e0e7ff" fontname="Arial"]
            edge [color="#6366f1"]
            Input -> Preprocess -> Model -> Postprocess -> Output
            Preprocess -> Cache [style=dashed]
            Cache -> Model [style=dashed label="hit"]
        }
    """)

# -------------------------------------------------------------------------
# st.pydeck_chart()
# -------------------------------------------------------------------------
st.subheader("st.pydeck_chart()")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `pydeck_obj`: A `pydeck.Deck` object
    - `use_container_width` (bool): Fill container width
    - `key` (str | None): Stable widget key

    Renders 3D maps and geospatial visualizations via deck.gl.
    """)

st.code(
    "import pydeck as pdk\n\n"
    "layer = pdk.Layer(\n"
    "    'ScatterplotLayer',\n"
    "    data=[{'lat': 48.8566, 'lon': 2.3522, 'name': 'Paris'},\n"
    "          {'lat': 51.5074, 'lon': -0.1278, 'name': 'London'},\n"
    "          {'lat': 52.5200, 'lon': 13.4050, 'name': 'Berlin'}],\n"
    "    get_position='[lon, lat]',\n"
    "    get_radius=50000,\n"
    "    get_fill_color=[99, 102, 241, 180],\n"
    "    pickable=True,\n"
    ")\n"
    "deck = pdk.Deck(\n"
    "    layers=[layer],\n"
    "    initial_view_state=pdk.ViewState(latitude=50, longitude=6,\n"
    "                                      zoom=4, pitch=30),\n"
    "    tooltip={'text': '{name}'},\n"
    ")\n"
    "st.pydeck_chart(deck)",
    language="python",
)

with st.container(border=True):
    try:
        import pydeck as pdk
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=[
                {"lat": 48.8566, "lon": 2.3522, "name": "Paris"},
                {"lat": 51.5074, "lon": -0.1278, "name": "London"},
                {"lat": 52.5200, "lon": 13.4050, "name": "Berlin"},
                {"lat": 40.4168, "lon": -3.7038, "name": "Madrid"},
                {"lat": 41.9028, "lon": 12.4964, "name": "Rome"},
            ],
            get_position="[lon, lat]",
            get_radius=50000,
            get_fill_color=[99, 102, 241, 180],
            pickable=True,
        )
        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=pdk.ViewState(
                latitude=48, longitude=8, zoom=4, pitch=30
            ),
            tooltip={"text": "{name}"},
            map_style="light",
        )
        st.pydeck_chart(deck)
    except ImportError:
        st.warning("Install pydeck to see this demo: `pip install pydeck`")
