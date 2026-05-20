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

# =========================================================
# UNIVERSAL DATA LOADER
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
                    encoding="utf-8",
                    low_memory=False,
                    on_bad_lines="skip"
                )

            except Exception:

                df = pd.read_csv(
                    data_file,
                    encoding="latin1",
                    low_memory=False,
                    on_bad_lines="skip"
                )

        # =====================================================
        # GZIP CSV
        # =====================================================

        elif suffix.endswith(".gz"):

            try:

                df = pd.read_csv(
                    data_file,
                    compression="gzip",
                    encoding="utf-8",
                    low_memory=False,
                    on_bad_lines="skip"
                )

            except Exception:

                df = pd.read_csv(
                    data_file,
                    compression="gzip",
                    encoding="latin1",
                    low_memory=False,
                    on_bad_lines="skip"
                )

        # =====================================================
        # EXCEL
        # =====================================================

        elif (
            suffix.endswith(".xlsx")
            or
            suffix.endswith(".xls")
        ):

            df = pd.read_excel(
                data_file,
                engine="openpyxl"
            )

        # =====================================================
        # PARQUET
        # =====================================================

        elif suffix.endswith(".parquet"):

            df = pd.read_parquet(data_file)

        # =====================================================
        # UNKNOWN
        # =====================================================

        else:

            st.error(
                f"Unsupported file format : {data_file}"
            )

            return pd.DataFrame()

        # =====================================================
        # EMPTY CHECK
        # =====================================================

        if df.empty:

            return pd.DataFrame()

        # =====================================================
        # REMOVE DUPLICATE COLUMNS
        # =====================================================

        df = df.loc[:, ~df.columns.duplicated()]

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
            "Momentum": 0,
            "Volume Score": 50

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
            "Momentum",
            "Volume Score"

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

        # =====================================================
        # REMOVE EMPTY STOCKS
        # =====================================================

        df = df[

            df["Stock"]

            .astype(str)

            .str.strip()

            != ""

        ]

        return df

    except Exception as e:

        st.error(
            f"DATA LOAD FAILED : {e}"
        )

        return pd.DataFrame()

# =========================================================
# LOAD DATA
# =========================================================

possible_files = [

    OUTPUT_DIR / "enriched_stock_data.csv.gz",

    OUTPUT_DIR / "enriched_stock_data.csv",

    OUTPUT_DIR / "institutional_quant.xlsx",

    BASE_DIR / "institutional_quant.xlsx",

    Path("/mount/src/institutional-quant-urls/output/enriched_stock_data.csv.gz")

]

df = pd.DataFrame()

loaded_file = None

for file_path in possible_files:

    try:

        if file_path.exists():

            df = load_data(file_path)

            if not df.empty:

                loaded_file = file_path

                break

    except Exception:
        pass

# =========================================================
# EMPTY DATA CHECK
# =========================================================

if df.empty:

    st.error(
        """
        DATA LOAD FAILED :
        No valid institutional dataset found.
        """
    )

    st.stop()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("Institutional Controls")

st.sidebar.success(
    f"Loaded : {loaded_file.name}"
)

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
    "BUY": "#00CC44",
    "WATCH": "#FF9900",
    "HOLD": "#3399FF",
    "AVOID": "#FF3333"

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

# =========================================================
# MARKET REGIME
# =========================================================

try:

    from market_regime import get_market_regime

    regime, regime_color, regime_details = get_market_regime()

except Exception:

    regime = "SIDEWAYS"

    regime_color = "#FF9900"

    regime_details = {}

# =========================================================
# FILTERS
# =========================================================

filtered_df = df.copy()

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

if len(selected_trade_signal) > 0:

    filtered_df = filtered_df[

        filtered_df["Trade Signal"]

        .isin(selected_trade_signal)

    ]

filtered_df = filtered_df[

    filtered_df["Institutional Score"] >= min_score

]

filtered_df = filtered_df[

    filtered_df["Confidence"] >= min_confidence

]

# =========================================================
# HEADER
# =========================================================

st.title("🏦 Institutional Quant Platform")

st.caption(
    "AI Powered Institutional Analytics Engine"
)

# =========================================================
# REGIME BANNER
# =========================================================

st.markdown(
    f"""
    <div style="
        background-color:{regime_color};
        padding:18px;
        border-radius:12px;
        text-align:center;
        font-size:30px;
        font-weight:bold;
        color:white;
        margin-bottom:25px;
    ">
        MARKET REGIME : {regime}
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# METRICS
# =========================================================

strong_buy_count = len(
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

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Strong Buy Stocks",
        strong_buy_count
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
# PIE CHART
# =========================================================

st.markdown("---")

st.subheader("Trade Signal Distribution")

signal_chart = px.pie(
    filtered_df,
    names="Trade Signal",
    color="Trade Signal",
    color_discrete_map=signal_colors
)

signal_chart.update_traces(
    textposition="inside",
    textinfo="percent+label"
)

st.plotly_chart(
    signal_chart,
    width="stretch"
)

# =========================================================
# TOP STOCKS
# =========================================================

st.markdown("---")

st.subheader("Top Institutional Opportunities")

display_columns = [

    "Stock",
    "Sector",
    "Trade Signal",
    "Institutional Score",
    "Confidence",
    "RSI",
    "Current Price"

]

available_columns = [

    col

    for col in display_columns

    if col in filtered_df.columns

]

top_df = filtered_df.sort_values(
    by="Institutional Score",
    ascending=False
)

st.dataframe(
    top_df[available_columns],
    width="stretch",
    hide_index=True
)
