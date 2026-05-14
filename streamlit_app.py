# =========================================================
# INSTITUTIONAL - QUANT - URLS
# PROFESSIONAL INSTITUTIONAL DASHBOARD
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

try:

    conn = get_connection()

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
# LOAD INPUT UNIVERSE
# =========================================================

INPUT_FILE = (

    BASE_DIR

    / "input"

    / "yfinance_stock_urls.xlsx"
)

try:

    input_df = pd.read_excel(
        INPUT_FILE
    )

    total_universe = len(input_df)

except Exception:

    total_universe = len(df)

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
# LIVE UNIVERSE
# =========================================================

live_universe_size = st.sidebar.slider(

    "Live Analysis Universe",

    min_value=100,

    max_value=df["Stock"].nunique(),

    value=min(

        500,

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
# FILTER DATA
# =========================================================

filtered_df = df.copy()

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
# SORT DATA
# =========================================================

sort_column = "Institutional Score"

if "Composite Score" in filtered_df.columns:

    sort_column = "Composite Score"

filtered_df = filtered_df.sort_values(

    by=sort_column,

    ascending=False
)

# =========================================================
# LIMIT LIVE ENGINE
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

    filtered_df = build_trade_decisions(
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

    heatmap_df[
        "Avg Institutional Score"
    ]

    *

    heatmap_df[
        "Avg Confidence"
    ]
)

# =========================================================
# TOP CONVICTION PICKS
# =========================================================

top_conviction_df = filtered_df.sort_values(

    by=sort_column,

    ascending=False

).head(10)

watchlist_df = filtered_df[

    filtered_df[
        "Trade Signal"
    ].isin(

        [
            "Strong Buy",

            "Buy"
        ]
    )
].sort_values(

    by="Confidence",

    ascending=False

).head(25)

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
        f"⚡ Universe Size: {len(filtered_df)}"
    )

with status_col3:

    st.info(
        f"📊 Regime: {market_regime}"
    )

# =========================================================
# UNIVERSE METRICS
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

# =========================================================
# KPI SECTION
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
# INSTITUTIONAL HEATMAP
# =========================================================

st.markdown("---")

st.subheader(
    "Institutional Sector Heatmap"
)

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
# LOAD PRICE HISTORY
# =========================================================

@st.cache_data(ttl=1800)

def load_price_history(stock):

    try:

        symbol = stock

        if not symbol.endswith(".NS"):

            symbol = f"{symbol}.NS"

        ticker = yf.Ticker(symbol)

        hist = ticker.history(
            period="6mo"
        )

        return hist

    except Exception:

        return pd.DataFrame()

# =========================================================
# STOCK DETAIL ANALYTICS
# =========================================================

st.markdown("---")

st.subheader(
    "Institutional Stock Intelligence"
)

selected_stock = st.selectbox(

    "Select Stock",

    sorted(
        filtered_df[
            "Stock"
        ].unique()
    )
)

selected_df = filtered_df[

    filtered_df[
        "Stock"
    ] == selected_stock
]

if not selected_df.empty:

    stock_data = selected_df.iloc[0]

    detail_col1, detail_col2, detail_col3, detail_col4 = st.columns(4)

    detail_col1.metric(
        "Current Price",
        round(
            stock_data.get(
                "Current Price",
                0
            ),
            2
        )
    )

    detail_col2.metric(
        "Institutional Score",
        round(
            stock_data.get(
                "Institutional Score",
                0
            ),
            2
        )
    )

    detail_col3.metric(
        "Confidence",
        round(
            stock_data.get(
                "Confidence",
                0
            ),
            2
        )
    )

    detail_col4.metric(
        "Trade Signal",
        stock_data.get(
            "Trade Signal",
            "N/A"
        )
    )

# =========================================================
# PRICE VS TARGET
# =========================================================

if not selected_df.empty:

    price_data = pd.DataFrame({

        "Type": [

            "Current Price",

            "Target Price",

            "Stoploss"
        ],

        "Value": [

            stock_data.get(
                "Current Price",
                0
            ),

            stock_data.get(
                "Target Price",
                0
            ),

            stock_data.get(
                "Stoploss",
                0
            )
        ]
    })

    fig_price = px.bar(

        price_data,

        x="Type",

        y="Value",

        title=f"{selected_stock} Price Analysis",

        text_auto=True
    )

    st.plotly_chart(
        fig_price,
        use_container_width=True
    )

# =========================================================
# TECHNICAL ANALYSIS
# =========================================================

st.markdown("---")

st.subheader(
    "Technical Price Analysis"
)

hist_df = load_price_history(
    selected_stock
)

if not hist_df.empty:

    hist_df["MA20"] = (

        hist_df["Close"]

        .rolling(20)

        .mean()
    )

    hist_df["MA50"] = (

        hist_df["Close"]

        .rolling(50)

        .mean()
    )

    delta = hist_df["Close"].diff()

    gain = (

        delta.where(
            delta > 0,
            0
        )

        .rolling(14)

        .mean()
    )

    loss = (

        -delta.where(
            delta < 0,
            0
        )

        .rolling(14)

        .mean()
    )

    rs = gain / loss

    hist_df["RSI"] = (

        100

        - (
            100
            / (1 + rs)
        )
    )

    ema12 = hist_df["Close"].ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = hist_df["Close"].ewm(
        span=26,
        adjust=False
    ).mean()

    hist_df["MACD"] = ema12 - ema26

    hist_df["Signal"] = (

        hist_df["MACD"]

        .ewm(
            span=9,
            adjust=False
        )

        .mean()
    )

    fig = make_subplots(

        rows=4,

        cols=1,

        shared_xaxes=True,

        vertical_spacing=0.03,

        row_heights=[

            0.5,

            0.15,

            0.15,

            0.2
        ]
    )

    fig.add_trace(

        go.Candlestick(

            x=hist_df.index,

            open=hist_df["Open"],

            high=hist_df["High"],

            low=hist_df["Low"],

            close=hist_df["Close"],

            name="Price"
        ),

        row=1,

        col=1
    )

    fig.add_trace(

        go.Scatter(

            x=hist_df.index,

            y=hist_df["MA20"],

            mode="lines",

            name="MA20"
        ),

        row=1,

        col=1
    )

    fig.add_trace(

        go.Scatter(

            x=hist_df.index,

            y=hist_df["MA50"],

            mode="lines",

            name="MA50"
        ),

        row=1,

        col=1
    )

    fig.add_trace(

        go.Bar(

            x=hist_df.index,

            y=hist_df["Volume"],

            name="Volume"
        ),

        row=2,

        col=1
    )

    fig.add_trace(

        go.Scatter(

            x=hist_df.index,

            y=hist_df["RSI"],

            mode="lines",

            name="RSI"
        ),

        row=3,

        col=1
    )

    fig.add_trace(

        go.Scatter(

            x=hist_df.index,

            y=hist_df["MACD"],

            mode="lines",

            name="MACD"
        ),

        row=4,

        col=1
    )

    fig.add_trace(

        go.Scatter(

            x=hist_df.index,

            y=hist_df["Signal"],

            mode="lines",

            name="Signal"
        ),

        row=4,

        col=1
    )

    fig.update_layout(

        height=1100,

        title=f"{selected_stock} Institutional Technical Analysis",

        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(

        fig,

        use_container_width=True
    )

# =========================================================
# TOP CONVICTION PICKS
# =========================================================

st.markdown("---")

st.subheader(
    "Top Institutional Conviction Picks"
)

conviction_columns = [

    "Stock",

    "Sector",

    "Trade Signal",

    "Current Price",

    "Confidence",

    sort_column
]

available_conviction_columns = [

    col

    for col in conviction_columns

    if col in top_conviction_df.columns
]

st.dataframe(

    top_conviction_df[
        available_conviction_columns
    ],

    use_container_width=True,

    height=350
)

# =========================================================
# INSTITUTIONAL WATCHLIST
# =========================================================

st.markdown("---")

st.subheader(
    "Institutional Watchlist"
)

watchlist_columns = [

    "Stock",

    "Sector",

    "Trade Signal",

    "Current Price",

    "Confidence",

    "Institutional Score"
]

available_watchlist_columns = [

    col

    for col in watchlist_columns

    if col in watchlist_df.columns
]

st.dataframe(

    watchlist_df[
        available_watchlist_columns
    ],

    use_container_width=True,

    height=450
)

# =========================================================
# DOWNLOADS
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

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl"
    ) as writer:

        filtered_df.to_excel(
            writer,
            index=False
        )

    excel_buffer.seek(0)

    st.download_button(

        label="📥 Download Excel",

        data=excel_buffer,

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
