# =========================================================
# LIGHTWEIGHT CLOUD STREAMLIT APP
# =========================================================

# =========================================================
# IMPORTS
# =========================================================

import streamlit as st
import pandas as pd
import duckdb
import plotly.express as px

from pathlib import Path

from analytics.trade_decision_engine import (

    build_trade_decisions,

    calculate_market_regime
)

from analytics.realtime_market_engine import (
    fetch_live_market_data
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
# LIVE MARKET SWITCH
# =========================================================

ENABLE_LIVE_MARKET = False

# =========================================================
# SECTOR NORMALIZATION ENGINE
# =========================================================

def normalize_sector(sector):

    if pd.isna(sector):

        return "Other"

    sector = str(sector).strip().lower()

    sector_mapping = {

        # =============================================
        # TECHNOLOGY
        # =============================================

        "it services": "Technology",

        "software": "Technology",

        "information technology": "Technology",

        "tech": "Technology",

        "digital": "Technology",

        "saas": "Technology",

        # =============================================
        # BANKING & FINANCE
        # =============================================

        "banks": "Banking",

        "banking": "Banking",

        "financial services": "Financial Services",

        "finance": "Financial Services",

        "nbfc": "Financial Services",

        "insurance": "Financial Services",

        "asset management": "Financial Services",

        # =============================================
        # PHARMA & HEALTHCARE
        # =============================================

        "pharmaceuticals": "Healthcare",

        "pharma": "Healthcare",

        "healthcare": "Healthcare",

        "biotech": "Healthcare",

        "hospital": "Healthcare",

        # =============================================
        # ENERGY
        # =============================================

        "oil & gas": "Energy",

        "oil": "Energy",

        "gas": "Energy",

        "power": "Energy",

        "renewable energy": "Energy",

        "energy": "Energy",

        # =============================================
        # FMCG & CONSUMER
        # =============================================

        "fmcg": "Consumer",

        "consumer goods": "Consumer",

        "consumer staples": "Consumer",

        "retail": "Consumer",

        "food products": "Consumer",

        "beverages": "Consumer",

        # =============================================
        # AUTO
        # =============================================

        "automobile": "Automobile",

        "auto": "Automobile",

        "auto ancillaries": "Automobile",

        "automotive": "Automobile",

        # =============================================
        # INDUSTRIALS
        # =============================================

        "capital goods": "Industrials",

        "industrial manufacturing": "Industrials",

        "engineering": "Industrials",

        "infrastructure": "Industrials",

        "construction": "Industrials",

        # =============================================
        # METALS & MATERIALS
        # =============================================

        "metals": "Metals & Mining",

        "mining": "Metals & Mining",

        "steel": "Metals & Mining",

        "cement": "Materials",

        "chemicals": "Chemicals",

        # =============================================
        # TELECOM
        # =============================================

        "telecom": "Telecommunication",

        "telecommunications": "Telecommunication",

        # =============================================
        # MEDIA
        # =============================================

        "media": "Media",

        "entertainment": "Media",

        # =============================================
        # REAL ESTATE
        # =============================================

        "real estate": "Real Estate",

        "realty": "Real Estate",

        # =============================================
        # TEXTILES
        # =============================================

        "textiles": "Textiles",

        "apparel": "Textiles"
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
# CHECK TABLES
# =========================================================

try:

    tables = conn.execute(
        '''
        SHOW TABLES
        '''
    ).fetchall()

    tables = [
        table[0]
        for table in tables
    ]

except Exception as e:

    st.error(
        f"Table Detection Failed : {e}"
    )

    st.stop()

# =========================================================
# VALIDATE DATABASE
# =========================================================

if "enriched_stocks" not in tables:

    st.error(
        """
        enriched_stocks table not found.

        Please run main.py locally first.
        """
    )

    st.stop()

# =========================================================
# LOAD MAIN DATA
# =========================================================

try:

    df = conn.execute(
        '''
        SELECT *
        FROM enriched_stocks
        '''
    ).df()

except Exception as e:

    st.error(
        f"Data Loading Failed : {e}"
    )

    st.stop()

# =========================================================
# LOAD PORTFOLIO
# =========================================================

try:

    if "institutional_portfolio" in tables:

        portfolio_df = conn.execute(
            '''
            SELECT *
            FROM institutional_portfolio
            '''
        ).df()

    else:

        portfolio_df = pd.DataFrame()

except:

    portfolio_df = pd.DataFrame()

# =========================================================
# NUMERIC CLEANING
# =========================================================

numeric_columns = [

    "Institutional Score",

    "Alpha Score",

    "RSI",

    "ADX",

    "Buy Probability",

    "Current Price",

    "Portfolio Weight"
]

for column in numeric_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(

            df[column],

            errors="coerce"
        )

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
# LIVE MARKET DATA
# =========================================================

@st.cache_data(ttl=300)

def load_live_market_data(symbols):

    return fetch_live_market_data(
        symbols
    )

if "Validated Symbol" in df.columns:

    symbols = df[
        "Validated Symbol"
    ].dropna().tolist()

else:

    symbols = df[
        "Stock"
    ].dropna().tolist()

if ENABLE_LIVE_MARKET:

    live_df = load_live_market_data(
        symbols[:5]
    )

else:

    live_df = pd.DataFrame()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "Institutional Controls"
)

# =========================================================
# SECTOR FILTER
# =========================================================

if "Sector" in df.columns:

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

else:

    selected_sector = "All"

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

if (
    selected_sector != "All"
    and "Sector" in filtered_df.columns
):

    filtered_df = filtered_df[

        filtered_df["Sector"]

        == selected_sector
    ]

if "Institutional Score" in filtered_df.columns:

    filtered_df = filtered_df[

        filtered_df[
            "Institutional Score"
        ] >= min_score
    ]

# =========================================================
# BUILD TRADE DECISIONS
# =========================================================

filtered_df = build_trade_decisions(
    filtered_df
)

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
# MARKET REGIME DISPLAY
# =========================================================

st.markdown(
    f"""
    ## Market Regime: {market_regime}
    """
)

st.markdown("---")

# =========================================================
# TOP TRADE DECISIONS
# =========================================================

st.subheader(
    "Top 50 Institutional Trade Signals"
)

priority_columns = [

    "Stock",

    "Trade Signal",

    "Current Price",

    "Target Price",

    "Stoploss",

    "Confidence"
]

available_columns = [

    column

    for column in priority_columns

    if column in filtered_df.columns
]

priority_df = filtered_df[
    available_columns
].copy()

signal_order = {

    "Strong Buy": 0,

    "Buy": 1,

    "Watch": 2,

    "Avoid": 3
}

priority_df["Signal Rank"] = priority_df[
    "Trade Signal"
].map(signal_order)

priority_df = priority_df.sort_values(

    by=[

        "Signal Rank",

        "Confidence"
    ],

    ascending=[True, False]
)

priority_df = priority_df.drop(
    columns=["Signal Rank"]
)

st.dataframe(

    priority_df.head(50),

    use_container_width=True,

    height=700
)

st.markdown("---")

# =========================================================
# KPI SECTION
# =========================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Stocks",
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

col2.metric(
    "Avg Institutional Score",
    avg_score
)

col3.metric(
    "Avg Alpha Score",
    avg_alpha
)

col4.metric(
    "Portfolio Stocks",
    len(portfolio_df)
)

st.markdown("---")

# =========================================================
# SECTOR DISTRIBUTION
# =========================================================

if "Sector" in filtered_df.columns:

    st.subheader(
        "Sector Distribution"
    )

    sector_chart = px.pie(

        filtered_df,

        names="Sector",

        title="Sector Allocation"
    )

    st.plotly_chart(
        sector_chart,
        use_container_width=True
    )

# =========================================================
# ALPHA DISTRIBUTION
# =========================================================

if "Alpha Score" in filtered_df.columns:

    st.subheader(
        "Alpha Score Distribution"
    )

    alpha_chart = px.histogram(

        filtered_df,

        x="Alpha Score",

        nbins=20,

        title="Alpha Score Distribution"
    )

    st.plotly_chart(
        alpha_chart,
        use_container_width=True
    )

# =========================================================
# PORTFOLIO SECTION
# =========================================================

st.subheader(
    "Institutional Portfolio"
)

if not portfolio_df.empty:

    display_columns = [

        column

        for column in [

            "Portfolio Rank",

            "Stock",

            "Sector",

            "Institutional Score",

            "Alpha Score",

            "Portfolio Weight"
        ]

        if column in portfolio_df.columns
    ]

    st.dataframe(

        portfolio_df[
            display_columns
        ],

        use_container_width=True
    )

# =========================================================
# TOP QUANT LEADERS
# =========================================================

st.subheader(
    "Top Quant Leaders"
)

if "Alpha Score" in filtered_df.columns:

    quant_df = filtered_df.sort_values(

        by="Alpha Score",

        ascending=False

    ).head(20)

    st.dataframe(

        quant_df,

        use_container_width=True
    )

# =========================================================
# RAW DATA
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
    "Institutional Quant Platform"
)

# =========================================================
# CLOSE DATABASE
# =========================================================

conn.close()
