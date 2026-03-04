"""Data Display page — complete showcase of all data components in Fastlit."""

import pandas as pd
import fastlit as st

PAGE_CONFIG = {
    "title": "Data Display",
    "icon": "📊",
    "order": 40,
}

# ─────────────────────────────────────────────────────────────────────────────
# Shared datasets
# ─────────────────────────────────────────────────────────────────────────────

USERS_DATA = {
    "Name":   ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
    "Age":    [25, 30, 35, 28, 32],
    "City":   ["Paris", "London", "Berlin", "Madrid", "Rome"],
    "Score":  [85.5, 92.0, 78.5, 95.0, 88.5],
    "Active": [True, False, True, True, False],
    "Joined": ["2024-01-15", "2023-06-20", "2024-03-01", "2023-11-10", "2024-02-28"],
}

USERS_DF = pd.DataFrame(USERS_DATA)

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────

st.title("📊 Data Display")
st.caption(
    "Tous les composants de données de Fastlit : DataFrame virtualisé, "
    "Data Editor, Metrics, JSON et Table statique."
)

st.code("""USERS_DATA = {
    "Name":   ["Alice Martin", "Bob Johnson", "Charlie Lee", "Diana Chen", "Eve Wilson"],
    "Age":    [25, 30, 35, 28, 32],
    "City":   ["Paris", "London", "Berlin", "Madrid", "Rome"],
    "Score":  [85.5, 92.0, 78.5, 95.0, 88.5],
    "Active": [True, False, True, True, False],
    "Joined": ["2024-01-15", "2023-06-20", "2024-03-01", "2023-11-10", "2024-02-28"],
}
        
USERS_DF = pd.DataFrame(USERS_DATA)
""", language="python")


# ─────────────────────────────────────────────────────────────────────────────
# 1. st.dataframe — base
# ─────────────────────────────────────────────────────────────────────────────

st.header("st.dataframe()", divider="blue")
st.caption("DataFrame virtualisé avec toolbar, tri, filtre, resize, export CSV.")

with st.expander("📖 Paramètres", expanded=False):
    st.markdown("""
| Paramètre | Type | Description |
|-----------|------|-------------|
| `data` | DataFrame / dict / list | Données à afficher |
| `height` | int / "auto" | Hauteur en pixels |
| `width` | int / "stretch" / "content" | Largeur |
| `hide_index` | bool | Masquer l'index |
| `column_order` | list[str] | Ordre des colonnes |
| `column_config` | dict | Config par colonne |
| `toolbar` | bool | Afficher la barre d'outils |
| `downloadable` | bool | Bouton export CSV |
| `persist_view` | bool | Mémoriser tri/filtre/scroll |
| `on_select` | "rerun" / Callable / None | Mode sélection |
| `selection_mode` | "single-row" / "multi-row" | Mode de sélection |
| `key` | str | Clé stable |

**Retourne** : `DataframeSelection` si `on_select` est défini, sinon `None`.
    """)

# 1a — Affichage simple
st.subheader("Affichage simple")
st.code("""st.dataframe(df, height=260, hide_index=True)""", language="python")
with st.container(border=True):
    st.dataframe(USERS_DF, height=260, hide_index=True)

# 1b — Avec column_config
st.subheader("Avec column_config")
st.code("""st.dataframe(
    df,
    height=280,
    column_config={
        "Name":   st.column_config.TextColumn("Nom", width="medium", resizable=True, pinned="left"),
        "Score":  st.column_config.NumberColumn("Score /100", format="%.1f", resizable=True),
        "Active": st.column_config.CheckboxColumn("Actif"),
        "Joined": st.column_config.DateColumn("Inscrit le"),
    },
)""", language="python")
with st.container(border=True):
    st.dataframe(
        USERS_DF,
        height=280,
        column_config={
            "Name":   st.column_config.TextColumn("Nom", width="medium", resizable=True, pinned="left"),
            "Score":  st.column_config.NumberColumn("Score /100", format="%.1f", resizable=True),
            "Active": st.column_config.CheckboxColumn("Actif"),
            "Joined": st.column_config.DateColumn("Inscrit le"),
        },
    )

# 1c — Sélection interactive
st.subheader("Sélection interactive (`on_select`)")
st.caption("Clique sur une ou plusieurs lignes — les indices sélectionnés remontent en Python.")
st.code("""selection = st.dataframe(
    df,
    on_select="rerun",
    selection_mode="multi-row",
    height=280,
    key="df_select",
)
st.write("Lignes sélectionnées :", selection.rows)""", language="python")
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
        st.success(f"Lignes {sel.rows} → {', '.join(selected_users)}")
    else:
        st.info("Aucune ligne sélectionnée. Clique sur les cases à cocher.")

# 1d — Single-row + callback
st.subheader("Sélection mono-ligne (`single-row`)")
st.code("""def on_row_selected(s):
    st.session_state.selected_user = s.rows[0] if s.rows else None

selection = st.dataframe(df, on_select=on_row_selected, selection_mode="single-row", height=280)""", language="python")
with st.container(border=True):
    if "selected_user_idx" not in st.session_state:
        st.session_state.selected_user_idx = None

    def _on_single_select(s):
        st.session_state.selected_user_idx = s.rows[0] if s.rows else None

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
        cols[0].metric("Nom", USERS_DATA["Name"][idx])
        cols[1].metric("Ville", USERS_DATA["City"][idx])
        cols[2].metric("Score", USERS_DATA["Score"][idx])
        cols[3].metric("Actif", "✅" if USERS_DATA["Active"][idx] else "❌")
    else:
        st.info("Sélectionne une ligne pour voir le détail.")

# ─────────────────────────────────────────────────────────────────────────────
# 2. st.data_editor — édition simple
# ─────────────────────────────────────────────────────────────────────────────

st.header("st.data_editor()", divider="blue")
st.caption("Grille éditable avec ajout/suppression de lignes, persist_view, resize, colonnes épinglées.")

with st.expander("📖 Paramètres", expanded=False):
    st.markdown("""
| Paramètre | Type | Description |
|-----------|------|-------------|
| `data` | DataFrame / dict / list | Données initiales |
| `num_rows` | "fixed" / "dynamic" | Autoriser l'ajout de lignes |
| `disabled` | bool / list[str] | Colonnes ou tout désactivé |
| `column_config` | dict | Config par colonne |
| `height` | int | Hauteur |
| `on_change` | Callable | Callback à chaque édition |
| `persist_view` | bool | Mémoriser l'état visuel |

**Retourne** : DataFrame (ou dict/list selon l'entrée) avec les modifications.
    """)

st.subheader("Édition basique avec lignes dynamiques")
st.code("""edited = st.data_editor(
    df,
    num_rows="dynamic",
    column_config={
        "Name":   st.column_config.TextColumn("Nom", pinned="left", resizable=True),
        "Score":  st.column_config.NumberColumn("Score", min_value=0, max_value=100, step=0.5),
        "Active": st.column_config.CheckboxColumn("Actif"),
        "Joined": st.column_config.DateColumn("Inscrit le"),
    },
    key="editor_basic",
)
st.write(f"{len(edited)} lignes • {edited['Active'].sum()} actifs")""", language="python")

with st.container(border=True):
    edited_basic = st.data_editor(
        USERS_DF.copy(),
        num_rows="dynamic",
        column_config={
            "Name":   st.column_config.TextColumn("Nom", pinned="left", resizable=True),
            "Score":  st.column_config.NumberColumn("Score", min_value=0, max_value=100, step=0.5),
            "Active": st.column_config.CheckboxColumn("Actif"),
            "Joined": st.column_config.DateColumn("Inscrit le"),
        },
        height=320,
        key="editor_basic",
    )
    n_active = sum(bool(v) for v in edited_basic["Active"]) if hasattr(edited_basic, "__getitem__") else 0
    st.caption(f"{len(edited_basic)} lignes · {n_active} actifs")

# ─────────────────────────────────────────────────────────────────────────────
# 3. column_config — tous les types
# ─────────────────────────────────────────────────────────────────────────────

st.header("column_config — les 15 types", divider="blue")
st.caption(
    "Fastlit supporte 15 types de colonnes, vs 12 pour Streamlit. "
    "Les 3 extras : `ListColumn`, `MultiselectColumn`, `JSONColumn`."
)

with st.expander("📋 Tableau des types", expanded=True):
    st.markdown("""
| Type | Éditeur | Extra vs Streamlit |
|------|---------|-------------------|
| `TextColumn` | Input texte (+ regex, maxChars) | |
| `NumberColumn` | Input numérique (min/max/step/format) | |
| `CheckboxColumn` | Toggle booléen | |
| `SelectboxColumn` | Dropdown | |
| `DateColumn` | Calendrier | |
| `TimeColumn` | Sélecteur heure/minute/seconde | |
| `DatetimeColumn` | Calendrier + heure | |
| `ProgressColumn` | Barre + slider dans popover | |
| `LinkColumn` | URL + bouton open | |
| `ImageColumn` | Avatar + input URL | |
| `LineChartColumn` | Sparkline (lecture seule) | |
| `BarChartColumn` | Spark bar chart (lecture seule) | |
| `AreaChartColumn` | Spark area chart (lecture seule) | |
| `ListColumn` | Textarea JSON dans popover | ✅ |
| `MultiselectColumn` | Checkboxes dans popover | ✅ |
| `JSONColumn` | Textarea JSON formaté | ✅ |
    """)

# Dataset complet pour la démo
_CC_DF = pd.DataFrame({
    "Name":       ["Alice", "Bob", "Charlie", "Diana"],
    "Score":      [87.5, 92.0, 78.3, 95.1],
    "Active":     [True, False, True, True],
    "Role":       ["admin", "user", "user", "viewer"],
    "FocusStart": ["08:30", "09:00", "10:15", "11:00"],
    "ReminderAt": ["2026-03-01T08:30", "2026-03-01T09:15", "2026-03-01T10:45", "2026-03-01T11:30"],
    "Progress":   [75, 45, 90, 60],
    "Tags":       [["ops", "admin"], ["sales"], ["ml", "viz"], ["viewer", "beta"]],
    "Segments":   [["ops", "admin"], ["sales"], ["ml", "viz"], ["viewer", "beta"]],
    "Payload":    [
        {"tier": "gold", "quota": 12},
        {"tier": "silver", "quota": 8},
        {"tier": "bronze", "quota": 5},
        {"tier": "beta", "quota": 2},
    ],
    "Trend":      [[3, 4, 5, 6], [4, 4, 5, 7], [2, 3, 3, 4], [1, 2, 4, 6]],
    "Bars":       [[6, 4, 5, 7], [4, 5, 6, 4], [3, 4, 2, 5], [2, 3, 4, 6]],
    "Area":       [[1, 3, 2, 5], [2, 4, 3, 6], [1, 2, 3, 3], [2, 3, 5, 7]],
    "Avatar":     [
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=120&q=80",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&q=80",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=120&q=80",
        "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=120&q=80",
    ],
    "Link":       ["https://fastlit.dev", "https://streamlit.io", "https://github.com", ""],
})

st.code("""result = st.data_editor(
    df,
    num_rows="dynamic",
    column_config={
        "Name":       st.column_config.TextColumn("Nom", pinned="left", resizable=True),
        "Score":      st.column_config.NumberColumn("Score /100", min_value=0, max_value=100, step=0.5),
        "Active":     st.column_config.CheckboxColumn("Actif"),
        "Role":       st.column_config.SelectboxColumn("Rôle", options=["admin","user","viewer"]),
        "FocusStart": st.column_config.TimeColumn("Début focus", format="HH:mm"),
        "ReminderAt": st.column_config.DatetimeColumn("Rappel", format="YYYY-MM-DD HH:mm"),
        "Progress":   st.column_config.ProgressColumn("Progression", min_value=0, max_value=100),
        "Tags":       st.column_config.ListColumn("Tags"),
        "Segments":   st.column_config.MultiselectColumn("Segments", options=["ops","admin","sales","ml","viz","viewer","beta"]),
        "Payload":    st.column_config.JSONColumn("Payload"),
        "Trend":      st.column_config.LineChartColumn("Tendance", y_min=0, y_max=8),
        "Bars":       st.column_config.BarChartColumn("Bars", y_min=0, y_max=8),
        "Area":       st.column_config.AreaChartColumn("Area", y_min=0, y_max=8),
        "Avatar":     st.column_config.ImageColumn("Avatar"),
        "Link":       st.column_config.LinkColumn("URL", display_text="Ouvrir"),
    },
)""", language="python")

with st.container(border=True):
    _cc_result = st.data_editor(
        _CC_DF.copy(),
        num_rows="dynamic",
        column_config={
            "Name":       st.column_config.TextColumn("Nom", pinned="left", resizable=True),
            "Score":      st.column_config.NumberColumn("Score /100", min_value=0, max_value=100, step=0.5),
            "Active":     st.column_config.CheckboxColumn("Actif"),
            "Role":       st.column_config.SelectboxColumn("Rôle", options=["admin", "user", "viewer"]),
            "FocusStart": st.column_config.TimeColumn("Début focus", format="HH:mm"),
            "ReminderAt": st.column_config.DatetimeColumn("Rappel", format="YYYY-MM-DD HH:mm"),
            "Progress":   st.column_config.ProgressColumn("Progression", min_value=0, max_value=100),
            "Tags":       st.column_config.ListColumn("Tags"),
            "Segments":   st.column_config.MultiselectColumn(
                "Segments",
                options=["ops", "admin", "sales", "ml", "viz", "viewer", "beta"],
            ),
            "Payload":    st.column_config.JSONColumn("Payload"),
            "Trend":      st.column_config.LineChartColumn("Tendance", y_min=0, y_max=8),
            "Bars":       st.column_config.BarChartColumn("Bars", y_min=0, y_max=8),
            "Area":       st.column_config.AreaChartColumn("Area", y_min=0, y_max=8),
            "Avatar":     st.column_config.ImageColumn("Avatar"),
            "Link":       st.column_config.LinkColumn("URL", display_text="Ouvrir"),
        },
        height=420,
        key="cc_full_demo",
    )
    with st.expander("Données éditées (JSON)", expanded=False):
        if hasattr(_cc_result, "to_dict"):
            st.json(_cc_result.to_dict(orient="records"))
        else:
            st.json(_cc_result)

# ─────────────────────────────────────────────────────────────────────────────
# 4. st.metric()
# ─────────────────────────────────────────────────────────────────────────────

st.header("st.metric()", divider="blue")
st.caption("Carte KPI avec delta, sparkline intégrée (area/line/bar) et format personnalisé.")

with st.expander("📖 Paramètres", expanded=False):
    st.markdown("""
| Paramètre | Type | Description |
|-----------|------|-------------|
| `label` | str | Titre |
| `value` | int / float / str | Valeur principale |
| `delta` | int / float / str / None | Variation |
| `delta_color` | "normal"/"inverse"/"off" | Couleur du delta |
| `delta_arrow` | "up"/"down"/"off" | Flèche du delta |
| `format` | str | Format de la valeur (ex: `"$,.0f"`) |
| `chart_data` | list | Points pour le sparkline |
| `chart_type` | "line"/"area"/"bar" | Type de sparkline |
| `border` | bool | Bordure autour de la carte |
    """)

st.subheader("KPI dashboard — 4 colonnes")
st.code("""c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Revenu", 12_345, delta=5.2, format="$,.0f",
              chart_data=[9,10,12,11,14,16], chart_type="area", border=True)
with c2:
    st.metric("Utilisateurs", 1_234, delta=120,
              chart_data=[980,1010,1100,1130,1200,1234], chart_type="line")
with c3:
    st.metric("Erreurs", 23, delta=-8, delta_color="inverse", delta_arrow="down",
              chart_data=[40,33,28,26,25,23], chart_type="bar")
with c4:
    st.metric("Statut", "OK", delta="Stable", delta_arrow="off", border=True)""", language="python")

with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(
            "Revenu", 12_345, delta=5.2, format="$,.0f",
            chart_data=[9, 10, 12, 11, 14, 16], chart_type="area", border=True,
        )
    with c2:
        st.metric(
            "Utilisateurs", 1_234, delta=120,
            chart_data=[980, 1010, 1100, 1130, 1200, 1234], chart_type="line",
        )
    with c3:
        st.metric(
            "Erreurs", 23, delta=-8, delta_color="inverse", delta_arrow="down",
            chart_data=[40, 33, 28, 26, 25, 23], chart_type="bar",
        )
    with c4:
        st.metric("Statut", "OK", delta="Stable", delta_arrow="off", border=True)

st.subheader("Métriques dynamiques")
st.caption("Le slider met à jour le seuil et les métriques dérivées en direct grâce aux live expressions Fastlit.")
threshold = st.slider("Seuil d'alerte erreurs", 0, 100, 25, key="metric_threshold")

with st.container(border=True):
    current_errors = 23
    error_delta = current_errors - threshold
    is_healthy = current_errors <= threshold
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(
            "Erreurs (actuel)", current_errors,
            delta=error_delta,
            delta_color="inverse",
            chart_data=[40, 33, 28, 26, 25, current_errors],
            chart_type="area",
            border=True,
        )
    with m2:
        st.metric("Seuil défini", threshold, delta_arrow="off", border=True)
    with m3:
        status = (current_errors <= threshold).when("✅ OK", "⚠️ Dépassé")
        color = (current_errors <= threshold).when("normal", "inverse")
        st.metric("État", status, delta_color=color, border=True)
    st.progress(threshold, text=f"Seuil live: {threshold}")
    st.badge(
        is_healthy.when("Sous le seuil", "Au-dessus du seuil"),
        color=is_healthy.when("green", "orange"),
        icon=is_healthy.when("✅", "⚠️"),
    )

# ─────────────────────────────────────────────────────────────────────────────
# 5. st.json()
# ─────────────────────────────────────────────────────────────────────────────

st.header("st.json()", divider="blue")
st.caption("Affichage JSON interactif — expand/collapse, recherche, copy path/value.")

with st.expander("📖 Paramètres", expanded=False):
    st.markdown("""
| Paramètre | Type | Description |
|-----------|------|-------------|
| `body` | dict / list / str | Données JSON |
| `expanded` | bool / int | Profondeur auto-dépliée |
| `width` | str / int | Largeur |
    """)

st.code("""st.json({
    "app": "Fastlit",
    "version": "0.2.0",
    "transport": {"protocol": "ws", "format": "Arrow IPC", "diff_patch": True},
    "features": ["diff_patch", "fragments", "oidc", "arrow_transport", "routing"],
    "config": {"port": 8501, "debug": False, "max_sessions": 0},
}, expanded=2)""", language="python")

with st.container(border=True):
    st.json({
        "app": "Fastlit",
        "version": "0.2.0",
        "transport": {
            "protocol": "websocket",
            "format": "Arrow IPC",
            "diff_patch": True,
            "compression": "zlib (optionnel)",
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
            "shared_with_streamlit": ["text", "number", "checkbox", "selectbox", "date", "time",
                                      "datetime", "progress", "link", "image", "line_chart", "bar_chart"],
            "fastlit_extras": ["area_chart", "list", "multiselect", "json"],
        },
    }, expanded=2)

st.subheader("JSON imbriqué profond")
st.code("""st.json(nested_data, expanded=1)  # Premier niveau seulement""", language="python")

with st.container(border=True):
    st.json({
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
    }, expanded=1)

# ─────────────────────────────────────────────────────────────────────────────
# 6. st.table()
# ─────────────────────────────────────────────────────────────────────────────

st.header("st.table()", divider="blue")
st.caption("Table statique — idéale pour des petits datasets fixes, sans interaction.")

with st.expander("📖 Documentation", expanded=False):
    st.markdown("""
**Différence avec `st.dataframe()`**
- `st.table()` : statique, pas de scroll, rendu HTML complet
- `st.dataframe()` : virtualisé, interactif, scroll, tri, filtre

À utiliser pour des tableaux courts (< 30 lignes) affichés en lecture seule.
    """)

st.code("""st.table({
    "Fonctionnalité":  ["Diff/patch UI", "Arrow IPC", "Fragments", "OIDC Auth", "File routing"],
    "Fastlit":         ["✅", "✅", "✅", "✅", "✅"],
    "Streamlit":       ["❌", "⚠️ partiel", "⚠️ expérimental", "❌", "⚠️ plat"],
})""", language="python")

with st.container(border=True):
    st.table({
        "Fonctionnalité":     ["Diff/patch UI", "Arrow IPC + windowing", "Fragments auto-refresh",
                               "OIDC Auth", "File-based routing", "column_config extras",
                               "Event coalescing", "ASGI + middleware"],
        "Fastlit":            ["✅", "✅", "✅", "✅", "✅", "✅ (15 types)", "✅", "✅"],
        "Streamlit":          ["❌", "⚠️ Arrow partiel", "⚠️ Expérimental",
                               "❌ (Cloud only)", "⚠️ Plat seulement", "✅ (12 types)", "❌", "❌"],
    })

# ─────────────────────────────────────────────────────────────────────────────
# 7. Arrow transport — démo large dataset
# ─────────────────────────────────────────────────────────────────────────────

st.header("Arrow IPC Transport", divider="blue")
st.caption(
    "Pour les DataFrames ≥ 1 000 lignes, Fastlit bascule automatiquement sur Apache Arrow IPC "
    "(binaire) au lieu de JSON. Gain : ~3–10× moins de bytes transférés."
)

with st.expander("🔧 Détails technique", expanded=False):
    st.markdown("""
**Fonctionnement :**
1. Initial load → `arrowData` (base64 Arrow IPC) dans les props du nœud
2. Windowing (scroll) → `GET /_fastlit/dataframe/[id]?format=arrow` retourne du binaire Arrow pur
3. Fallback automatique si `pyarrow` non disponible → JSON classique

**Variables d'environnement :**
```
FASTLIT_ENABLE_ARROW_TRANSPORT=1   # activer (défaut)
FASTLIT_DF_ARROW_MIN_ROWS=1000     # seuil de bascule (défaut: 1000)
FASTLIT_DF_ARROW_PREVIEW_ROWS=200  # lignes initiales avant windowing
```
    """)

n_rows = st.slider("Nombre de lignes à générer", 500, 10_000, 2_000, step=500, key="arrow_demo_rows")

st.code(f"""import numpy as np
import pandas as pd

# Génère {n_rows} lignes — Arrow s'active automatiquement au-dessus de 1 000
large_df = pd.DataFrame({{
    "id":    range({n_rows}),
    "value": np.random.randn({n_rows}),
    "label": [f"item_{{i}}" for i in range({n_rows})],
    "score": np.random.uniform(0, 100, {n_rows}),
}})

st.dataframe(large_df, height=400)""", language="python")

with st.container(border=True):
    import numpy as np
    _rng = np.random.default_rng(seed=42)
    large_df = pd.DataFrame({
        "id":    range(n_rows),
        "value": _rng.standard_normal(n_rows).round(4),
        "label": [f"item_{i}" for i in range(n_rows)],
        "score": _rng.uniform(0, 100, n_rows).round(2),
        "active": _rng.integers(0, 2, n_rows).astype(bool),
    })
    transport_mode = "Arrow IPC (binaire)" if n_rows >= 1000 else "JSON (fallback)"
    st.info(f"**{n_rows} lignes** · Transport : `{transport_mode}`")
    st.dataframe(large_df, height=380)
