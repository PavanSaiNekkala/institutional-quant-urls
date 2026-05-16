# =========================================================
# streamlit_app.py
# FINAL PRODUCTION SAFE VERSION
# =========================================================

import warnings
warnings.filterwarnings("ignore")

# =========================================================
# IMPORTS
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import duckdb
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Institutional Quant Platform",
    page_icon="📈",
    layout="wide"
)

# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #0E1117;
    }

    .stDataFrame {
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# TITLE
# =========================================================

st.title("📈 Institutional Quant Platform")

st.caption(
    "AI Powered Institutional Stock Analytics"
)

# =========================================================
# DATABASE
# =========================================================

DATABASE_PATH = (
    "database/institutional_quant.db"
)

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data(ttl=1800)
def load_data():

    try:

        if not Path(DATABASE_PATH).exists():

            return pd.DataFrame()

        conn = duckdb.connect(
            DATABASE_PATH,
            read_only=True
        )

        tables = conn.execute(
            "SHOW TABLES"
        ).fetchdf()

        if tables.empty:

            conn.close()

            return pd.DataFrame()

        table_name = tables.iloc[0, 0]

        query = f"""
        SELECT *
        FROM {table_name}
        """

        df = conn.execute(
            query
        ).fetchdf()

        conn.close()

        # =============================================
        # STANDARDIZE COLUMN NAMES
        # =============================================

        df.columns = [

            str(col).strip()
            for col in df.columns

        ]

        # =============================================
        # REQUIRED COLUMNS
        # =============================================

        required_columns = {

            "Stock": "UNKNOWN",
            "Sector": "Other",
            "Institutional Score": 0,
            "Confidence": 0,
            "Current Price": 0,
            "Trade Signal": "HOLD"

        }

        for col, default_value in required_columns.items():

            if col not in df.columns:

                df[col] = default_value

        # =============================================
        # CLEAN SECTOR
        # =============================================

        df["Sector"] = (

            df["Sector"]

            .fillna("Other")

            .astype(str)

        )

        return df

    except Exception as e:

        st.error(
            f"Database Load Failed : {e}"
        )

        return pd.DataFrame()

# =========================================================
# LOAD DATAFRAME
# =========================================================

df = load_data()

# =========================================================
# EMPTY CHECK
# =========================================================

if df.empty:

    st.warning(
        "No data available."
    )

    st.stop()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "Institutional Controls"
)

# =========================================================
# SEARCH
# =========================================================

search_stock = st.sidebar.text_input(
    "Search Stock"
)

if search_stock:

    df = df[
        df["Stock"]
        .astype(str)
        .str.contains(
            search_stock,
            case=False,
            na=False
        )
    ]

# =========================================================
# TRADE SIGNAL FILTER
# =========================================================

trade_options = sorted(

    df["Trade Signal"]
    .astype(str)
    .unique()

)

selected_trade_signal = st.sidebar.multiselect(

    "Trade Signal",

    options=trade_options,

    default=trade_options

)

filtered_df = df[

    df["Trade Signal"]
    .isin(selected_trade_signal)

]

# =========================================================
# METRICS
# =========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Stocks",
        len(filtered_df)
    )

with col2:

    st.metric(
        "Avg Institutional Score",

        round(

            filtered_df[
                "Institutional Score"
            ].mean(),

            2

        )
    )

with col3:

    st.metric(
        "Avg Confidence",

        round(

            filtered_df[
                "Confidence"
            ].mean(),

            2

        )
    )

with col4:

    st.metric(
        "Avg Price",

        round(

            filtered_df[
                "Current Price"
            ].mean(),

            2

        )
    )

# =========================================================
# DATAFRAME
# =========================================================

st.markdown("---")

st.subheader(
    "Institutional Stock Table"
)

st.dataframe(

    filtered_df,

    use_container_width=True,

    height=700

)

# =========================================================
# SECTOR SAFETY
# =========================================================

if "Sector" not in filtered_df.columns:

    filtered_df["Sector"] = "Other"

filtered_df["Sector"] = (

    filtered_df["Sector"]

    .fillna("Other")

    .astype(str)

)

# =========================================================
# HEATMAP
# =========================================================

st.markdown("---")

st.subheader(
    "Institutional Sector Heatmap"
)

try:

    heatmap_df = (

        filtered_df

        .groupby("Sector", dropna=False)

        .agg({

            "Institutional Score": "mean",
            "Confidence": "mean",
            "Current Price": "mean",
            "Stock": "count"

        })

        .reset_index()

    )

    heatmap_df.columns = [

        "Sector",
        "Avg Institutional Score",
        "Avg Confidence",
        "Avg Price",
        "Stock Count"

    ]

    heatmap_df["Capital Flow Score"] = (

        heatmap_df[
            "Avg Institutional Score"
        ]

        *

        heatmap_df[
            "Avg Confidence"
        ]

    )

    fig_heatmap = px.treemap(

        heatmap_df,

        path=["Sector"],

        values="Stock Count",

        color="Capital Flow Score",

        hover_data=[

            "Avg Institutional Score",
            "Avg Confidence",
            "Avg Price"

        ],

        color_continuous_scale="RdYlGn"

    )

    fig_heatmap.update_layout(
        height=700
    )

    st.plotly_chart(

        fig_heatmap,

        use_container_width=True

    )

except Exception as e:

    st.error(
        f"Heatmap Failed : {e}"
    )

# =========================================================
# TOP STOCKS
# =========================================================

st.markdown("---")

st.subheader(
    "Top Institutional Picks"
)

top_df = (

    filtered_df

    .sort_values(

        by="Institutional Score",

        ascending=False

    )

    .head(25)

)

fig_bar = px.bar(

    top_df,

    x="Stock",

    y="Institutional Score",

    color="Confidence"

)

fig_bar.update_layout(
    height=600
)

st.plotly_chart(

    fig_bar,

    use_container_width=True

)

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.success(
    "Quant Engine Active"
)
