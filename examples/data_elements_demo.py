"""Data elements demo — st.metric, st.json, st.dataframe, st.data_editor, st.table"""

import fastlit as st

st.title("Data Elements Demo")

# --- st.metric ---
st.header("st.metric")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Temperature", "72°F", delta="2°F")

with col2:
    st.metric("Revenue", "$12,500", delta="-$500", delta_color="inverse")

with col3:
    st.metric("Active Users", "1,234", delta="12%", help="Compared to last week")

st.divider()

# --- st.json ---
st.header("st.json")

sample_json = {
    "name": "Fastlit",
    "version": "0.1.0",
    "features": ["dataframe", "metric", "json", "data_editor"],
    "config": {
        "server": {"port": 8501, "host": "localhost"},
        "auth": {"enabled": False},
    },
    "stats": {
        "users": 1234,
        "sessions": 5678,
        "uptime_hours": 99.9,
    },
}

st.json(sample_json, expanded=2)

st.divider()

# --- st.dataframe ---
st.header("st.dataframe (virtualized)")

try:
    import pandas as pd
    import numpy as np

    n = 500
    df = pd.DataFrame({
        "id": range(n),
        "name": [f"Item {i}" for i in range(n)],
        "value": np.random.randn(n).round(4),
        "quantity": np.random.randint(1, 100, n),
        "active": np.random.choice([True, False], n),
    })

    st.dataframe(df, height=300)

except ImportError:
    st.markdown("Install pandas and numpy: `pip install pandas numpy`")

st.divider()

# --- st.table (static) ---
st.header("st.table (static, small data)")

small_data = {
    "Method": ["GET", "POST", "PUT", "DELETE"],
    "Count": [1234, 567, 89, 12],
    "Avg (ms)": [45, 123, 89, 34],
}

st.table(small_data)

st.divider()

# --- st.data_editor ---
st.header("st.data_editor (editable)")

st.markdown("Click any cell to edit. Changes are saved automatically.")

try:
    import pandas as pd

    editable_df = pd.DataFrame({
        "Task": ["Design UI", "Write tests", "Deploy"],
        "Status": ["Done", "In Progress", "Pending"],
        "Priority": [1, 2, 3],
    })

    edited = st.data_editor(editable_df, num_rows="dynamic")

    if st.button("Show edited data"):
        st.write("Edited data:")
        st.json(edited.to_dict() if hasattr(edited, "to_dict") else edited)

except ImportError:
    st.markdown("Install pandas: `pip install pandas`")
