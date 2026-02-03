"""Charts demo — st.line_chart, st.bar_chart, st.area_chart, st.scatter_chart, st.map"""

import fastlit as st

st.title("Charts Demo")

# --- Simple Charts (Recharts) ---
st.header("Simple Charts")

try:
    import pandas as pd
    import numpy as np

    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "sales": np.random.randint(100, 500, 30),
        "revenue": np.random.randint(1000, 5000, 30),
        "profit": np.random.randint(200, 800, 30),
    })

    st.subheader("Line Chart")
    st.line_chart(df, x="date", y=["sales", "revenue"])

    st.subheader("Bar Chart")
    bar_data = pd.DataFrame({
        "category": ["A", "B", "C", "D", "E"],
        "value": [23, 45, 56, 78, 32],
    })
    st.bar_chart(bar_data, x="category", y="value")

    st.subheader("Area Chart")
    st.area_chart(df, x="date", y=["sales", "profit"], stack=True)

    st.subheader("Scatter Chart")
    scatter_df = pd.DataFrame({
        "x": np.random.randn(50),
        "y": np.random.randn(50),
    })
    st.scatter_chart(scatter_df, x="x", y="y")

except ImportError:
    st.markdown("Install pandas and numpy: `pip install pandas numpy`")

    # Fallback with simple data
    st.line_chart([10, 20, 15, 25, 30, 22, 35])
    st.bar_chart([23, 45, 56, 78, 32])

st.divider()

# --- Map ---
st.header("Map")

# Sample locations (major cities)
locations = [
    {"lat": 48.8566, "lon": 2.3522},   # Paris
    {"lat": 51.5074, "lon": -0.1278},  # London
    {"lat": 40.7128, "lon": -74.0060}, # New York
    {"lat": 35.6762, "lon": 139.6503}, # Tokyo
    {"lat": -33.8688, "lon": 151.2093}, # Sydney
]

st.map(locations, zoom=2)

st.divider()

# --- Plotly (if available) ---
st.header("Plotly Chart")

try:
    import plotly.express as px

    fig = px.scatter(
        x=[1, 2, 3, 4, 5],
        y=[1, 4, 2, 3, 5],
        size=[10, 20, 30, 40, 50],
        color=["A", "B", "C", "D", "E"],
        title="Plotly Scatter Plot",
    )
    st.plotly_chart(fig)

except ImportError:
    st.markdown("Install plotly: `pip install plotly`")

st.divider()

# --- Graphviz ---
st.header("Graphviz Chart")

dot_graph = """
digraph {
    A -> B
    B -> C
    B -> D
    C -> E
    D -> E
    A -> D
}
"""
st.graphviz_chart(dot_graph)

st.divider()

# --- Matplotlib (if available) ---
st.header("Matplotlib (pyplot)")

try:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
    ax.set_title("Matplotlib Figure")
    ax.set_xlabel("X axis")
    ax.set_ylabel("Y axis")
    st.pyplot(fig)

except ImportError:
    st.markdown("Install matplotlib: `pip install matplotlib`")
