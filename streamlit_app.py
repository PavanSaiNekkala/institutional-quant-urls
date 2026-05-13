# =========================================================
# INSTITUTIONAL - QUANT - URLS
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

    page_title="Institutional - Quant - Urls",

    page_icon="📈",

    layout="wide",

    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .stMetric {
        background-color: #111827;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #1f2937;
    }

    .metric-title {
        font-size: 14px;
        color: #9ca3af;
    }

    .main-title {
        font-size: 42px;
        font-weight: 800;
        color: white;
        margin-bottom: 0px;
    }

    .sub-title {
        font-size: 16px;
        color: #9ca3af;
        margin-top: -10px;
    }

    .section-title {
        font-size: 26px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
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

        "banking": "Banking",
        "banks": "Banking",

        "financial services": "Financial Services",

        "pharma": "Healthcare",

        "oil & gas": "Energy",

        "fmcg": "Consumer",

        "auto": "Automobile",

        "metals": "Metals & Mining",

        "chemicals": "Chemicals"
    }

    for key, value in sector_mapping.items():

        if key in sector:

            return value

    return "Other"

# =========================================================
# DATABASE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DB_FILE = (

    BASE_DIR

    / "database"

    / "institutional_quant.db"
)

try:

    conn = duckdb.connect(

        str(DB_FILE),

        read_only=True
    )

except Exception as e:

    st.error(
        f"Database Connection Failed: {e}"
    )

    st.stop()

# =========================================================
# LOAD DATABASE
# =========================================================

@st.cache_data(ttl=300)

def load_database():

    return conn.execute(
        """
        SELECT *
        FROM enriched_stocks
        """
    ).df()

try:

    df = load_database()

except Exception as e:

    st.error(
        f"Data Loading Failed: {e}"
    )

    st.stop()

# =========================================================
# CLEAN NUMERIC
# =========================================================

numeric_columns = [

    "Institutional Score",

    "Alpha Score",

    "Buy Probability",

    "RSI",

    "ADX"
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

st.sidebar.markdown(
    "## Institutional Controls"
)

st.sidebar.caption(
    "Live Quantitative Filtering Engine"
)

st.sidebar.markdown("---")

# =========================================================
# REFRESH BUTTON
# =========================================================

if st.sidebar.button(
    "🔄 Refresh Market Data"
):

    st.cache_data.clear()

    st.rerun()

# =========================================================
# LIVE UNIVERSE
# =========================================================

live_universe_size = st.sidebar.slider(

    "Live Analysis Universe",

    min_value=25,

    max_value=100,

    value=50,

    step=25
)

# =========================================================
# FILTERS
# =========================================================

sectors = sorted(

    df["Sector"]

    .dropna()

    .unique()

    .tolist()
)

selected_sector = st.sidebar.selectbox(

    "Sector",

    ["All"] + sectors
)

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
# LIMIT LIVE ENGINE
# =========================================================

filtered_df = filtered_df.sort_values(

    by="Institutional Score",

    ascending=False

).head(
    live_universe_size
)

# =========================================================
# LIVE ENGINE
# =========================================================

with st.spinner(
    "Running Institutional Quant Engine..."
):

    filtered_df = build_trade_decisions(
        filtered_df
    )

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
# HEADER
# =========================================================

st.markdown(

    """
    <div class="main-title">
        Institutional - Quant - Urls
    </div>

    <div class="sub-title">
        AI-Powered Institutional Quantitative Analytics Platform
    </div>
    """,

    unsafe_allow_html=True
)

st.caption(

    f"Last Updated: "

    f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
)

# =========================================================
# STATUS BAR
# =========================================================

col_a, col_b = st.columns([1, 2])

with col_a:

    current_hour = datetime.now().hour

    if 9 <= current_hour <= 15:

        st.success(
            "🟢 Indian Market Live"
        )

    else:

        st.warning(
            "🔴 Market Closed"
        )

with col_b:

    st.info(

        f"""
        ⚡ Live Quant Engine Active
        
        Universe Size: {live_universe_size} Stocks
        
        Market Regime: {market_regime}
        """
    )

# =========================================================
# KPI SECTION
# =========================================================

col1, col2, col3, col4 = st.columns(4)

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

strong_buys = len(

    filtered_df[

        filtered_df[
            "Trade Signal"
        ] == "Strong Buy"
    ]
)

col1.metric(
    "Live Stocks",
    len(filtered_df)
)

col2.metric(
    "Avg Institutional Score",
    avg_score
)

col3.metric(
    "Strong Buys",
    strong_buys
)

col4.metric(
    "Avg Confidence",
    avg_confidence
)

st.markdown("---")

# =========================================================
# TOP SIGNALS
# =========================================================

st.markdown(
    '<div class="section-title">Top Institutional Trade Signals</div>',
    unsafe_allow_html=True
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

styled_df = top_signals[
    available_columns
].head(50)

st.dataframe(

    styled_df,

    use_container_width=True,

    height=650
)

st.markdown("---")

# =========================================================
# QUANT LEADERS
# =========================================================

st.markdown(
    '<div class="section-title">Top Quant Leaders</div>',
    unsafe_allow_html=True
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
    "Institutional - Quant - Urls | Stable Live Quantitative Analytics Engine"
)

# =========================================================
# CLOSE DATABASE
# =========================================================

conn.close()
