"""Progressive loading demo for deferred fragments."""

from __future__ import annotations

import time

import pandas as pd

import fastlit as st

PAGE_CONFIG = {
    "title": "Progressive Loading",
    "icon": "⏳",
    "order": 125,
}


def _sales_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "week": ["W1", "W2", "W3", "W4", "W5", "W6"],
            "sales": [120, 146, 161, 155, 178, 194],
            "returns": [8, 7, 6, 9, 5, 4],
        }
    )


def _inventory_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sku": ["A-100", "A-220", "B-010", "B-114", "C-404", "D-210"],
            "warehouse": ["Paris", "Paris", "Lyon", "Berlin", "Madrid", "Rome"],
            "stock": [42, 18, 71, 9, 33, 57],
            "status": ["healthy", "low", "healthy", "critical", "healthy", "healthy"],
        }
    )


st.title("Progressive Loading")
st.caption(
    "This page keeps navigation responsive: the shell renders first, then slow "
    "sections hydrate in the background with local loaders."
)

st.info(
    "Wrap expensive sections in `@st.fragment(deferred=True, ...)` to prevent them "
    "from delaying the first useful paint."
)

summary_a, summary_b, summary_c = st.columns(3)
with summary_a:
    st.metric("Navigation shell", "Instant")
with summary_b:
    st.metric("Deferred sections", 2)
with summary_c:
    st.metric("Hydration mode", "Sequential")


@st.fragment(deferred=True, placeholder="skeleton", min_height=320)
def _sales_chart() -> None:
    with st.spinner("Loading sales chart..."):
        time.sleep(1.0)
        sales = _sales_frame()
    st.subheader("Deferred chart")
    st.caption("This chart hydrates after the page shell is already visible.")
    st.line_chart(sales.set_index("week")[["sales", "returns"]])


@st.fragment(deferred=True, placeholder="spinner", min_height=220)
def _inventory_table() -> None:
    with st.spinner("Loading inventory table..."):
        time.sleep(1.4)
        inventory = _inventory_frame()
    st.subheader("Deferred dataframe")
    st.caption("Tables and charts can hydrate independently with their own loader.")
    st.dataframe(inventory, hide_index=True, height=240)


st.header("Above-the-fold content", divider="blue")
st.write(
    "Everything in this section renders during the main page pass. The blocks "
    "below are deferred, so they no longer dominate navigation time."
)

_sales_chart()
_inventory_table()
