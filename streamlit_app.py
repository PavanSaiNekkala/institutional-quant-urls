# =========================================================
# LIGHTWEIGHT CLOUD STREAMLIT APP
# =========================================================

# =========================================================
# IMPORTS
# =========================================================

import streamlit as st
import pandas as pd
import duckdb

from pathlib import Path
from datetime import datetime

from analytics.trade_decision_engine import (

    build_trade_decisions,

    calculate_market_regime
)

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(

    page_title="Institutional Quant Platform",

    page_icon="📈",

    layout="wide"
)

# =========================================================
# SECTOR NORMALIZATION
# =========================================================

def normalize_sector(sector):

    if pd.isna(sector):

        return "Other"

    sector = str(sector).strip().lower()

    sector_mapping = {

        "it services": "Technology",
        "software": "Technology",
        "information technology": "Technology",
        "tech": "Technology",

        "banks": "Banking",
        "banking": "Banking",

        "financial services": "Financial Services",
        "finance": "Financial Services",
        "nbfc": "Financial Services",

        "pharma": "Healthcare",
        "pharmaceuticals": "Healthcare",
        "healthcare": "Healthcare",

        "oil & gas": "Energy",
        "energy": "Energy",
        "power": "Energy",

        "fmcg": "Consumer",
        "consumer goods": "Consumer",

        "automobile": "Automobile",
        "auto": "Automobile",

        "capital goods": "Industrials",
        "engineering": "Industrials",

        "metals": "Metals & Mining",
        "steel": "Metals & Mining",

        "cement": "Materials",
        "chemicals": "Chemicals",

        "telecom": "Telecommunication",

        "media": "Media",

        "real estate": "Real Estate",

        "textiles": "Textiles"
    }

    for key, value in sector_mapping.items():

        if key in sector:

            return value

    return "Other"

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DB_FILE = (

    BASE_DIR

    / "database"

    / "institutional_quant.db"
)

# =========================================================
# DATABASE CONNECTION
# =========================================================

try:

    conn = duckdb.connect(
        str(DB_FILE),
        read_only=True
    )

except Exception as e:

    st.error(
        f"Database Connection Failed : {e}"
    )

    st.stop()

# =========================================================
# LOAD DATABASE
# =========================================================

@st.cache_data(ttl=300)

def load_database():

    return conn.execute(
        '''
        SELECT *
        FROM enriched_stocks
        '''
    ).df()

try:

    df = load_database()

except Exception as e:

    st.error(
        f"Data Loading Failed : {e}"
    )

    st.stop()

# =========================================================
# NUMERIC CLEANING
# =========================================================

numeric_columns = [

    "Institutional Score",

    "Alpha Score",

    "RSI",

    "ADX",

    "Buy Probability"
]

for column in numeric_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(

            df[column],

            errors="coerce"

        ).fillna(0)

# =========================================================
# SECTOR NORMALIZATION
# =========================================================

if "Sector" in df.columns:

    df["Sector"] = df[
        "Sector"
    ].apply(
        normalize_sector
    )

else:

    df["Sector"] = "Other"

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "Institutional Controls"
)

# =========================================================
# REFRESH BUTTON
# =========================================================

st.sidebar.markdown("---")

if st.sidebar.button(
    "🔄 Refresh Market Data"
):

    st.cache_data.clear()

    st.rerun()

# =========================================================
# LIVE UNIVERSE SIZE
# =========================================================

live_universe_size = st.sidebar.slider(

    "Live Analysis Universe",

    min_value=25,

    max_value=100,

    value=50,

    step=25
)

# =========================================================
# SIDEBAR WARNING
# =========================================================

st.sidebar.warning(

    """
    Larger universes may slow
    Streamlit Cloud performance.
    """
)

# =========================================================
# SECTOR FILTER
# =========================================================

sectors = sorted(

    df["Sector"]

    .dropna()

    .unique()

    .tolist()
)

selected_sector = st.sidebar.selectbox(

    "Select Sector",

    ["All"] + sectors
)

# =========================================================
# SIGNAL FILTER
# =========================================================

selected_signal = st.sidebar.selectbox(

    "Trade Signal",

    [

        "All",

        "Strong Buy",

        "Buy",

        "Watch",

        "Avoid"
    ]
)

# =========================================================
# SCORE FILTER
# =========================================================

min_score = st.sidebar.slider(

    "Minimum Institutional Score",

    0,

    100,

    60
)

# =========================================================
# FILTERING
# =========================================================

filtered_df = df.copy()

if selected_sector != "All":

    filtered_df = filtered_df[

        filtered_df["Sector"]

        == selected_sector
    ]

filtered_df = filtered_df[

    filtered_df[
        "Institutional Score"
    ] >= min_score
]

# =========================================================
# SORT BEFORE LIVE ENGINE
# =========================================================

if "Institutional Score" in filtered_df.columns:

    filtered_df = filtered_df.sort_values(

        by="Institutional Score",

        ascending=False
    )

# =========================================================
# LIMIT LIVE PROCESSING
# =========================================================

filtered_df = filtered_df.head(
    live_universe_size
)

# =========================================================
# BUILD TRADE DECISIONS
# =========================================================

with st.spinner(
    "Running Institutional Quant Engine..."
):

    filtered_df = build_trade_decisions(
        filtered_df
    )

# =========================================================
# EMPTY FAILSAFE
# =========================================================

if filtered_df.empty:

    st.warning(
        "No stocks available after processing."
    )

    st.stop()

# =========================================================
# MARKET REGIME
# =========================================================

market_regime = calculate_market_regime(
    filtered_df
)

# =========================================================
# SIGNAL FILTER
# =========================================================

if selected_signal != "All":

    filtered_df = filtered_df[

        filtered_df[
            "Trade Signal"
        ] == selected_signal
    ]

# =========================================================
# TITLE
# =========================================================

st.title(
    "Institutional Quant Platform"
)

# =========================================================
# LAST UPDATED
# =========================================================

st.caption(

    f"Last Updated: "

    f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
)

# =========================================================
# MARKET STATUS
# =========================================================

current_hour = datetime.now().hour

if 9 <= current_hour <= 15:

    st.success(
        "🟢 Indian Market Live"
    )

else:

    st.warning(
        "🔴 Market Closed"
    )

# =========================================================
# ENGINE STATUS
# =========================================================

st.info(

    f"""
    ⚡ Live Quant Engine Active

    Universe Size: {live_universe_size} stocks
    """
)

# =========================================================
# MARKET REGIME
# =========================================================

st.markdown(

    f"""
    ## Market Regime: {market_regime}
    """
)

st.markdown("---")

# =========================================================
# KPI SECTION
# =========================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Live Stocks",
    len(filtered_df)
)

avg_score = round(

    filtered_df[
        "Institutional Score"
    ].mean(),

    2
)

avg_alpha = round(

    filtered_df[
        "Alpha Score"
    ].mean(),

    2
)

avg_confidence = round(

    filtered_df[
        "Confidence"
    ].mean(),

    2
)

col2.metric(
    "Avg Institutional Score",
    avg_score
)

col3.metric(
    "Avg Alpha Score",
    avg_alpha
)

col4.metric(
    "Avg Confidence",
    avg_confidence
)

st.markdown("---")

# =========================================================
# TOP TRADE DECISIONS
# =========================================================

st.subheader(
    "Top Institutional Trade Signals"
)

top_signals = filtered_df[

    filtered_df[
        "Trade Signal"
    ].isin(

        [
            "Strong Buy",

            "Buy"
        ]
    )

].copy()

# =========================================================
# FALLBACK IF EMPTY
# =========================================================

if top_signals.empty:

    top_signals = filtered_df.head(20)

# =========================================================
# DISPLAY COLUMNS
# =========================================================

display_columns = [

    "Stock",

    "Trade Signal",

    "Current Price",

    "Target Price",

    "Stoploss",

    "Confidence",

    "Momentum Score",

    "Volume Score",

    "5D Return",

    "20D Return",

    "Composite Score"
]

available_columns = [

    col

    for col in display_columns

    if col in top_signals.columns
]

# =========================================================
# MAIN TABLE
# =========================================================

st.dataframe(

    top_signals[
        available_columns
    ].head(50),

    use_container_width=True,

    height=650
)

st.markdown("---")

# =========================================================
# TOP QUANT LEADERS
# =========================================================

st.subheader(
    "Top Quant Leaders"
)

quant_df = filtered_df.sort_values(

    by="Composite Score",

    ascending=False

).head(20)

st.dataframe(

    quant_df[
        available_columns
    ],

    use_container_width=True
)

# =========================================================
# FULL DATASET
# =========================================================

with st.expander(
    "View Full Dataset"
):

    st.dataframe(

        filtered_df,

        use_container_width=True
    )

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Institutional Quant Platform | Stable Live Quant Engine"
)

# =========================================================
# CLOSE DATABASE
# =========================================================

conn.close()
