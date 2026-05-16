# =========================================================
# INSTITUTIONAL - QUANT - URLS
# PROFESSIONAL INSTITUTIONAL DASHBOARD
# FINAL FIXED STREAMLIT VERSION
# =========================================================

# =========================================================
# IMPORTS
# =========================================================

import io
import pytz
import yfinance as yf
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path
from datetime import datetime
from plotly.subplots import make_subplots

from utils.db_manager import (
    get_connection
)

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

    .main .block-container {
        padding-top: 1rem;
        max-width: 1700px;
    }

    .stMetric {
        border-radius: 12px;
        padding: 10px;
    }

    .stDataFrame {
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# INDIA TIME
# =========================================================

india_time = datetime.now(
    pytz.timezone("Asia/Kolkata")
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
# BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

# =========================================================
# DATABASE CONNECTION
# =========================================================

try:

    conn = get_connection()

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
        """
        SELECT *
        FROM enriched_stocks
        """
    ).df()

# =========================================================
# LOAD DATA
# =========================================================

try:

    df = load_database()

    if df.empty:

        st.warning(
            "Database is empty. Run pipeline first."
        )

        st.stop()

except Exception as e:

    st.error(
        f"Database Load Failed : {e}"
    )

    st.stop()

# =========================================================
# LOAD INPUT UNIVERSE
# =========================================================

INPUT_FILE = (
    BASE_DIR
    / "input"
    / "yfinance_stock_urls.xlsx"
)

try:

    input_df = pd.read_excel(INPUT_FILE)

    total_universe = len(input_df)

except Exception:

    total_universe = len(df)

# =========================================================
# REMOVE DUPLICATES
# =========================================================

if "Stock" in df.columns:

    df = (
        df
        .drop_duplicates(subset=["Stock"])
        .reset_index(drop=True)
    )

# =========================================================
# CLEAN NUMERIC COLUMNS
# =========================================================

numeric_columns = [

    "Institutional Score",
    "Alpha Score",
    "Buy Probability",
    "RSI",
    "ADX",
    "Current Price",
    "Confidence"
]

for column in numeric_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)

# =========================================================
# NORMALIZE SECTOR
# =========================================================

if "Sector" in df.columns:

    df["Sector"] = df["Sector"].apply(
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

st.sidebar.markdown("---")

st.sidebar.markdown(
    "## 📈 Institutional - Quant - Urls"
)

st.sidebar.caption(
    """
    AI-Powered Institutional
    Quantitative Analytics Platform
    """
)

st.sidebar.markdown("---")

st.sidebar.success(
    "🟢 Quant Engine Active"
)

st.sidebar.info(
    "⚡ Live Institutional Analytics"
)

st.sidebar.info(
    "🤖 ML Prediction Engine Enabled"
)

st.sidebar.info(
    "📊 Backtesting Engine Enabled"
)

st.sidebar.markdown("---")

# =========================================================
# LIVE UNIVERSE SIZE
# =========================================================

max_universe = max(
    100,
    int(df["Stock"].nunique())
)

default_universe = min(
    500,
    max_universe
)

live_universe_size = st.sidebar.slider(
    "Live Analysis Universe",
    min_value=100,
    max_value=max_universe,
    value=default_universe,
    step=100
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
# FILTER DATA
# =========================================================

filtered_df = df.copy()

# =========================================================
# SEARCH
# =========================================================

search_stock = st.sidebar.text_input(
    "Search Stock"
)

if search_stock:

    filtered_df = filtered_df[

        filtered_df["Stock"]
        .astype(str)
        .str.contains(
            search_stock,
            case=False,
            na=False
        )
    ]

# =========================================================
# SECTOR FILTER
# =========================================================

if selected_sector != "All":

    filtered_df = filtered_df[
        filtered_df["Sector"] == selected_sector
    ]

# =========================================================
# SCORE FILTER
# =========================================================

if "Institutional Score" in filtered_df.columns:

    filtered_df = filtered_df[
        filtered_df["Institutional Score"] >= min_score
    ]

# =========================================================
# SORT
# =========================================================

sort_column = "Institutional Score"

if "Composite Score" in filtered_df.columns:
    sort_column = "Composite Score"

filtered_df = filtered_df.sort_values(
    by=sort_column,
    ascending=False
)

# =========================================================
# LIMIT UNIVERSE
# =========================================================

if live_universe_size < len(filtered_df):

    filtered_df = filtered_df.head(
        live_universe_size
    )

# =========================================================
# BUILD TRADE DECISIONS
# =========================================================

with st.spinner(
    "Running Institutional Quant Engine..."
):

    try:

        filtered_df = build_trade_decisions(
            filtered_df
        )

    except Exception as e:

        st.warning(
            f"Trade Engine Warning : {e}"
        )

# =========================================================
# SIGNAL FILTER
# =========================================================

if selected_signal != "All":

    filtered_df = filtered_df[
        filtered_df["Trade Signal"] == selected_signal
    ]

# =========================================================
# EMPTY CHECK
# =========================================================

if filtered_df.empty:

    st.warning(
        "No stocks available after filtering."
    )

    st.stop()

# =========================================================
# MARKET REGIME
# =========================================================

try:

    market_regime = calculate_market_regime(
        filtered_df
    )

except Exception:

    market_regime = "Unknown"

# =========================================================
# HEATMAP DATA
# =========================================================

heatmap_df = (

    filtered_df

    .groupby("Sector")

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

    heatmap_df["Avg Institutional Score"]
    *
    heatmap_df["Avg Confidence"]
)

# =========================================================
# HEADER
# =========================================================

st.title(
    "📈 Institutional - Quant - Urls"
)

st.caption(
    "AI-Powered Institutional Quantitative Analytics Platform"
)

st.caption(
    f"Last Updated : "
    f"{india_time.strftime('%d-%m-%Y %H:%M:%S IST')}"
)

st.markdown("---")

# =========================================================
# STATUS BAR
# =========================================================

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:

    current_hour = india_time.hour

    market_open = (
        (current_hour > 9)
        or
        (
            current_hour == 9
            and india_time.minute >= 15
        )
    )

    market_close = (
        current_hour < 15
        or
        (
            current_hour == 15
            and india_time.minute <= 30
        )
    )

    if market_open and market_close:

        st.success(
            "🟢 NSE Market Live"
        )

    else:

        st.warning(
            "🔴 NSE Market Closed"
        )

with status_col2:

    st.info(
        f"⚡ Universe Size : {len(filtered_df)}"
    )

with status_col3:

    st.info(
        f"📊 Regime : {market_regime}"
    )

# =========================================================
# KPI METRICS
# =========================================================

processed_universe = len(df)

failed_universe = max(
    total_universe - processed_universe,
    0
)

success_rate = round(
    (
        processed_universe
        / total_universe
    ) * 100,
    2
)

avg_score = round(
    filtered_df["Institutional Score"].mean(),
    2
)

avg_confidence = round(
    filtered_df["Confidence"].mean(),
    2
)

strong_buys = len(
    filtered_df[
        filtered_df["Trade Signal"] == "Strong Buy"
    ]
)

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "Total Universe",
    total_universe
)

metric2.metric(
    "Processed Stocks",
    processed_universe
)

metric3.metric(
    "Failed Stocks",
    failed_universe
)

metric4.metric(
    "Success Rate",
    f"{success_rate}%"
)

st.markdown("---")

metric5, metric6, metric7, metric8 = st.columns(4)

metric5.metric(
    "Live Stocks",
    len(filtered_df)
)

metric6.metric(
    "Institutional Score",
    avg_score
)

metric7.metric(
    "Strong Buys",
    strong_buys
)

metric8.metric(
    "Confidence",
    avg_confidence
)

# =========================================================
# HEATMAP
# =========================================================

st.markdown("---")

st.subheader(
    "Institutional Sector Heatmap"
)

if heatmap_df.empty:

    st.warning(
        "Heatmap data unavailable."
    )

else:

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

# =========================================================
# CLOSE DATABASE
# =========================================================

conn.close()
