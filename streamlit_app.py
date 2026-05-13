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

    .stApp {
        background-color: #0b1220;
        color: #f3f4f6;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }

    section[data-testid="stSidebar"] {

        background-color: #111827;
        border-right: 1px solid #1f2937;
    }

    section[data-testid="stSidebar"] * {

        color: #f3f4f6;
    }

    .dashboard-title {

        font-size: 46px;
        font-weight: 800;
        color: white;

        margin-bottom: 0px;
    }

    .dashboard-subtitle {

        font-size: 16px;
        color: #9ca3af;

        margin-top: -10px;
        margin-bottom: 25px;
    }

    .section-title {

        font-size: 28px;
        font-weight: 700;

        color: white;

        margin-top: 10px;
        margin-bottom: 10px;
    }

    div[data-testid="metric-container"] {

        background: linear-gradient(
            145deg,
            #111827,
            #1f2937
        );

        border: 1px solid #374151;

        padding: 14px;

        border-radius: 16px;

        box-shadow:
            0 4px 15px rgba(0,0,0,0.15);
    }

    .status-box {

        background: #111827;

        border: 1px solid #1f2937;

        padding: 18px;

        border-radius: 16px;

        margin-bottom: 18px;
    }

    .live-box {

        background-color: rgba(16,185,129,0.12);

        border: 1px solid #10b981;

        color: #10b981;

        padding: 16px;

        border-radius: 14px;

        font-weight: 600;
    }

    .closed-box {

        background-color: rgba(239,68,68,0.12);

        border: 1px solid #ef4444;

        color: #ef4444;

        padding: 16px;

        border-radius: 14px;

        font-weight: 600;
    }

    .stDataFrame {

        border-radius: 14px;

        overflow: hidden;

        border: 1px solid #1f2937;
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
    <div class="dashboard-title">
        Institutional - Quant - Urls
    </div>

    <div class="dashboard-subtitle">
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

        st.markdown(

            """
            <div class="live-box">
                🟢 Indian Market Live
            </div>
            """,

            unsafe_allow_html=True
        )

    else:

        st.markdown(

            """
            <div class="closed-box">
                🔴 Market Closed
            </div>
            """,

            unsafe_allow_html=True
        )

with col_b:

    st.markdown(

        f"""
        <div class="status-box">

        ⚡ <b>Live Quant Engine Active</b>

        <br><br>

        Universe Size: <b>{live_universe_size}</b> Stocks

        <br><br>

        Market Regime:
        <b>{market_regime}</b>

        </div>
        """,

        unsafe_allow_html=True
    )
