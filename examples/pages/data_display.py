"""Data Display page - complete showcase of Fastlit data components."""

import pandas as pd
import fastlit as st

PAGE_CONFIG = {
    "title": "Data Display",
    "icon": "📊",
    "order": 40,
}


# ---------------------------------------------------------------------------
# Shared datasets
# ---------------------------------------------------------------------------

USERS_DATA = {
    "Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
    "Age": [25, 30, 35, 28, 32],
    "City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
    "Score": [85.5, 92.0, 78.5, 95.0, 88.5],
    "Active": [True, False, True, True, False],
    "Joined": ["2024-01-15", "2023-06-20", "2024-03-01", "2023-11-10", "2024-02-28"],
}

USERS_DF = pd.DataFrame(USERS_DATA)


def _build_paginated_users(total_rows: int = 120) -> pd.DataFrame:
    names = USERS_DATA["Name"]
    ages = USERS_DATA["Age"]
    cities = USERS_DATA["City"]
    scores = USERS_DATA["Score"]
    active_flags = USERS_DATA["Active"]
    joined_dates = USERS_DATA["Joined"]

    records: list[dict[str, object]] = []
    source_len = len(names)

    for idx in range(total_rows):
        base_idx = idx % source_len
        cycle = idx // source_len
        joined_at = pd.Timestamp(joined_dates[base_idx]) + pd.Timedelta(days=7 * cycle)

        records.append(
            {
                "User ID": idx + 1,
                "Name": names[base_idx],
                "Age": ages[base_idx] + (cycle % 4),
                "City": cities[base_idx],
                "Score": round(min(100.0, scores[base_idx] + (cycle % 6) * 1.2), 1),
                "Active": active_flags[base_idx] if cycle % 2 == 0 else not active_flags[base_idx],
                "Joined": joined_at.strftime("%Y-%m-%d"),
            }
        )

    return pd.DataFrame(records)


PAGINATED_USERS_DF = _build_paginated_users()


def _manual_users_query(query: st.DataframeQueryRequest) -> st.DataframeQueryResult:
    view = PAGINATED_USERS_DF.copy()
    if query.search:
        lowered = query.search.lower()
        mask = view.astype(str).apply(lambda series: series.str.lower().str.contains(lowered, regex=False))
        view = view[mask.any(axis=1)]

    for sort in reversed(query.sorts):
        ascending = sort.direction != "desc"
        if sort.column in view.columns:
            view = view.sort_values(sort.column, ascending=ascending, kind="stable")

    start = min(query.offset, len(view))
    end = min(len(view), start + query.limit)
    window = view.iloc[start:end]

    return st.DataframeQueryResult(
        rows=window.values.tolist(),
        total_rows=len(view),
        columns=[{"name": str(column), "type": "auto"} for column in view.columns],
        index=window.index.tolist(),
        positions=list(range(start, end)),
        schema_version="users-v1",
        diagnostics={"mode": "manual-demo"},
    )


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("📊 Data Display")
st.caption(
    "All Fastlit data components in one place: virtualized DataFrame, "
    "Data Editor, Metrics, JSON, and static Table."
)

st.code(
    """USERS_DATA = {
    "Name": ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
    "Age": [25, 30, 35, 28, 32],
    "City": ["Paris", "London", "Berlin", "Madrid", "Rome"],
    "Score": [85.5, 92.0, 78.5, 95.0, 88.5],
    "Active": [True, False, True, True, False],
    "Joined": ["2024-01-15", "2023-06-20", "2024-03-01", "2023-11-10", "2024-02-28"],
}

USERS_DF = pd.DataFrame(USERS_DATA)
""",
    language="python",
)


# ---------------------------------------------------------------------------
# 1. st.dataframe
# ---------------------------------------------------------------------------

st.header("st.dataframe()", divider="blue")
st.caption("Virtualized DataFrame with toolbar, sorting, filtering, resize, and CSV export.")

with st.expander("📖 Parameters", expanded=False):
    st.markdown(
        """
| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | DataFrame / dict / list | Data to display |
| `height` | int / "auto" | Height in pixels |
| `width` | int / "stretch" / "content" | Width |
| `hide_index` | bool | Hide the index |
| `column_order` | list[str] | Column order |
| `column_config` | dict | Per-column config |
| `toolbar` | bool | Show the toolbar |
| `show_search` | bool | Show the search input |
| `show_filters` | bool | Show the filters popover |
| `show_column_manager` | bool | Show the columns button |
| `show_reset_view` | bool | Show the reset button |
| `show_footer_summary` | bool | Show footer row/column badges |
| `downloadable` | bool | CSV export button |
| `persist_view` | bool | Persist sort/filter/scroll |
| `pagination` | bool / "text" / "number" / "icon" | Fastlit-only pagination UI |
| `page_size` | int | Rows per page when pagination is enabled |
| `on_query` | Callable | Fastlit-only server/manual query callback |
| `on_select` | "rerun" / Callable / None | Selection mode |
| `selection_mode` | "single-row" / "multi-row" | Selection behavior |
| `key` | str | Stable key |

**Returns**: `DataframeSelection` when `on_select` is set, otherwise `None`.
        """
    )

st.subheader("Basic display")
st.code("""st.dataframe(df, height=260, hide_index=True)""", language="python")
with st.container(border=True):
    st.dataframe(USERS_DF, height=260, hide_index=True)

st.subheader("Pagination")
st.caption(
    "Native pagination supports modes: `pagination='text'`, "
    "`pagination='number'`, or `pagination='icon'`."
)
st.code(
    """st.dataframe(
    df,
    pagination="text",
    page_size=10,
    hide_index=True,
)""",
    language="python",
)
with st.container(border=True):
    mode_col_a, mode_col_b = st.columns(2)
    with mode_col_a:
        st.caption("Mode: text")
        st.dataframe(
            PAGINATED_USERS_DF,
            height=300,
            hide_index=True,
            pagination="text",
            page_size=8,
            key="df_paginated_text",
        )
    with mode_col_b:
        st.caption("Mode: number")
        st.dataframe(
            PAGINATED_USERS_DF,
            height=300,
            hide_index=True,
            pagination="number",
            page_size=8,
            key="df_paginated_number",
        )

    st.caption("Mode: icon")
    st.dataframe(
        PAGINATED_USERS_DF,
        height=320,
        hide_index=True,
        pagination="icon",
        page_size=10,
        key="df_paginated_icon",
    )

st.subheader("Manual server query (`on_query`) - Fastlit extension")
st.caption(
    "`on_query` lets the app provide rows on demand from a DB, API, or warehouse. "
    "The same search, sort, and pagination UI stays active in the grid."
)
st.code(
    """st.dataframe(
    on_query=_manual_users_query,
    height=320,
    pagination="number",
    page_size=10,
    hide_index=True,
)""",
    language="python",
)
with st.container(border=True):
    st.dataframe(
        on_query=_manual_users_query,
        height=320,
        pagination="number",
        page_size=10,
        hide_index=True,
        key="df_manual_query",
    )

st.subheader("With column_config")
st.code(
    """st.dataframe(
    df,
    height=280,
    column_config={
        "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
        "Score": st.column_config.NumberColumn("Score /100", format="%.1f", resizable=True),
        "Active": st.column_config.CheckboxColumn("Active"),
        "Joined": st.column_config.DateColumn("Joined"),
    },
)""",
    language="python",
)
with st.container(border=True):
    st.dataframe(
        USERS_DF,
        height=280,
        column_config={
            "Name": st.column_config.TextColumn("Name", width="medium", resizable=True, pinned="left"),
            "Score": st.column_config.NumberColumn("Score /100", format="%.1f", resizable=True),
            "Active": st.column_config.CheckboxColumn("Active"),
            "Joined": st.column_config.DateColumn("Joined"),
        },
    )

st.subheader("Search and filters visible by default")
st.caption("Search and filters are enabled by default. You can hide them explicitly, and toolbar buttons collapse to icon-only when space gets tight.")
st.code(
    """st.dataframe(
    df,
    height=280,
    show_search=True,   # default
    show_filters=True,  # default
)

st.dataframe(
    df,
    height=280,
    show_search=False,
    show_filters=False,
    show_footer_summary=False,
)""",
    language="python",
)
with st.container(border=True):
    col_a, col_b = st.columns(2)
    with col_a:
        st.caption("Default toolbar")
        st.dataframe(
            USERS_DF,
            height=240,
            hide_index=True,
            key="df_toolbar_default",
        )
    with col_b:
        st.caption("Search + filters disabled")
        st.dataframe(
            USERS_DF,
            height=240,
            hide_index=True,
            show_search=False,
            show_filters=False,
            show_column_manager=False,
            show_reset_view=False,
            show_footer_summary=False,
            downloadable=False,
            key="df_toolbar_hidden",
        )

st.subheader("Interactive selection (`on_select`)")
st.caption("Click one or more rows. The selected row indices are returned to Python.")
st.code(
    """selection = st.dataframe(
    df,
    on_select="rerun",
    selection_mode="multi-row",
    height=280,
    key="df_select",
)
st.write("Selected rows:", selection.rows)""",
    language="python",
)
with st.container(border=True):
    sel = st.dataframe(
        USERS_DF,
        on_select="rerun",
        selection_mode="multi-row",
        height=280,
        key="df_select",
    )
    if sel and sel.rows:
        selected_users = [USERS_DATA["Name"][i] for i in sel.rows if i < len(USERS_DATA["Name"])]
        st.success(f"Rows {sel.rows} -> {', '.join(selected_users)}")
    else:
        st.info("No row selected yet. Click the checkboxes to select rows.")

st.subheader("Single-row selection (`single-row`)")
st.code(
    """def on_row_selected(s):
    st.session_state.selected_user = s.rows[0] if s.rows else None

selection = st.dataframe(
    df,
    on_select=on_row_selected,
    selection_mode="single-row",
    height=280,
)""",
    language="python",
)
with st.container(border=True):
    if "selected_user_idx" not in st.session_state:
        st.session_state.selected_user_idx = None

    def _on_single_select(selection):
        st.session_state.selected_user_idx = selection.rows[0] if selection.rows else None

    st.dataframe(
        USERS_DF,
        on_select=_on_single_select,
        selection_mode="single-row",
        height=280,
        key="df_single_select",
    )
    idx = st.session_state.selected_user_idx
    if idx is not None and idx < len(USERS_DATA["Name"]):
        cols = st.columns(4)
        cols[0].metric("Name", USERS_DATA["Name"][idx])
        cols[1].metric("City", USERS_DATA["City"][idx])
        cols[2].metric("Score", USERS_DATA["Score"][idx])
        cols[3].metric("Active", "✅" if USERS_DATA["Active"][idx] else "❌")
    else:
        st.info("Select a row to inspect its details.")


# ---------------------------------------------------------------------------
# 2. st.data_editor
# ---------------------------------------------------------------------------

st.header("st.data_editor()", divider="blue")
st.caption("Editable grid with add/delete rows, persist_view, resize, and pinned columns.")

with st.expander("📖 Parameters", expanded=False):
    st.markdown(
        """
| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | DataFrame / dict / list | Initial data |
| `num_rows` | "fixed" / "dynamic" | Allow adding rows |
| `disabled` | bool / list[str] | Disable specific columns or all |
| `column_config` | dict | Per-column config |
| `height` | int | Height |
| `on_change` | Callable | Callback on edits |
| `show_search` | bool | Show the search input |
| `show_filters` | bool | Show the filters popover |
| `show_column_manager` | bool | Show the columns button |
| `show_reset_view` | bool | Show the reset button |
| `show_footer_summary` | bool | Show footer row/column badges |
| `show_row_actions` | bool | Show the per-row actions column |
| `persist_view` | bool | Persist visual state |
| `return_changes` | bool | Return `(edited_value, DataEditorChangeSet)` |

**Returns**: DataFrame (or dict/list matching the input shape) with edits applied.
        """
    )

st.subheader("Basic editing with dynamic rows")
st.code(
    """edited = st.data_editor(
    df,
    num_rows="dynamic",
    show_row_actions=False,
    column_config={
        "Name": st.column_config.TextColumn("Name", pinned="left", resizable=True),
        "Score": st.column_config.NumberColumn("Score", min_value=0, max_value=100, step=0.5),
        "Active": st.column_config.CheckboxColumn("Active"),
        "Joined": st.column_config.DateColumn("Joined"),
    },
    key="editor_basic",
)
st.write(f"{len(edited)} rows • {edited['Active'].sum()} active")""",
    language="python",
)

with st.container(border=True):
    edited_basic = st.data_editor(
        USERS_DF.copy(),
        num_rows="dynamic",
        show_row_actions=False,
        column_config={
            "Name": st.column_config.TextColumn("Name", pinned="left", resizable=True),
            "Score": st.column_config.NumberColumn("Score", min_value=0, max_value=100, step=0.5),
            "Active": st.column_config.CheckboxColumn("Active"),
            "Joined": st.column_config.DateColumn("Joined"),
        },
        height=320,
        key="editor_basic",
    )
    n_active = sum(bool(v) for v in edited_basic["Active"]) if hasattr(edited_basic, "__getitem__") else 0
    st.caption(f"{len(edited_basic)} rows · {n_active} active")

st.subheader("Structured diff (`return_changes=True`) - Fastlit extension")
st.code(
    """edited_value, changes = st.data_editor(
    df,
    return_changes=True,
    column_config={
        "Name": st.column_config.TextColumn("Name", required=True, validate_message="Name is required"),
        "Score": st.column_config.NumberColumn("Score", min_value=0, max_value=100),
    },
)
st.write(changes.edited_cells)""",
    language="python",
)
with st.container(border=True):
    edited_value, changes = st.data_editor(
        USERS_DF.copy(),
        return_changes=True,
        height=280,
        column_config={
            "Name": st.column_config.TextColumn("Name", required=True, validate_message="Name is required"),
            "Score": st.column_config.NumberColumn("Score", min_value=0, max_value=100),
        },
        key="editor_changes",
    )
    st.caption(
        f"added={len(changes.added_rows)} · edited={len(changes.edited_cells)} · deleted={len(changes.deleted_rows)}"
    )

st.subheader("Minimal editor toolbar")
st.caption("The footer summary can also be removed, while the Add row action stays available in dynamic mode.")
st.code(
    """st.data_editor(
    df,
    num_rows="dynamic",
    show_search=False,
    show_filters=False,
    show_column_manager=False,
    show_reset_view=False,
    show_footer_summary=False,
    downloadable=False,
    show_row_actions=False,
    key="editor_minimal",
)""",
    language="python",
)
with st.container(border=True):
    st.data_editor(
        USERS_DF.copy(),
        num_rows="dynamic",
        show_search=False,
        show_filters=False,
        show_column_manager=False,
        show_reset_view=False,
        show_footer_summary=False,
        downloadable=False,
        show_row_actions=False,
        height=260,
        key="editor_minimal",
    )

st.subheader("Fully stripped toolbar")
st.code(
    """st.dataframe(
    df,
    hide_index=True,
    show_search=False,
    show_filters=False,
    show_column_manager=False,
    show_reset_view=False,
    show_footer_summary=False,
    downloadable=False,
)""",
    language="python",
)
with st.container(border=True):
    st.dataframe(
        USERS_DF,
        height=220,
        hide_index=True,
        show_search=False,
        show_filters=False,
        show_column_manager=False,
        show_reset_view=False,
        show_footer_summary=False,
        downloadable=False,
        key="df_fully_stripped",
    )


# ---------------------------------------------------------------------------
# 3. column_config
# ---------------------------------------------------------------------------

st.header("column_config - all 15 types", divider="blue")
st.caption(
    "Fastlit supports 15 column types, versus 12 in Streamlit. "
    "The 3 extras are `ListColumn`, `MultiselectColumn`, and `JSONColumn`."
)

with st.expander("📋 Type matrix", expanded=True):
    st.markdown(
        """
| Type | Editor | Extra vs Streamlit |
|------|--------|--------------------|
| `TextColumn` | Text input (+ regex, maxChars) | |
| `NumberColumn` | Numeric input (min/max/step/format) | |
| `CheckboxColumn` | Boolean toggle | |
| `SelectboxColumn` | Dropdown | |
| `DateColumn` | Calendar | |
| `TimeColumn` | Hour/minute/second picker | |
| `DatetimeColumn` | Calendar + time | |
| `ProgressColumn` | Progress bar + slider in popover | |
| `LinkColumn` | URL + open button | |
| `ImageColumn` | Avatar + URL input | |
| `LineChartColumn` | Sparkline (read-only) | |
| `BarChartColumn` | Spark bar chart (read-only) | |
| `AreaChartColumn` | Spark area chart (read-only) | |
| `ListColumn` | JSON textarea in popover | ✅ |
| `MultiselectColumn` | Checkboxes in popover | ✅ |
| `JSONColumn` | Formatted JSON textarea | ✅ |
        """
    )

CC_DF = pd.DataFrame(
    {
        "Name": ["Alice", "Bob", "Charlie", "Diana"],
        "Score": [87.5, 92.0, 78.3, 95.1],
        "Active": [True, False, True, True],
        "Role": ["admin", "user", "user", "viewer"],
        "FocusStart": ["08:30", "09:00", "10:15", "11:00"],
        "ReminderAt": ["2026-03-01T08:30", "2026-03-01T09:15", "2026-03-01T10:45", "2026-03-01T11:30"],
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
        "Bars": [[6, 4, 5, 7], [4, 5, 6, 4], [3, 4, 2, 5], [2, 3, 4, 6]],
        "Area": [[1, 3, 2, 5], [2, 4, 3, 6], [1, 2, 3, 3], [2, 3, 5, 7]],
        "Avatar": [
            "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=120&q=80",
            "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&q=80",
            "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=120&q=80",
            "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=120&q=80",
        ],
        "Link": ["https://fastlit.dev", "https://streamlit.io", "https://github.com", ""],
    }
)

st.code(
    """result = st.data_editor(
    df,
    num_rows="dynamic",
    column_config={
        "Name": st.column_config.TextColumn("Name", pinned="left", resizable=True),
        "Score": st.column_config.NumberColumn("Score /100", min_value=0, max_value=100, step=0.5),
        "Active": st.column_config.CheckboxColumn("Active"),
        "Role": st.column_config.SelectboxColumn("Role", options=["admin", "user", "viewer"]),
        "FocusStart": st.column_config.TimeColumn("Focus start", format="HH:mm"),
        "ReminderAt": st.column_config.DatetimeColumn("Reminder", format="YYYY-MM-DD HH:mm"),
        "Progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=100),
        "Tags": st.column_config.ListColumn("Tags"),
        "Segments": st.column_config.MultiselectColumn("Segments", options=["ops", "admin", "sales", "ml", "viz", "viewer", "beta"]),
        "Payload": st.column_config.JSONColumn("Payload"),
        "Trend": st.column_config.LineChartColumn("Trend", y_min=0, y_max=8),
        "Bars": st.column_config.BarChartColumn("Bars", y_min=0, y_max=8),
        "Area": st.column_config.AreaChartColumn("Area", y_min=0, y_max=8),
        "Avatar": st.column_config.ImageColumn("Avatar"),
        "Link": st.column_config.LinkColumn("URL", display_text="Open"),
    },
)""",
    language="python",
)

with st.container(border=True):
    cc_result = st.data_editor(
        CC_DF.copy(),
        num_rows="dynamic",
        column_config={
            "Name": st.column_config.TextColumn("Name", pinned="left", resizable=True),
            "Score": st.column_config.NumberColumn("Score /100", min_value=0, max_value=100, step=0.5),
            "Active": st.column_config.CheckboxColumn("Active"),
            "Role": st.column_config.SelectboxColumn("Role", options=["admin", "user", "viewer"]),
            "FocusStart": st.column_config.TimeColumn("Focus start", format="HH:mm"),
            "ReminderAt": st.column_config.DatetimeColumn("Reminder", format="YYYY-MM-DD HH:mm"),
            "Progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=100),
            "Tags": st.column_config.ListColumn("Tags"),
            "Segments": st.column_config.MultiselectColumn(
                "Segments",
                options=["ops", "admin", "sales", "ml", "viz", "viewer", "beta"],
            ),
            "Payload": st.column_config.JSONColumn("Payload"),
            "Trend": st.column_config.LineChartColumn("Trend", y_min=0, y_max=8),
            "Bars": st.column_config.BarChartColumn("Bars", y_min=0, y_max=8),
            "Area": st.column_config.AreaChartColumn("Area", y_min=0, y_max=8),
            "Avatar": st.column_config.ImageColumn("Avatar"),
            "Link": st.column_config.LinkColumn("URL", display_text="Open"),
        },
        height=420,
        key="cc_full_demo",
    )
    with st.expander("Edited data (JSON)", expanded=False):
        if hasattr(cc_result, "to_dict"):
            st.json(cc_result.to_dict(orient="records"))
        else:
            st.json(cc_result)


# ---------------------------------------------------------------------------
# 4. st.metric
# ---------------------------------------------------------------------------

st.header("st.metric()", divider="blue")
st.caption("KPI card with delta, built-in sparkline (area/line/bar), and custom formatting.")

with st.expander("📖 Parameters", expanded=False):
    st.markdown(
        """
| Parameter | Type | Description |
|-----------|------|-------------|
| `label` | str | Title |
| `value` | int / float / str | Main value |
| `delta` | int / float / str / None | Variation |
| `delta_color` | "normal"/"inverse"/"off" | Delta color |
| `delta_arrow` | "up"/"down"/"off" | Delta arrow |
| `format` | str | Value format (example: `"$,.0f"`) |
| `chart_data` | list | Sparkline points |
| `chart_type` | "line"/"area"/"bar" | Sparkline type |
| `border` | bool | Card border |
        """
    )

st.subheader("KPI dashboard - 4 columns")
st.code(
    """c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Revenue", 12_345, delta=5.2, format="$,.0f",
              chart_data=[9,10,12,11,14,16], chart_type="area", border=True)
with c2:
    st.metric("Users", 1_234, delta=120,
              chart_data=[980,1010,1100,1130,1200,1234], chart_type="line")
with c3:
    st.metric("Errors", 23, delta=-8, delta_color="inverse", delta_arrow="down",
              chart_data=[40,33,28,26,25,23], chart_type="bar")
with c4:
    st.metric("Status", "OK", delta="Stable", delta_arrow="off", border=True)""",
    language="python",
)

with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "Revenue",
            12_345,
            delta=5.2,
            format="$,.0f",
            chart_data=[9, 10, 12, 11, 14, 16],
            chart_type="area",
            border=True,
        )
    with c2:
        st.metric(
            "Users",
            1_234,
            delta=120,
            chart_data=[980, 1010, 1100, 1130, 1200, 1234],
            chart_type="line",
        )
    with c3:
        st.metric(
            "Errors",
            23,
            delta=-8,
            delta_color="inverse",
            delta_arrow="down",
            chart_data=[40, 33, 28, 26, 25, 23],
            chart_type="bar",
        )
    with c4:
        st.metric("Status", "OK", delta="Stable", delta_arrow="off", border=True)

st.subheader("Dynamic metrics")
st.caption("The slider updates the threshold and the derived metrics live through Fastlit live expressions.")
threshold = st.slider("Error alert threshold", 0, 100, 25, key="metric_threshold")

with st.container(border=True):
    current_errors = 23
    error_delta = current_errors - threshold
    is_healthy = current_errors <= threshold
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(
            "Errors (current)",
            current_errors,
            delta=error_delta,
            delta_color="inverse",
            chart_data=[40, 33, 28, 26, 25, current_errors],
            chart_type="area",
            border=True,
        )
    with m2:
        st.metric("Defined threshold", threshold, delta_arrow="off", border=True)
    with m3:
        status = (current_errors <= threshold).when("✅ OK", "⚠️ Over threshold")
        color = (current_errors <= threshold).when("normal", "inverse")
        st.metric("State", status, delta_color=color, border=True)
    st.progress(threshold, text=f"Live threshold: {threshold}")
    st.badge(
        is_healthy.when("Below threshold", "Above threshold"),
        color=is_healthy.when("green", "orange"),
        icon=is_healthy.when("✅", "⚠️"),
    )


# ---------------------------------------------------------------------------
# 5. st.json
# ---------------------------------------------------------------------------

st.header("st.json()", divider="blue")
st.caption("Interactive JSON viewer with expand/collapse, search, and copy path/value.")

with st.expander("📖 Parameters", expanded=False):
    st.markdown(
        """
| Parameter | Type | Description |
|-----------|------|-------------|
| `body` | dict / list / str | JSON data |
| `expanded` | bool / int | Auto-expanded depth |
| `width` | str / int | Width |
        """
    )

st.code(
    """st.json({
    "app": "Fastlit",
    "version": "0.2.0",
    "transport": {"protocol": "ws", "format": "Arrow IPC", "diff_patch": True},
    "features": ["diff_patch", "fragments", "oidc", "arrow_transport", "routing"],
    "config": {"port": 8501, "debug": False, "max_sessions": 0},
}, expanded=2)""",
    language="python",
)

with st.container(border=True):
    st.json(
        {
            "app": "Fastlit",
            "version": "0.2.0",
            "transport": {
                "protocol": "websocket",
                "format": "Arrow IPC",
                "diff_patch": True,
                "compression": "zlib (optional)",
            },
            "features": [
                "diff_patch",
                "fragments",
                "oidc_auth",
                "arrow_transport",
                "file_based_routing",
                "column_config_15_types",
            ],
            "config": {
                "port": 8501,
                "debug": False,
                "max_sessions": 0,
                "max_concurrent_runs": 4,
            },
            "column_config_types": {
                "shared_with_streamlit": [
                    "text",
                    "number",
                    "checkbox",
                    "selectbox",
                    "date",
                    "time",
                    "datetime",
                    "progress",
                    "link",
                    "image",
                    "line_chart",
                    "bar_chart",
                ],
                "fastlit_extras": ["area_chart", "list", "multiselect", "json"],
            },
        },
        expanded=2,
    )

st.subheader("Deep nested JSON")
st.code("""st.json(nested_data, expanded=1)  # first level only""", language="python")

with st.container(border=True):
    st.json(
        {
            "session_0": {
                "user": "alice@example.com",
                "state": {"counter": 42, "filters": ["active", "admin"]},
                "widget_store": {"slider_0": 70, "checkbox_0": True},
            },
            "session_1": {
                "user": "bob@example.com",
                "state": {"counter": 17, "filters": []},
                "widget_store": {"slider_0": 30, "checkbox_0": False},
            },
        },
        expanded=1,
    )


# ---------------------------------------------------------------------------
# 6. st.table
# ---------------------------------------------------------------------------

st.header("st.table()", divider="blue")
st.caption("Static table - ideal for small fixed datasets with no interaction.")

with st.expander("📖 Documentation", expanded=False):
    st.markdown(
        """
**Difference vs `st.dataframe()`**
- `st.table()`: static, no scroll, full HTML rendering
- `st.dataframe()`: virtualized, interactive, scroll, sorting, filtering

Use it for short read-only tables (typically under 30 rows).
        """
    )

st.code(
    """st.table({
    "Feature": ["UI diff/patch", "Arrow IPC", "Fragments", "OIDC Auth", "File routing"],
    "Fastlit": ["✅", "✅", "✅", "✅", "✅"],
    "Streamlit": ["❌", "⚠️ partial", "⚠️ experimental", "❌", "⚠️ flat only"],
})""",
    language="python",
)

with st.container(border=True):
    st.table(
        {
            "Feature": [
                "UI diff/patch",
                "Arrow IPC + windowing",
                "Fragments auto-refresh",
                "OIDC Auth",
                "File-based routing",
                "column_config extras",
                "Event coalescing",
                "ASGI + middleware",
            ],
            "Fastlit": ["✅", "✅", "✅", "✅", "✅", "✅ (15 types)", "✅", "✅"],
            "Streamlit": [
                "❌",
                "⚠️ Partial Arrow",
                "⚠️ Experimental",
                "❌ (Cloud only)",
                "⚠️ Flat only",
                "✅ (12 types)",
                "❌",
                "❌",
            ],
        }
    )


# ---------------------------------------------------------------------------
# 7. Arrow transport
# ---------------------------------------------------------------------------

st.header("Arrow IPC Transport", divider="blue")
st.caption(
    "For DataFrames with at least 1,000 rows, Fastlit automatically switches to "
    "Apache Arrow IPC (binary) instead of JSON. Typical gain: about 3x to 10x fewer bytes transferred."
)

with st.expander("🔧 Technical details", expanded=False):
    st.markdown(
        """
**How it works**
1. Initial load -> `arrowData` (base64 Arrow IPC) is embedded in the node props
2. Windowing on scroll -> `GET /_fastlit/dataframe/[id]?format=arrow` returns raw Arrow binary
3. Automatic fallback if `pyarrow` is unavailable -> regular JSON path

**Environment variables**
```bash
FASTLIT_ENABLE_ARROW_TRANSPORT=1   # enable it (default)
FASTLIT_DF_ARROW_MIN_ROWS=1000     # switch threshold (default: 1000)
FASTLIT_DF_ARROW_PREVIEW_ROWS=200  # initial preview rows before windowing
```
        """
    )

with st.container(border=True):
    import numpy as np
    row_count = 2000
    rng = np.random.default_rng(seed=42)
    large_df = pd.DataFrame(
        {
            "id": range(row_count),
            "value": rng.standard_normal(row_count).round(4),
            "label": [f"item_{i}" for i in range(row_count)],
            "score": rng.uniform(0, 100, row_count).round(2),
            "active": rng.integers(0, 2, row_count).astype(bool),
        }
    )
    transport_mode = "Arrow IPC (binary)" if row_count >= 1000 else "JSON (fallback)"
    st.dataframe(
        large_df,
        height=380,
        persist_view=False,
        key="arrow_demo_df",
    )
