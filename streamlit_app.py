# =========================================================
# FINAL ENTERPRISE STREAMLIT APP
# INSTITUTIONAL QUANT PLATFORM
# =========================================================

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np

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
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "output"

CSV_FILE = OUTPUT_DIR / "enriched_stock_data.csv.gz"

XLSX_FILE = OUTPUT_DIR / "institutional_quant.xlsx"

# =========================================================
# CACHE LOADER
# =========================================================

@st.cache_data(ttl=3600, show_spinner=False)

def load_data(data_file):

    try:

        suffix = str(data_file).lower()

        # =====================================================
        # CSV
        # =====================================================

        if suffix.endswith(".csv"):

            try:

                df = pd.read_csv(
                    data_file,
                    encoding="utf-8"
                )

            except UnicodeDecodeError:

                df = pd.read_csv(
                    data_file,
                    encoding="latin1"
                )

        # =====================================================
        # GZIP CSV
        # =====================================================

        elif suffix.endswith(".gz"):

            df = pd.read_csv(
                data_file,
                compression="gzip"
            )

        # =====================================================
        # PARQUET
        # =====================================================

        elif suffix.endswith(".parquet"):

            df = pd.read_parquet(data_file)

        # =====================================================
        # EXCEL
        # =====================================================

        elif (
            suffix.endswith(".xlsx")
            or
            suffix.endswith(".xls")
        ):

            df = pd.read_excel(data_file)

        # =====================================================
        # UNKNOWN
        # =====================================================

        else:

            st.error(
                f"Unsupported file format : {data_file}"
            )

            return pd.DataFrame()

        # =====================================================
        # CLEAN COLUMN NAMES
        # =====================================================

        df.columns = [

            str(col).strip()

            for col in df.columns

        ]

        # =====================================================
        # REQUIRED COLUMNS
        # =====================================================

        required_columns = {

            "Stock": "",
            "Sector": "Unknown",
            "Trade Signal": "WATCH",
            "Institutional Score": 0,
            "Confidence": 0,
            "Current Price": 0,
            "Composite Score": 0,
            "RSI": 50,
            "SMA20": 0,
            "SMA50": 0,
            "MACD": 0,
            "ATR": 0,
            "1M Return": 0,
            "3M Return": 0,
            "6M Return": 0

        }

        for col, default in required_columns.items():

            if col not in df.columns:

                df[col] = default

        # =====================================================
        # NUMERIC CLEANING
        # =====================================================

        numeric_cols = [

            "Institutional Score",
            "Confidence",
            "Current Price",
            "Composite Score",
            "RSI",
            "SMA20",
            "SMA50",
            "MACD",
            "ATR",
            "1M Return",
            "3M Return",
            "6M Return"

        ]

        for col in numeric_cols:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

        # =====================================================
        # SIGNAL CLEANING
        # =====================================================

        df["Trade Signal"] = (

            df["Trade Signal"]

            .astype(str)

            .str.upper()

            .str.strip()

        )

        return df

    except Exception as e:

        st.error(f"DATA LOAD FAILED : {e}")

        return pd.DataFrame()

# =========================================================
# LOAD DATA
# =========================================================

df = load_data(CSV_FILE)

if df.empty:

    st.warning("No institutional data available.")

    st.stop()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("Institutional Controls")

search_stock = st.sidebar.text_input(
    "Search Stock"
)

signal_order = [

    "STRONG BUY",
    "BUY",
    "WATCH",
    "HOLD",
    "AVOID"

]

signal_colors = {

    "STRONG BUY": "#006400",
    "BUY": "#00AA00",
    "WATCH": "#FF8C00",
    "HOLD": "#1E90FF",
    "AVOID": "#FF0000"

}

selected_trade_signal = st.sidebar.multiselect(
    "Trade Signal",
    options=signal_order,
    default=[]
)

min_score = st.sidebar.slider(
    "Minimum Institutional Score",
    0,
    100,
    50
)

min_confidence = st.sidebar.slider(
    "Minimum Confidence",
    0,
    100,
    70
)

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
# MARKET REGIME
# =========================================================

from market_regime import get_market_regime

regime, regime_color, regime_details = get_market_regime()

# =========================================================
# FILTERED DATA
# =========================================================

filtered_df = df.copy()

# =========================================================
# ADVANCED INSTITUTIONAL SIGNAL ENGINE
# =========================================================

def generate_trade_signal(row, market_regime):

    try:
        score = float(row.get("Institutional Score", 0))
    except:
        score = 0

    try:
        rsi = float(row.get("RSI", 50))
    except:
        rsi = 50

    try:
        confidence = float(row.get("Confidence", 50))
    except:
        confidence = 50

    try:
        momentum = float(row.get("Momentum", 0))
    except:
        momentum = 0

    try:
        volume_score = float(row.get("Volume Score", 50))
    except:
        volume_score = 50

    regime_lower = str(market_regime).lower()

    # =====================================================
    # REGIME ADAPTIVE THRESHOLDS
    # =====================================================

    if "bull" in regime_lower:

        strong_buy_score = 85
        strong_buy_conf = 70
        strong_buy_rsi = 55

        buy_score = 70

    elif "bear" in regime_lower:

        strong_buy_score = 95
        strong_buy_conf = 88
        strong_buy_rsi = 60

        buy_score = 82

    elif "sideways" in regime_lower:

        strong_buy_score = 90
        strong_buy_conf = 75
        strong_buy_rsi = 50

        buy_score = 72

    else:

        strong_buy_score = 88
        strong_buy_conf = 72
        strong_buy_rsi = 52

        buy_score = 70

    # =====================================================
    # STRONG BUY
    # =====================================================

    if (
        score >= strong_buy_score
        and confidence >= strong_buy_conf
        and rsi >= strong_buy_rsi
        and momentum > 0
        and volume_score >= 60
    ):

        return "STRONG BUY"

    # =====================================================
    # BUY
    # =====================================================

    elif (
        score >= buy_score
        and confidence >= 55
    ):

        return "BUY"

    # =====================================================
    # HOLD
    # =====================================================

    elif score >= 45:

        return "HOLD"

    # =====================================================
    # WATCH
    # =====================================================

    else:

        return "WATCH"

# =========================================================
# APPLY SIGNAL ENGINE
# =========================================================

filtered_df["Trade Signal"] = filtered_df.apply(
    lambda row: generate_trade_signal(row, regime),
    axis=1
)

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
# SCORE FILTER
# =========================================================

filtered_df = filtered_df[
    filtered_df["Institutional Score"] >= min_score
]

filtered_df = filtered_df[
    filtered_df["Confidence"] >= min_confidence
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

st.title("🏦 Institutional Quant Platform")

st.caption(
    "AI Powered Institutional Analytics Engine"
)

# =========================================================
# MARKET DETAILS
# =========================================================

st.write(
    f"""
    NIFTY: {regime_details.get('NIFTY', 'N/A')}
    SMA50: {regime_details.get('SMA50', 'N/A')}
    SMA200: {regime_details.get('SMA200', 'N/A')}
    RSI: {regime_details.get('RSI', 'N/A')}
    """
)

# =========================================================
# MARKET REGIME BANNER
# =========================================================

st.markdown(
    f"""
    <div style="
        background-color:{regime_color};
        padding:15px;
        border-radius:10px;
        text-align:center;
        font-size:28px;
        font-weight:bold;
        color:white;
        margin-bottom:20px;
    ">
        MARKET REGIME : {regime}
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# METRICS
# =========================================================

bullish_count = len(
    filtered_df[
        filtered_df["Trade Signal"] == "STRONG BUY"
    ]
)

buy_count = len(
    filtered_df[
        filtered_df["Trade Signal"] == "BUY"
    ]
)

avg_score = round(
    filtered_df["Institutional Score"].mean(),
    2
)

avg_rsi = round(
    filtered_df["RSI"].mean(),
    2
)

# =========================================================
# METRIC CARDS
# =========================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Strong Buy Stocks",
        bullish_count
    )

with col2:
    st.metric(
        "Buy Stocks",
        buy_count
    )

with col3:
    st.metric(
        "Average Score",
        avg_score
    )

with col4:
    st.metric(
        "Average RSI",
        avg_rsi
    )

# =========================================================
# TRADE SIGNAL DISTRIBUTION
# =========================================================

st.markdown("---")

st.subheader("Trade Signal Distribution")

signal_chart = px.pie(
    filtered_df,
    names="Trade Signal",
    color="Trade Signal",
    color_discrete_map=signal_colors
)

st.plotly_chart(
    signal_chart,
    width="stretch"
)
