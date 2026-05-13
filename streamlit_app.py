# =========================================================
# INSTITUTIONAL - QUANT - URLS
# CLEAN PROFESSIONAL DASHBOARD
# =========================================================

# =========================================================
# IMPORTS
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import duckdb
import pytz

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
# MINIMAL CSS
# =========================================================

st.markdown(
    """
    <style>

    .main .block-container {

        padding-top: 1rem;

        max-width: 1500px;
    }

    .stDataFrame {

        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# INDIAN TIME
# =========================================================

india_time = datetime.now(

    pytz.timezone(
        "Asia/Kolkata"
    )
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
        f"Database Load Failed: {e}"
    )

    st.stop()

# =========================================================
# REMOVE DUPLICATES
# =========================================================

if "Stock" in df.columns:

    df = df.drop_duplicates(

        subset=["Stock"]

    ).reset_index(drop=True)

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

st.sidebar.title(
    "Institutional Controls"
)
# =========================================================
# SIDEBAR BRANDING
# =========================================================

st.sidebar.markdown("---")

st.sidebar.markdown(
    """
    ## 📈 Institutional - Quant - Urls
    """
)

st.sidebar.caption(
    """
    AI-Powered Institutional
    Quantitative Analytics Platform
    """
)

st.sidebar.markdown("---")

# =========================================================
# SYSTEM STATUS
# =========================================================

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
st.sidebar.caption(
    "Live Quantitative Filtering Engine"
)

# =========================================================
# LIVE UNIVERSE
# =========================================================

live_universe_size = st.sidebar.slider(

    "Live Analysis Universe",

    min_value=100,

    max_value=df["Stock"].nunique(),

    value=min(

        300,

        df["Stock"].nunique()
    ),

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
# STOCK SEARCH
# =========================================================

search_stock = st.sidebar.text_input(
    "Search Stock"
)

if search_stock:

    filtered_df = filtered_df[

        filtered_df[
            "Stock"
        ]

        .astype(str)

        .str.contains(

            search_stock,

            case=False,

            na=False
        )
    ]
# =========================================================
# FILTER DATA
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
)

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

    filtered_df = build_trade_decisions(
        filtered_df
    )

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

st.title(
    "📈 Institutional - Quant - Urls"
)

st.caption(
    "AI-Powered Institutional Quantitative Analytics Platform"
)

st.caption(

    f"Last Updated: "

    f"{india_time.strftime('%d-%m-%Y %H:%M:%S IST')}"
)

st.markdown("---")

# =========================================================
# STATUS BAR
# =========================================================

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:

    current_hour = india_time.hour

    if 9 <= current_hour <= 15:

        st.success(
            "🟢 Indian Market Live"
        )

    else:

        st.warning(
            "🔴 Market Closed"
        )

with status_col2:

    st.info(
        f"⚡ Universe Size: {len(filtered_df)}"
    )

with status_col3:

    st.info(
        f"📊 Regime: {market_regime}"
    )

# =========================================================
# KPI CALCULATIONS
# =========================================================

avg_score = round(

    filtered_df[
        "Institutional Score"
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

# =========================================================
# KPI SECTION
# =========================================================

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "Live Stocks",
    len(filtered_df)
)

metric2.metric(
    "Institutional Score",
    avg_score
)

metric3.metric(
    "Strong Buys",
    strong_buys
)

metric4.metric(
    "Confidence",
    avg_confidence
)

st.markdown("---")

# =========================================================
# MAIN DASHBOARD LAYOUT
# =========================================================

left_col, right_col = st.columns([3.5, 1.2])

# =========================================================
# LEFT SIDE
# =========================================================

with left_col:

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

    if top_signals.empty:

        top_signals = filtered_df.head(20)

    display_columns = [

        "Stock",

        "Sector",

        "Trade Signal",

        "Current Price",

        "Target Price",

        "Confidence",

        "Composite Score"
    ]

    available_columns = [

        col

        for col in display_columns

        if col in top_signals.columns
    ]

    st.dataframe(

        top_signals[
            available_columns
        ].head(100),

        use_container_width=True,

        height=700
    )

# =========================================================
# RIGHT SIDE
# =========================================================

with right_col:

    st.subheader(
        "Market Intelligence"
    )

    bullish_count = len(

        filtered_df[

            filtered_df[
                "Trade Signal"
            ].isin(

                [
                    "Strong Buy",

                    "Buy"
                ]
            )
        ]
    )

    bearish_count = len(

        filtered_df[

            filtered_df[
                "Trade Signal"
            ] == "Avoid"
        ]
    )

    st.metric(
        "Bullish Signals",
        bullish_count
    )

    st.metric(
        "Bearish Signals",
        bearish_count
    )

    st.metric(
        "Market Regime",
        market_regime
    )

    if "Sector" in filtered_df.columns:

        sector_series = (

            filtered_df["Sector"]

            .dropna()

            .astype(str)
        )

        if not sector_series.empty:

            top_sector = (

                sector_series
                .mode()
                .iloc[0]
            )

        else:

            top_sector = "Unknown"

    else:

        top_sector = "Unknown"

    st.info(
        f"Dominant Sector: {top_sector}"
    )
# =========================================================
# INSTITUTIONAL ANALYTICS
# =========================================================

st.markdown("---")

st.subheader(
    "Institutional Analytics"
)

chart_col1, chart_col2 = st.columns(2)

# =========================================================
# SIGNAL DISTRIBUTION
# =========================================================

with chart_col1:

    signal_counts = (

        filtered_df[
            "Trade Signal"
        ]

        .value_counts()

        .reset_index()
    )

    signal_counts.columns = [

        "Signal",

        "Count"
    ]

    fig_signal = px.pie(

        signal_counts,

        names="Signal",

        values="Count",

        title="Trade Signal Distribution"
    )

    fig_signal.update_layout(

        height=450
    )

    st.plotly_chart(

        fig_signal,

        use_container_width=True
    )

# =========================================================
# SECTOR DISTRIBUTION
# =========================================================

with chart_col2:

    if "Sector" in filtered_df.columns:

        sector_counts = (

            filtered_df[
                "Sector"
            ]

            .value_counts()

            .head(10)

            .reset_index()
        )

        sector_counts.columns = [

            "Sector",

            "Count"
        ]

        fig_sector = px.bar(

            sector_counts,

            x="Sector",

            y="Count",

            title="Top Sectors",

            text_auto=True
        )

        fig_sector.update_layout(

            height=450
        )

        st.plotly_chart(

            fig_sector,

            use_container_width=True
        )

# =========================================================
# SCORE DISTRIBUTION
# =========================================================

st.markdown("---")

score_col1, score_col2 = st.columns(2)

with score_col1:

    fig_score = px.histogram(

        filtered_df,

        x="Institutional Score",

        nbins=30,

        title="Institutional Score Distribution"
    )

    fig_score.update_layout(
        height=450
    )

    st.plotly_chart(

        fig_score,

        use_container_width=True
    )

with score_col2:

    fig_conf = px.scatter(

        filtered_df,

        x="Institutional Score",

        y="Confidence",

        color="Trade Signal",

        hover_data=["Stock"],

        title="Confidence vs Institutional Score"
    )

    fig_conf.update_layout(
        height=450
    )

    st.plotly_chart(

        fig_conf,

        use_container_width=True
    )
# =========================================================
# QUANT LEADERS
# =========================================================

st.markdown("---")

st.subheader(
    "Top Quant Leaders"
)

quant_df = filtered_df.sort_values(

    by="Composite Score",

    ascending=False

).head(25)

st.dataframe(

    quant_df[
        available_columns
    ],

    use_container_width=True,

    height=500
)

# =========================================================
# FULL DATASET
# =========================================================

with st.expander(
    "View Full Dataset"
):

    st.dataframe(

        filtered_df,

        use_container_width=True,

        height=700
    )
# =========================================================
# DOWNLOAD SECTION
# =========================================================

st.markdown("---")

st.subheader(
    "Download Analytics"
)

download_col1, download_col2 = st.columns(2)

with download_col1:

    csv_data = filtered_df.to_csv(
        index=False
    )

    st.download_button(

        label="📥 Download CSV",

        data=csv_data,

        file_name="institutional_quant_data.csv",

        mime="text/csv"
    )

with download_col2:

    excel_buffer = filtered_df.to_excel(
        "temp_download.xlsx",
        index=False
    )

    with open(
        "temp_download.xlsx",
        "rb"
    ) as f:

        st.download_button(

            label="📥 Download Excel",

            data=f,

            file_name="institutional_quant_data.xlsx",

            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Institutional - Quant - Urls | Institutional Analytics Dashboard"
)

# =========================================================
# CLOSE DATABASE
# =========================================================

conn.close()
