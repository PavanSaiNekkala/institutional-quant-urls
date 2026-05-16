# =========================================================
# INSTITUTIONAL QUANT PLATFORM
# FINAL PRODUCTION-GRADE MAIN.PY
# =========================================================

import sys
import time
import traceback
from pathlib import Path
from concurrent.futures import
    ThreadPoolExecutor,
    as_completed
)

import duckdb
import numpy as np
import pandas as pd
import requests
import yfinance as yf

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD
from ta.volatility import AverageTrueRange
# =========================================================
# BASE PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / "cache"
DB_DIR = BASE_DIR / "database"
LOG_DIR = BASE_DIR / "logs"

OUTPUT_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# =========================================================
# DATABASE
# =========================================================

DB_PATH = DB_DIR / "institutional_quant.db"

conn = duckdb.connect(
    str(DB_PATH),
    read_only=False
)

# =========================================================
# INPUT FILE
# =========================================================

INPUT_XLSX = (
    INPUT_DIR /
    "yfinance_stock_urls.xlsx"
)

# =========================================================
# REQUEST SESSION
# =========================================================

HEADERS = {

    "User-Agent": (

        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"

    )

}

def create_session():

    session = requests.Session()

    retries = Retry(

        total=3,

        backoff_factor=1,

        status_forcelist=[
            429,
            500,
            502,
            503,
            504
        ]

    )

    adapter = HTTPAdapter(
        max_retries=retries
    )

    session.mount(
        "https://",
        adapter
    )

    session.mount(
        "http://",
        adapter
    )

    session.headers.update(
        HEADERS
    )

    return session

SESSION = create_session()

# =========================================================
# LOAD XLSX INPUT
# =========================================================

def load_stock_input():

    try:

        print("=" * 60)
        print("LOADING XLSX INPUT")
        print("=" * 60)

        if not INPUT_XLSX.exists():

            print(
                f"INPUT FILE NOT FOUND : "
                f"{INPUT_XLSX}"
            )

            return pd.DataFrame()

        df = pd.read_excel(
            INPUT_XLSX
        )

        if df.empty:

            print("INPUT XLSX EMPTY")

            return pd.DataFrame()

        df.columns = [
            c.strip()
            for c in df.columns
        ]

        required_columns = [
            "Stock"
        ]

        missing_columns = [

            col

            for col
            in required_columns

            if col not in df.columns

        ]

        if missing_columns:

            print(
                f"MISSING COLUMNS : "
                f"{missing_columns}"
            )

            return pd.DataFrame()

        df["Stock"] = (

            df["Stock"]

            .astype(str)

            .str.strip()

            .str.upper()

        )

        df = (

            df

            .dropna(subset=["Stock"])

            .drop_duplicates(
                subset=["Stock"]
            )

            .reset_index(drop=True)

        )

        print(
            f"TOTAL STOCKS LOADED : "
            f"{len(df)}"
        )

        return df

    except Exception as e:

        print(
            f"XLSX LOAD FAILED : {e}"
        )

        traceback.print_exc()

        return pd.DataFrame()

# =========================================================
# LOAD INPUT
# =========================================================

stock_input_df = load_stock_input()

# =========================================================
# EMPTY INPUT SAFETY
# =========================================================

if stock_input_df.empty:

    print("=" * 60)
    print("NO STOCK INPUT AVAILABLE")
    print("=" * 60)

    sys.exit(0)

# =========================================================
# TRADE SIGNAL CLASSIFIER
# =========================================================

def classify_signal(confidence):

    if confidence >= 85:

        return "STRONG BUY"

    elif confidence >= 75:

        return "BUY"

    elif confidence >= 65:

        return "WATCH"

    elif confidence >= 50:

        return "HOLD"

    else:

        return "AVOID"

# =========================================================
# PROCESS SINGLE STOCK
# =========================================================

def process_stock(row):

    stock = row["Stock"]

    try:

        print("=" * 60)
        print(f"PROCESSING : {stock}")
        print("=" * 60)

        time.sleep(0.15)

        ticker = yf.Ticker(
            stock,
            session=SESSION
        )

        # =================================================
        # FAST INFO
        # =================================================

        try:

            info = ticker.fast_info

        except Exception:

            info = {}

        # =================================================
        # HISTORY
        # =================================================

        try:

            hist = ticker.history(

                period="6mo",

                auto_adjust=True,

                timeout=20

            )

        except Exception:

            print(
                f"HISTORY FAILED : "
                f"{stock}"
            )

            return None

        if hist.empty:

            print(
                f"NO HISTORY : {stock}"
            )

            return None

        close_prices = hist["Close"]
        # =========================================================
        # TECHNICAL INDICATORS
        # =========================================================

        rsi = RSIIndicator(
            close_prices,
            window=14
        ).rsi().iloc[-1]

        sma_20 = SMAIndicator(
            close_prices,
            window=20
        ).sma_indicator().iloc[-1]

        sma_50 = SMAIndicator(
            close_prices,
            window=50
        ).sma_indicator().iloc[-1]

        macd = MACD(
            close_prices
        ).macd().iloc[-1]

        atr = AverageTrueRange(
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"]
        ).average_true_range().iloc[-1]

        if close_prices.empty:

            print(
                f"EMPTY CLOSE DATA : "
                f"{stock}"
            )

            return None

        # =================================================
        # PRICE METRICS
        # =================================================

        current_price = round(
            float(close_prices.iloc[-1]),
            2
        )

        previous_close = round(

            float(close_prices.iloc[-2]),

            2

        ) if len(close_prices) > 1 else current_price

        # =================================================
        # RETURNS
        # =================================================

        returns_1m = (

            (
                close_prices.iloc[-1]
                /
                close_prices.iloc[-22]
            ) - 1

            if len(close_prices) > 22

            else 0

        )

        returns_3m = (

            (
                close_prices.iloc[-1]
                /
                close_prices.iloc[-66]
            ) - 1

            if len(close_prices) > 66

            else 0

        )

        returns_6m = (

            (
                close_prices.iloc[-1]
                /
                close_prices.iloc[0]
            ) - 1

            if len(close_prices) > 1

            else 0

        )

        # =================================================
        # INFO METRICS
        # =================================================

        volume = info.get(
            "lastVolume",
            0
        )

        market_cap = info.get(
            "marketCap",
            0
        )

        day_high = info.get(
            "dayHigh",
            0
        )

        day_low = info.get(
            "dayLow",
            0
        )

        year_high = info.get(
            "yearHigh",
            0
        )

        year_low = info.get(
            "yearLow",
            0
        )

        # =========================================================
        # MULTI FACTOR SCORING
        # =========================================================

        institutional_score = 0

        # ---------------------------------------------------------
        # MARKET CAP
        # ---------------------------------------------------------

        if market_cap > 500_000_000_000:

            institutional_score += 25

        elif market_cap > 100_000_000_000:

            institutional_score += 18

        elif market_cap > 10_000_000_000:

            institutional_score += 10

        # ---------------------------------------------------------
        # LIQUIDITY
        # ---------------------------------------------------------

        if volume > 5_000_000:

            institutional_score += 20

        elif volume > 1_000_000:

            institutional_score += 15
        
        elif volume > 250_000:

            institutional_score += 8

        # ---------------------------------------------------------
        # MOMENTUM
        # ---------------------------------------------------------

        if returns_1m > 0.05:

            institutional_score += 10

        if returns_3m > 0.10:

            institutional_score += 10

        if returns_6m > 0.20:

            institutional_score += 10

        # ---------------------------------------------------------
        # RSI
        # ---------------------------------------------------------

        if 45 <= rsi <= 70:

            institutional_score += 10

        elif rsi > 80:

            institutional_score -= 5

        # ---------------------------------------------------------
        # TREND STRENGTH
        # ---------------------------------------------------------

        if current_price > sma_20:

            institutional_score += 5
        
        if current_price > sma_50:

            institutional_score += 5

        # ---------------------------------------------------------
        # MACD
        # ---------------------------------------------------------

        if macd > 0:

            institutional_score += 5

        # ---------------------------------------------------------
        # VOLATILITY
        # ---------------------------------------------------------

        if atr < current_price * 0.04:

            institutional_score += 5

        # ---------------------------------------------------------
        # LIMIT SCORE
        # ---------------------------------------------------------

        institutional_score = max(
            0,
            min(institutional_score, 100)
        )

        # =================================================
        # CONFIDENCE
        # =================================================

        confidence = round(

            (
                institutional_score
                * 0.95
            ),

            2

        
        )

        buy_probability = round(
            confidence * 0.95,
            2
        )

        trade_signal = classify_signal(
            confidence
        )

        composite_score = round(

            (
                institutional_score
                +
                confidence
                +
                buy_probability
            ) / 3,

            2

        )

        # =================================================
        # RESULT
        # =================================================

        result = {

                "Stock": stock,

                "Current Price":
                current_price,

                "Previous Close":
                previous_close,

                "Volume":
                volume,

                "Market Cap":
                market_cap,

                "Day High":
                day_high,

                "Day Low":
                day_low,

                "52W High":
                year_high,

                "52W Low":
                year_low,

                "1M Return":
                round(
                        returns_1m * 100,
                        2
                ),

                "3M Return":
                round(
                        returns_3m * 100,
                        2
                ),

                "6M Return":
                round(
                        returns_6m * 100,
                        2
                ),

                # =====================================================
                # TECHNICAL INDICATORS
                # =====================================================

                "RSI":
                round(
                        rsi,
                        2
                ),

                "SMA20":
                round(
                        sma_20,
                        2
                ),

                "SMA50":
                round(
                        sma_50,
                        2
                ),

                "MACD":
                round(
                        macd,
                        2
                ),

                "ATR":
                round(
                        atr,
                        2
                ),

                # =====================================================
                # SCORING
                # =====================================================

                "Institutional Score":
                institutional_score,

                "Confidence":
                confidence,

                "Buy Probability":
                buy_probability,

                "Composite Score":
                composite_score,

                "Trade Signal":
                trade_signal

        }
        print(f"SUCCESS : {stock}")

        return result

    except Exception as e:

        print(f"FAILED : {stock}")

        print(str(e))

        return None

# =========================================================
# FAST PARALLEL ENGINE
# =========================================================

results = []

success_count = 0
failed_count = 0

print("=" * 60)
print("STARTING FAST PARALLEL PIPELINE")
print("=" * 60)

MAX_WORKERS = min(
    25,
    len(stock_input_df)
)

with ThreadPoolExecutor(
    max_workers=MAX_WORKERS
) as executor:

    futures = [

        executor.submit(
            process_stock,
            row
        )

        for _, row
        in stock_input_df.iterrows()

    ]

    for future in as_completed(futures):

        try:

            result = future.result()

            if result is not None:

                results.append(result)

                success_count += 1

            else:

                failed_count += 1

        except Exception as e:

            failed_count += 1

            print(
                f"THREAD ERROR : {e}"
            )

# =========================================================
# CREATE DATAFRAME
# =========================================================

final_df = pd.DataFrame(results)

# =========================================================
# EMPTY DATAFRAME SAFETY
# =========================================================

if final_df.empty:

    print("=" * 60)
    print("NO VALID STOCK DATA GENERATED")
    print("=" * 60)

    sys.exit(0)

# =========================================================
# CLEAN DATA
# =========================================================

final_df = (

    final_df

    .drop_duplicates(
        subset=["Stock"]
    )

    .fillna(0)

    .reset_index(drop=True)

)
# =========================================================
# SECTOR RELATIVE STRENGTH ENGINE
# =========================================================

try:

        # -----------------------------
        # ENSURE SECTOR COLUMN EXISTS
        # -----------------------------

        if "Sector" not in final_df.columns:

                final_df["Sector"] = "Unknown"

        # -----------------------------
        # ENSURE RETURN COLUMNS EXIST
        # -----------------------------

        required_return_cols = [
                "1M Return",
                "3M Return",
                "6M Return"
        ]

        for col in required_return_cols:

                if col not in final_df.columns:

                        final_df[col] = 0

        # -----------------------------
        # SECTOR RANK
        # -----------------------------

        final_df["Sector Rank"] = (

                final_df

                .groupby("Sector")[
                        "Institutional Score"
                ]

                .rank(
                        ascending=False,
                        method="dense"
                )

        )

        # -----------------------------
        # SECTOR PERCENTILE
        # -----------------------------

        final_df["Sector Percentile"] = (

                final_df

                .groupby("Sector")[
                        "Institutional Score"
                ]

                .rank(
                        pct=True
                ) * 100

        ).round(2)

        # -----------------------------
        # MARKET LEADER
        # -----------------------------

        final_df["Market Leader"] = np.where(

                final_df["Sector Percentile"] >= 90,

                "YES",

                "NO"

        )

        # -----------------------------
        # RELATIVE STRENGTH SCORE
        # -----------------------------

        final_df["Relative Strength Score"] = (

                (
                        final_df["1M Return"] * 0.3
                        +
                        final_df["3M Return"] * 0.3
                        +
                        final_df["6M Return"] * 0.4
                )

        ).round(2)

        # -----------------------------
        # ELITE STOCK
        # -----------------------------

        if "Trade Signal" not in final_df.columns:

                final_df["Trade Signal"] = "WATCH"

        final_df["Elite Stock"] = np.where(

                (
                        (final_df["Institutional Score"] >= 85)
                        &
                        (final_df["Relative Strength Score"] >= 15)
                        &
                        (
                                final_df["Trade Signal"]
                                == "STRONG BUY"
                        )
                ),

                "YES",

                "NO"

        )

        print(
                "SECTOR ENGINE COMPLETED"
        )

except Exception as e:

        print(
                f"SECTOR ENGINE FAILED : {e}"
        )
# =========================================================
# SECTOR RELATIVE STRENGTH
# =========================================================

if "Sector" in final_df.columns:

        final_df["Sector Rank"] = (

                final_df

                .groupby("Sector")[
                        "Institutional Score"
                ]

                .rank(

                        ascending=False,

                        method="dense"

                )

        )

        final_df["Sector Percentile"] = (

                final_df

                .groupby("Sector")[
                        "Institutional Score"
                ]

                .rank(
                        pct=True
                ) * 100

        ).round(2)
# =========================================================
# MARKET LEADER
# =========================================================

final_df["Market Leader"] = np.where(

        (
                final_df[
                        "Sector Percentile"
                ] >= 90
        ),

        "YES",

        "NO"

)
# =========================================================
# RELATIVE STRENGTH SCORE
# =========================================================

final_df["Relative Strength Score"] = (

        (
                final_df["1M Return"] * 0.3
                +
                final_df["3M Return"] * 0.3
                +
                final_df["6M Return"] * 0.4
        )

).round(2)
# =========================================================
# ELITE STOCKS
# =========================================================

final_df["Elite Stock"] = np.where(

        (
                (final_df["Institutional Score"] >= 85)
                &
                (final_df["Relative Strength Score"] >= 15)
                &
                (final_df["Trade Signal"] == "STRONG BUY")
        ),

        "YES",

        "NO"

)
# =========================================================
# SORTING
# =========================================================

if "Composite Score" in final_df.columns:

    final_df = final_df.sort_values(

        by="Composite Score",

        ascending=False

    )

# =========================================================
# TOP PICKS
# =========================================================

top_picks_df = final_df.head(100)

portfolio_df = top_picks_df.copy()

# =========================================================
# EXPORT CSV
# =========================================================

csv_exports = {

    "enriched_stock_data.csv":
    final_df,

    "institutional_portfolio.csv":
    portfolio_df,

    "top_institutional_picks.csv":
    top_picks_df

}

print("=" * 60)
print("EXPORTING CSV FILES")
print("=" * 60)

for filename, dataframe in csv_exports.items():

    try:

        export_path = (
            OUTPUT_DIR /
            filename
        )

        dataframe.to_csv(

            export_path,

            index=False

        )

        print(
            f"EXPORTED : "
            f"{filename}"
        )

    except Exception as e:

        print(
            f"EXPORT FAILED : "
            f"{filename}"
        )

        print(str(e))

# =========================================================
# SAVE DUCKDB
# =========================================================

try:

    conn.execute(
        """
        DROP TABLE IF EXISTS
        enriched_stocks
        """
    )

    conn.register(
        "final_df",
        final_df
    )

    conn.execute(
        """
        CREATE TABLE enriched_stocks AS
        SELECT * FROM final_df
        """
    )

    print("DUCKDB SAVED")

except Exception as e:

    print(
        f"DUCKDB SAVE FAILED : {e}"
    )

# =========================================================
# SAVE PARQUET
# =========================================================

try:

    parquet_path = (

        OUTPUT_DIR /
        "institutional_quant.parquet"

    )

    final_df.to_parquet(

        parquet_path,

        index=False

    )

    print("PARQUET SAVED")

except Exception as e:

    print(
        f"PARQUET FAILED : {e}"
    )

# =========================================================
# SAVE EXCEL
# =========================================================

try:

    excel_path = (

        OUTPUT_DIR /
        "institutional_quant.xlsx"

    )

    final_df.to_excel(

        excel_path,

        index=False

    )

    print("EXCEL SAVED")

except Exception as e:

    print(
        f"EXCEL FAILED : {e}"
    )

# =========================================================
# FINAL SUMMARY
# =========================================================

print("=" * 60)

print(
    f"FINAL STOCK COUNT : "
    f"{len(final_df)}"
)

print(
    f"TOP PICKS COUNT : "
    f"{len(top_picks_df)}"
)

print(
    f"PORTFOLIO COUNT : "
    f"{len(portfolio_df)}"
)

print(
    f"SUCCESS COUNT : "
    f"{success_count}"
)

print(
    f"FAILED COUNT : "
    f"{failed_count}"
)

print(

    f"SUCCESS RATE : "

    f"{round((success_count / max(len(stock_input_df),1))*100,2)}%"

)

print("=" * 60)

print("PIPELINE COMPLETED")

print("=" * 60)

conn.close()
