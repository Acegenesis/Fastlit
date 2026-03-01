"""Data Display page for the Fastlit demo."""

import inspect

import fastlit as st

PAGE_CONFIG = {
    "title": "Data Display",
    "icon": "📊",
    "order": 40,
}


st.title("📊 Data Display")
st.caption("Components for displaying data")

# Sample data
sample_data = {
    "Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
    "Age": [25, 30, 35, 28, 32],
    "City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
    "Score": [85.5, 92.0, 78.5, 95.0, 88.5],
    "Active": [True, False, True, True, False],
    "Joined": ["2024-01-15", "2023-06-20", "2024-03-01", "2023-11-10", "2024-02-28"],
}

# -------------------------------------------------------------------------
# st.dataframe()
# -------------------------------------------------------------------------
st.header("st.dataframe()", divider="blue")
st.caption("New in Fastlit: `on_select` + `selection_mode` for interactive row selection.")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `data` (DataFrame | dict | list): Data to display
    - `height` (int | None): Height in pixels (auto-sizes up to 400px)
    - `use_container_width` (bool): Stretch to container width
    - `hide_index` (bool): Hide row index
    - `on_select` ("rerun" | Callable | None): Selection callback behavior
    - `selection_mode` ("single-row" | "multi-row"): Row selection mode
    - `key` (str | None): Unique key
    
    **Features:**
    - Virtualized rendering (handles millions of rows)
    - Column sorting (click headers)
    - Column resizing
    - Smooth scrolling

    **Returns:** Selection object with `.rows` when `on_select` is set, else `None`
    """)

st.code('''sample_data = {
"Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
"Age": [25, 30, 35, 28, 32],
"City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
"Score": [85.5, 92.0, 78.5, 95.0, 88.5],
"Active": [True, False, True, True, False],
}
st.dataframe(sample_data, height=400)

# With hidden index:
st.dataframe(sample_data, height=300, hide_index=True)

# With column_config and sticky column:
st.dataframe(
sample_data,
height=400,
column_config={
    "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
    "Score": st.column_config.NumberColumn("Score", format="%.1f", resizable=True),
    "Active": st.column_config.CheckboxColumn("Active"),
},
)''', language="python")

with st.container(border=True):
    st.dataframe(sample_data, height=300)
    
    st.caption("With hidden index:")
    st.dataframe(sample_data, height=300, hide_index=True)
    
    st.caption("With column_config, sticky `Name` column and resize:")
    st.dataframe(
        sample_data,
        height=400,
        column_config={
            "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
            "Score": st.column_config.NumberColumn("Score", format="%.1f", resizable=True),
            "Active": st.column_config.CheckboxColumn("Active"),
        },
    )

dataframe_params = inspect.signature(st.dataframe).parameters
supports_df_selection = {"on_select", "selection_mode"}.issubset(dataframe_params.keys())

if supports_df_selection:
    st.code('''selection_demo_data = {
"Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
"Age": [25, 30, 35, 28, 32],
"City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
"Score": [85.5, 92.0, 78.5, 95.0, 88.5],
"Active": [True, False, True, True, False],
}

selection = st.dataframe(
selection_demo_data,
on_select="rerun",
selection_mode="multi-row",
height=180,
key="df_selection_demo",
)

st.write(f"Selected rows: {selection.rows if selection is not None else []}")''', language="python")

    with st.container(border=True):
        selection_demo_data = {
            "Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
            "Age": [25, 30, 35, 28, 32],
            "City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
            "Score": [85.5, 92.0, 78.5, 95.0, 88.5],
            "Active": [True, False, True, True, False],
        }

        selection = st.dataframe(
            selection_demo_data,
            on_select="rerun",
            selection_mode="multi-row",
            height=300,
            key="df_selection_demo",
        )

        st.write(f"Selected rows: {selection.rows if selection is not None else []}")
else:
    st.warning(
        "This runtime does not expose `st.dataframe(on_select=..., selection_mode=...)` yet. "
        "Using compatibility fallback."
    )
    st.code('''selection_demo_data = {
"Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
"Age": [25, 30, 35, 28, 32],
"City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
"Score": [85.5, 92.0, 78.5, 95.0, 88.5],
"Active": [True, False, True, True, False],
}

st.dataframe(selection_demo_data, height=180, key="df_selection_demo")''', language="python")

    with st.container(border=True):
        selection_demo_data = {
            "Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
            "Age": [25, 30, 35, 28, 32],
            "City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
            "Score": [85.5, 92.0, 78.5, 95.0, 88.5],
            "Active": [True, False, True, True, False],
        }
        st.dataframe(selection_demo_data, height=300, key="df_selection_demo")

# -------------------------------------------------------------------------
# st.data_editor()
# -------------------------------------------------------------------------
st.header("st.data_editor()", divider="blue")
st.caption("Editing with toolbar, persisted view state, column resize and sticky columns.")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `data`: Data to edit
    - `height`, `width`: Dimensions
    - `use_container_width` (bool): Full width
    - `hide_index` (bool): Hide index
    - `column_order` (list[str]): Column display order
    - `column_config` (dict): Column configurations
    - `num_rows` (str): "fixed" or "dynamic" (allow add/remove rows)
    - `disabled` (bool | list[str]): Disable all or specific columns
    - `row_height` (int | None): Fixed row height
    - `placeholder` (str | None): Empty state message
    - `toolbar` / `downloadable` / `persist_view`: UX controls
    - `on_change` (Callable): Callback when data changes
    
    **Returns:** Edited data
    """)

st.code('''import pandas as pd

editor_demo_df = pd.DataFrame(sample_data)

edited = st.data_editor(
editor_demo_df,
height=250,
num_rows="dynamic",
persist_view=True,
column_config={
    "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
    "Score": st.column_config.NumberColumn("Score", min_value=0, max_value=100, format="%.1f", resizable=True),
    "Active": st.column_config.CheckboxColumn("Active"),
    "Joined": st.column_config.DateColumn("Joined", format="YYYY-MM-DD", resizable=True),
}
)

st.caption(f"Returned type: {type(edited).__name__}")
st.json(edited.to_dict(orient="records"))''', language="python")

with st.container(border=True):
    import pandas as _pd_editor

    edited = st.data_editor(
        _pd_editor.DataFrame(sample_data),
        height=400,
        num_rows="dynamic",
        persist_view=True,
        column_config={
            "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
            "Score": st.column_config.NumberColumn("Score", min_value=0, max_value=100, format="%.1f", resizable=True),
            "Active": st.column_config.CheckboxColumn("Active"),
            "Joined": st.column_config.DateColumn("Joined", format="YYYY-MM-DD", resizable=True),
        }
    )
    
    st.caption(f"Returned type: `{type(edited).__name__}`")
    st.caption("Astuce: teste la recherche, les filtres, le resize des colonnes et la colonne `Name` sticky.")
    st.json(edited.to_dict(orient="records"))

# -------------------------------------------------------------------------
# Column Configuration
# -------------------------------------------------------------------------
st.header("Column Configuration", divider="blue")

with st.expander("📖 All Column Types", expanded=True):
    st.markdown("""
    | Type | Usage |
    |------|-------|
    | `TextColumn` | Text with validation |
    | `NumberColumn` | Numeric with min/max/step |
    | `CheckboxColumn` | Boolean checkbox |
    | `SelectboxColumn` | Dropdown select |
    | `DateColumn` | Date picker |
    | `TimeColumn` | Time picker |
    | `DatetimeColumn` | Date + time |
    | `ProgressColumn` | Progress bar |
    | `LinkColumn` | Clickable URL |
    | `ImageColumn` | Image preview |
    | `LineChartColumn` | Sparkline chart |
    | `BarChartColumn` | Sparkbar chart |
    | `AreaChartColumn` | Spark area chart |
    | `ListColumn` | Array display |
    | `MultiselectColumn` | Editable chips |
    | `JSONColumn` | Expandable JSON cell |
    """)

st.code('''st.column_config.NumberColumn("Price", min_value=0, max_value=1000, format="$%.2f", resizable=True)
st.column_config.ProgressColumn("Progress", min_value=0, max_value=100)
st.column_config.MultiselectColumn("Tags", options=["ops", "beta"])
st.column_config.JSONColumn("Payload")''', language="python")

st.subheader("Live demo - all column_config types")
st.caption("Text, numbers, booleans, select, chips, JSON, images, links and spark area columns.")

import pandas as _pd_cc

_cc_df = _pd_cc.DataFrame({
    "Name": ["Alice", "Bob", "Charlie", "Diana"],
    "Score": [87.5, 92.0, 78.3, 95.1],
    "Active": [True, False, True, True],
    "Role": ["admin", "user", "user", "viewer"],
    "Progress": [75, 45, 90, 60],
    "Tags": [["ops", "admin"], ["sales"], ["ml", "viz"], ["viewer", "beta"]],
    "Segments": [["ops", "admin"], ["sales"], ["ml", "viz"], ["viewer", "beta"]],
    "Payload": [
        {"tier": "gold", "quota": 12},
        {"tier": "silver", "quota": 8},
        {"tier": "bronze", "quota": 5},
        {"tier": "beta", "quota": 2},
    ],
    "Trend": [[3, 4, 5, 6], [4, 4, 5, 7], [2, 3, 3, 4], [1, 2, 4, 6]],
    "Avatar": [
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=120&q=80",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&q=80",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=120&q=80",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=120&q=80",
    ],
    "Link": [
        "https://fastlit.dev",
        "https://streamlit.io",
        "https://github.com",
        "",
    ],
})

st.code('''result = st.data_editor(
df,
column_config={
    "Name":     st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
    "Score":    st.column_config.NumberColumn("Score /100", min_value=0, max_value=100, step=0.5, resizable=True),
    "Active":   st.column_config.CheckboxColumn("Active ?"),
    "Role":     st.column_config.SelectboxColumn("Role", options=["admin", "user", "viewer"]),
    "Progress": st.column_config.ProgressColumn("Progress %", min_value=0, max_value=100),
    "Tags":     st.column_config.ListColumn("Tags", resizable=True),
    "Segments": st.column_config.MultiselectColumn("Segments", options=["ops", "admin", "sales", "ml", "viz", "viewer", "beta"]),
    "Payload":  st.column_config.JSONColumn("Payload", width="large"),
    "Trend":    st.column_config.AreaChartColumn("Trend", y_min=0, y_max=8),
    "Avatar":   st.column_config.ImageColumn("Avatar"),
    "Link":     st.column_config.LinkColumn("URL", display_text="Open", resizable=True),
},
num_rows="dynamic",
)''', language="python")

with st.container(border=True):
    _cc_result = st.data_editor(
        _cc_df,
        column_config={
            "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
            "Score": st.column_config.NumberColumn(
                "Score /100", min_value=0, max_value=100, step=0.5, resizable=True
            ),
            "Active": st.column_config.CheckboxColumn("Active ?"),
            "Role": st.column_config.SelectboxColumn(
                "Role", options=["admin", "user", "viewer"]
            ),
            "Progress": st.column_config.ProgressColumn(
                "Progress %", min_value=0, max_value=100
            ),
            "Tags": st.column_config.ListColumn("Tags", resizable=True),
            "Segments": st.column_config.MultiselectColumn(
                "Segments",
                options=["ops", "admin", "sales", "ml", "viz", "viewer", "beta"],
            ),
            "Payload": st.column_config.JSONColumn("Payload", width="large"),
            "Trend": st.column_config.AreaChartColumn("Trend", y_min=0, y_max=8),
            "Avatar": st.column_config.ImageColumn("Avatar"),
            "Link": st.column_config.LinkColumn("URL", display_text="Open", resizable=True),
        },
        height=400,
        num_rows="dynamic",
        key="cc_demo_editor",
    )
    st.caption("Edited data:")
    st.caption("Resize `Name`, `Score`, `Tags` or `Link`, then try `Segments`, `Payload` and `Trend`.")
    if hasattr(_cc_result, "to_dict"):
        st.json(_cc_result.to_dict(orient="records"))
    else:
        st.json(_cc_result)

# -------------------------------------------------------------------------
# st.table()
# -------------------------------------------------------------------------
st.header("st.table()", divider="blue")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
    **Parameters:**
    - `data` (DataFrame | dict | list): Data to display
    - `key` (str | None): Unique key
    
    **Note:** Static table - use for small data only. For large data, use st.dataframe().
    """)

st.code('''small_data = {
"Feature": ["Fast", "Compatible", "Modern"],
"Status": ["✅", "✅", "✅"],
}
st.table(small_data)''', language="python")

with st.container(border=True):
    import pandas as _pd_table

    small_data = _pd_table.DataFrame({
        "Feature": ["Fast", "Compatible", "Modern"],
        "Status": ["✅", "✅", "✅"],
    })
    st.table(small_data)

# -------------------------------------------------------------------------
# st.metric()
# -------------------------------------------------------------------------
st.header("st.metric()", divider="blue")

st.code('''cols = st.columns(4)

with cols[0]:
st.metric("Revenue", 12345, delta=5.2, format="$,.0f", chart_data=[9, 10, 12, 11, 14, 16], chart_type="area", border=True)
with cols[1]:
st.metric("Users", 1234, delta=120, chart_data=[980, 1010, 1100, 1130, 1200, 1234], chart_type="line")
with cols[2]:
st.metric("Errors", 23, delta=-8, delta_color="inverse", delta_arrow="down", chart_data=[40, 33, 28, 26, 25, 23], chart_type="bar")
with cols[3]:
st.metric("Status", "OK", delta="Stable", delta_arrow="off", border=True)''', language="python")

with st.container(border=True):
    cols = st.columns(4)
    
    with cols[0]:
        st.metric(
            "Revenue",
            12345,
            delta=5.2,
            format="$,.0f",
            chart_data=[9, 10, 12, 11, 14, 16],
            chart_type="area",
            border=True,
        )
    with cols[1]:
        st.metric(
            "Users",
            1234,
            delta=120,
            chart_data=[980, 1010, 1100, 1130, 1200, 1234],
            chart_type="line",
        )
    with cols[2]:
        st.metric(
            "Errors",
            23,
            delta=-8,
            delta_color="inverse",
            delta_arrow="down",
            chart_data=[40, 33, 28, 26, 25, 23],
            chart_type="bar",
        )
    with cols[3]:
        st.metric("Status", "OK", delta="Stable", delta_arrow="off", border=True)

# -------------------------------------------------------------------------
# st.json()
# -------------------------------------------------------------------------
st.header("st.json()", divider="blue")

st.code('''st.json({
"app": "Fastlit",
"version": "0.2.0",
"config": {
    "debug": True,
    "port": 8501,
    "features": {
        "caching": True,
        "hot_reload": True,
        "copy_path": True
    }
},
"authors": ["Developer 1", "Developer 2"]
}, expanded=2)

# Search, global expand/collapse and copy path/value''', language="python")

with st.container(border=True):
    st.json({
        "app": "Fastlit",
        "version": "0.2.0",
        "config": {
            "debug": True,
            "port": 8501,
            "features": {
                "caching": True,
                "hot_reload": True,
                "copy_path": True
            }
        },
        "authors": ["Developer 1", "Developer 2"]
    }, expanded=2)
