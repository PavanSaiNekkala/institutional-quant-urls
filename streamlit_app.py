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

CSV_FILE = OUTPUT_DIR / "enriched_stock_data.csv"

XLSX_FILE = OUTPUT_DIR / "institutional_quant.xlsx"

# =========================================================
# CACHE LOADER
# =========================================================

@st.cache_data(
        ttl=3600,
        show_spinner=False
)

def load_data():

        try:

                # =========================================
                # PRIORITY 1 -> CSV
                # =========================================

                if CSV_FILE.exists():

                        df = pd.read_csv(
                                CSV_FILE
                        )

                # =========================================
                # PRIORITY 2 -> XLSX
                # =========================================

                elif XLSX_FILE.exists():

                        df = pd.read_excel(
                                XLSX_FILE
                        )

                else:

                        return pd.DataFrame()

                # =========================================
                # EMPTY SAFETY
                # =========================================

                if df.empty:

                        return pd.DataFrame()

                # =========================================
                # COLUMN CLEANING
                # =========================================

                df.columns = [

                        str(col).strip()
                        for col in df.columns

                ]

                # =========================================
                # REQUIRED COLUMNS
                # =========================================

                required_columns = {

                        "Stock": "",

                        "Sector": "Unknown",

                        "Trade Signal": "WATCH",

                        "Institutional Score": 0,

                        "Confidence": 0,

                        "Current Price": 0,

                        "Composite Score": 0,

                        "RSI": 0,

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

                # =========================================
                # NUMERIC CLEANING
                # =========================================

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

                # =========================================
                # SIGNAL CLEANING
                # =========================================

                df["Trade Signal"] = (

                        df["Trade Signal"]

                        .astype(str)

                        .str.upper()

                        .str.strip()

                )

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
                        f"DATA LOAD FAILED : {e}"
                )

                return pd.DataFrame()

# =========================================================
# LOAD DATA
# =========================================================

df = load_data()

# =========================================================
# EMPTY SAFETY
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
signal_colors = {
    "STRONG BUY": "#006400",   # dark green
    "BUY": "#00AA00",          # green
    "WATCH": "#FF8C00",        # orange
    "HOLD": "#1E90FF",         # blue
    "AVOID": "#FF4B4B"         # red
}

selected_trade_signal = st.sidebar.multiselect(

        "Trade Signal",

        options=signal_order,

        default=[]

)

# =========================================================
# SCORE FILTERS
# =========================================================

min_score = st.sidebar.slider(

        "Minimum Institutional Score",

        0,
        100,
        70

)

min_confidence = st.sidebar.slider(

        "Minimum Confidence",

        0,
        100,
        70

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
# SMART SIGNAL ENGINE
# =========================================================

def generate_trade_signal(row):

    score = row.get("Institutional Score", 0)
    rsi = row.get("RSI", 50)
    revenue_growth = row.get("Revenue_Growth", 0)
    institutional_change = row.get("Institutional_Change", 0)

    # STRONG BUY
    if (
        score >= 90
        and 50 <= rsi <= 70
        and revenue_growth > 0
        and institutional_change > 0
    ):
        return "STRONG BUY"

    # BUY
    elif (
        score >= 75
        and rsi > 45
    ):
        return "BUY"

    # WATCH
    elif score >= 60:
        return "WATCH"

    # HOLD
    elif score >= 45:
        return "HOLD"

    # AVOID
    else:
        return "AVOID"


filtered_df["Trade Signal"] = filtered_df.apply(
    generate_trade_signal,
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

        filtered_df[
                "Institutional Score"
        ] >= min_score

]

filtered_df = filtered_df[

        filtered_df[
                "Confidence"
        ] >= min_confidence

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
        "AI Powered Institutional Analytics Engine"
)
from market_regime import get_market_regime

regime, regime_color, regime_details = get_market_regime()

st.write(
    f"""
    NIFTY: {regime_details.get('NIFTY', 'N/A')}
    SMA50: {regime_details.get('SMA50', 'N/A')}
    SMA200: {regime_details.get('SMA200', 'N/A')}
    RSI: {regime_details.get('RSI', 'N/A')}
    """
)

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
# MARKET METRICS
# =========================================================

bullish_count = len(

        filtered_df[
                filtered_df["Trade Signal"]
                == "STRONG BUY"
        ]

)

buy_count = len(

        filtered_df[
                filtered_df["Trade Signal"]
                == "BUY"
        ]

)

avg_score = round(

        filtered_df[
                "Institutional Score"
        ].mean(),

        2

)

avg_rsi = round(

        filtered_df[
                "RSI"
        ].mean(),

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
# SIGNAL DISTRIBUTION
# =========================================================

st.markdown("---")

st.subheader(
        "Trade Signal Distribution"
)

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

# =========================================================
# TOP PICKS
# =========================================================

st.markdown("---")

st.subheader(
        "🔥 Top Institutional Picks"
)

top_picks = filtered_df.sort_values(

        by="Composite Score",

        ascending=False

).head(25)

st.dataframe(

        top_picks,

        width="stretch",
        height=500

)

st.markdown("---")

st.subheader(
        "🏆 Sector Leaders"
)

if "Market Leader" in filtered_df.columns:

        sector_leaders = filtered_df[
                filtered_df["Market Leader"] == "YES"
        ]

else:

        sector_leaders = pd.DataFrame()

if not sector_leaders.empty:

        sector_leaders = sector_leaders.sort_values(

                by="Sector Percentile",

                ascending=False

        )

        st.dataframe(

                sector_leaders,

                width="stretch",
                height=400

        )

else:

        st.info("No sector leaders available.")


st.markdown("---")

st.subheader(
        "🚀 Elite Institutional Stocks"
)

if "Elite Stock" in filtered_df.columns:

        elite_df = filtered_df[
                filtered_df["Elite Stock"] == "YES"
        ]

else:

        elite_df = pd.DataFrame()

if not elite_df.empty:

        st.dataframe(

                elite_df,

                width="stretch",
                height=400

        )

else:

        st.info("No elite stocks available.")

st.markdown("---")

st.subheader(
        "🔥 Sector Strength Heatmap"
)

sector_strength = (

        filtered_df

        .groupby("Sector")[
                "Institutional Score"
        ]

        .mean()

        .reset_index()

)

heatmap = px.treemap(

        sector_strength,

        path=["Sector"],

        values="Institutional Score",

        color="Institutional Score"

)

st.plotly_chart(

        heatmap,

        width="stretch"

)

# =========================================================
# RSI HEATMAP
# =========================================================

st.markdown("---")

st.subheader(
        "RSI Heatmap"
)

heatmap = px.scatter(

        filtered_df,

        x="RSI",

        y="Institutional Score",

        color="Trade Signal",

        color_discrete_map=signal_colors,

        hover_data=["Stock"]

)

st.plotly_chart(

        heatmap,

        width="stretch"

)

# =========================================================
# MOMENTUM ANALYTICS
# =========================================================

st.markdown("---")

st.subheader(
        "Momentum Analysis"
)

momentum_chart = px.scatter(

        filtered_df,

        x="3M Return",

        y="6M Return",

        color="Trade Signal",

        color_discrete_map=signal_colors,

        hover_data=["Stock"]

)
st.plotly_chart(

        momentum_chart,

        width="stretch"

)

# =========================================================
# MAIN TABLE
# =========================================================

st.markdown("---")

st.subheader(
        "📊 Institutional Stock Table"
)

display_columns = [

        "Stock",
        "Sector",
        "Trade Signal",
        "Institutional Score",
        "Confidence",
        "Composite Score",
        "Current Price",
        "RSI",
        "SMA20",
        "SMA50",
        "MACD",
        "ATR",
        "1M Return",
        "3M Return",
        "6M Return",
        "Sector Rank",
        "Sector Percentile",
        "Relative Strength Score",
        "Market Leader",
        "Elite Stock"

]

available_columns = [

        col

        for col in display_columns

        if col in filtered_df.columns

]
# =========================
# MAIN TABLE
# =========================

def highlight_signal(val):

        colors = {

                "STRONG BUY": "background-color: #006400; color: white;",
                "BUY": "background-color: #00AA00; color: white;",
                "WATCH": "background-color: #FF8C00; color: white;",
                "HOLD": "background-color: #1E90FF; color: white;",
                "AVOID": "background-color: #FF0000; color: white;"

        }

        return colors.get(val, "")

styled_df = filtered_df[
        available_columns
].sort_values(
        by="Composite Score",
        ascending=False
).style.map(
        highlight_signal,
        subset=["Trade Signal"]
)

st.dataframe(

        styled_df,

        width="stretch",
        height=800

)
st.dataframe(

        filtered_df[
                available_columns
        ]

        .sort_values(

                by="Composite Score",

                ascending=False

        ),

        width="stretch",
        height=800

)

# =========================================================
# DOWNLOAD
# =========================================================

st.markdown("---")

st.subheader(
        "Download Institutional Data"
)

csv = filtered_df.to_csv(
        index=False
).encode("utf-8")

st.download_button(

        "Download CSV",

        csv,

        "institutional_quant_data.csv",

        "text/csv"

)
