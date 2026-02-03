"""DataFrame demo — virtualized scrolling with large datasets."""

import fastlit as st

st.title("DataFrame Demo")

st.markdown("### Virtualized DataFrame with TanStack Virtual")

# Number of rows slider
n = st.slider("Number of rows", min_value=10, max_value=10000, value=1000, step=100)

# Generate sample data
try:
    import pandas as pd
    import numpy as np

    # Create a large DataFrame
    df = pd.DataFrame({
        "id": range(n),
        "name": [f"Item {i}" for i in range(n)],
        "value": np.random.randn(n).round(4),
        "quantity": np.random.randint(1, 100, n),
        "active": np.random.choice([True, False], n),
        "category": np.random.choice(["A", "B", "C", "D"], n),
    })

    st.markdown(f"Displaying **{n:,}** rows with virtualization:")
    st.dataframe(df, height=400)

    st.divider()

    st.markdown("### Small static table")
    st.table(df.head(5))

except ImportError:
    st.markdown("**Note:** Install pandas and numpy for the full demo:")
    st.markdown("```pip install pandas numpy```")

    # Fallback with dict data
    data = {
        "id": list(range(n)),
        "name": [f"Item {i}" for i in range(n)],
        "value": [i * 1.5 for i in range(n)],
    }
    st.dataframe(data, height=400)
