# =========================================================
# STREAMLIT APP
# =========================================================

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
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
# LOAD DATA
# =========================================================

OUTPUT_FILE = Path(
    "output/enriched_stock_data.xlsx"
)

# =========================================================
# SAFE LOADER
# =========================================================

@st.cache_data(show_spinner=False)

def load_data():

    try:

        if not OUTPUT_FILE.exists():

            return pd.DataFrame()

        df = pd.read_excel(
            OUTPUT_FILE
        )

        # =============================================
        # COLUMN CLEANING
        # =============================================

        df.columns = [

            str(col).strip()
            for col in df.columns

        ]

        # =============================================
        # REQUIRED COLUMNS
        # =============================================

        required_columns = {

            "Stock": "",
            "Sector": "Unknown",
            "Trade Signal": "WATCH",
            "Institutional Score": 0,
            "Current Price": 0,
            "Confidence": 0

        }

        for col, default in required_columns.items():

            if col not in df.columns:

                df[col] = default

        # =============================================
        # CLEAN NUMERIC COLUMNS
        # =============================================

        numeric_cols = [

            "Institutional Score",
            "Current Price",
            "Confidence"

        ]

        for col in numeric_cols:

            df[col] = pd.to_numeric(

                df[col],
                errors="coerce"

            ).fillna(0)

        # =============================================
        # CLEAN TRADE SIGNALS
        # =============================================

        df["Trade Signal"] = (

            df["Trade Signal"]

            .astype(str)

            .str.upper()

            .str.strip()

        )

        # =============================================
        # ALLOWED SIGNALS
        # =============================================

        allowed_signals = [

            "STRONG BUY",
            "BUY",
            "WATCH",
            "HOLD",
            "AVOID"

        ]

        df.loc[
            ~df["Trade Signal"].isin(
                allowed_signals
            ),
            "Trade Signal"
        ] = "WATCH"

        return df

    except Exception as e:

        st.error(
            f"Data Loading Error : {e}"
        )

        return pd.DataFrame()

# =========================================================
# LOAD
# =========================================================

df = load_data()

# =========================================================
# EMPTY CHECK
# =========================================================

if df.empty:

    st.warning(
        "No institutional data available."
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

# =========================================================
# TRADE SIGNAL FILTER
# =========================================================

signal_order = [

    "STRONG BUY",
    "BUY",
    "WATCH",
    "HOLD",
    "AVOID"

]

selected_trade_signal = st.sidebar.multiselect(

    "Trade Signal",

    options=signal_order,

    default=[]

)

# =========================================================
# SECTOR FILTER
# =========================================================

all_sectors = sorted(

    df["Sector"]
    .dropna()
    .astype(str)
    .unique()

)

selected_sectors = st.sidebar.multiselect(

    "Sector",

    options=all_sectors,

    default=[]

)

# =========================================================
# FILTERING
# =========================================================

filtered_df = df.copy()

# =========================================================
# SEARCH FILTER
# =========================================================

if search_stock:

    filtered_df = filtered_df[

        filtered_df["Stock"]

        .astype(str)

        .str.upper()

        .str.contains(

            search_stock.upper(),
            na=False

        )

    ]

# =========================================================
# SIGNAL FILTER
# =========================================================

if len(selected_trade_signal) > 0:

    filtered_df = filtered_df[

        filtered_df["Trade Signal"]

        .isin(selected_trade_signal)

    ]

# =========================================================
# SECTOR FILTER
# =========================================================

if len(selected_sectors) > 0:

    filtered_df = filtered_df[

        filtered_df["Sector"]

        .isin(selected_sectors)

    ]

# =========================================================
# HEADER
# =========================================================

st.title(
    "🏦 Institutional Quant Platform"
)

st.caption(
    "AI Powered Institutional Stock Analytics"
)

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
# TABLE
# =========================================================

st.markdown("---")

st.subheader(
    "Institutional Stock Table"
)

display_columns = [

    "Stock",
    "Sector",
    "Trade Signal",
    "Institutional Score",
    "Confidence",
    "Current Price"

]

available_columns = [

    col for col in display_columns
    if col in filtered_df.columns

]

st.dataframe(

    filtered_df[
        available_columns
    ]

    .sort_values(

        by="Institutional Score",
        ascending=False

    ),

    use_container_width=True,
    height=700

)

# =========================================================
# SIGNAL DISTRIBUTION
# =========================================================

st.markdown("---")

st.subheader(
    "Trade Signal Distribution"
)

signal_counts = (

    filtered_df[
        "Trade Signal"
    ]

    .value_counts()

    .reindex(signal_order)

    .fillna(0)

)

st.bar_chart(
    signal_counts
)
