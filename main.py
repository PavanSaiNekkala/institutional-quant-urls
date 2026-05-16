# =========================================================
# INSTITUTIONAL QUANT PLATFORM
# FINAL PRODUCTION MAIN.PY
# =========================================================

import time
import traceback
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import yfinance as yf

# =========================================================
# BASE PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / "cache"
DB_DIR = BASE_DIR / "database"

OUTPUT_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# =========================================================
# DATABASE
# =========================================================

DB_PATH = DB_DIR / "institutional_quant.db"

conn = duckdb.connect(str(DB_PATH))

# =========================================================
# INPUT FILE
# =========================================================

INPUT_XLSX = INPUT_DIR / "yfinance_stock_urls.xlsx"

# =========================================================
# LOAD XLSX INPUT
# =========================================================

def load_stock_input():

    try:

        print("=" * 60)
        print("LOADING XLSX INPUT")
        print("=" * 60)

        if not INPUT_XLSX.exists():

            print(f"INPUT FILE NOT FOUND : {INPUT_XLSX}")

            return pd.DataFrame()

        df = pd.read_excel(INPUT_XLSX)

        if df.empty:

            print("INPUT XLSX EMPTY")

            return pd.DataFrame()

        required_columns = [
            "Stock"
        ]

        missing_columns = [

            col for col in required_columns
            if col not in df.columns

        ]

        if missing_columns:

            print(f"MISSING COLUMNS : {missing_columns}")

            return pd.DataFrame()

        df["Stock"] = (

            df["Stock"]

            .astype(str)

            .str.strip()

            .str.upper()

        )

        df = (

            df

            .drop_duplicates(subset=["Stock"])

            .reset_index(drop=True)

        )

        print(f"TOTAL STOCKS LOADED : {len(df)}")

        return df

    except Exception as e:

        print(f"XLSX LOAD FAILED : {e}")

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

# =========================================================
# PROCESS STOCKS
# =========================================================

results = []

print("=" * 60)
print("STARTING PIPELINE")
print("=" * 60)

for idx, row in stock_input_df.iterrows():

    stock = row["Stock"]

    try:

        print("=" * 60)
        print(f"PROCESSING : {stock}")
        print("=" * 60)

        ticker = yf.Ticker(stock)

        info = ticker.info

        hist = ticker.history(
            period="6mo",
            auto_adjust=True
        )

        if hist.empty:

            print(f"NO HISTORY : {stock}")

            continue

        close_prices = hist["Close"]

        current_price = round(

            float(close_prices.iloc[-1]),

            2

        )

        previous_close = round(

            float(close_prices.iloc[-2]),

            2

        ) if len(close_prices) > 1 else current_price

        returns_1m = (

            (
                close_prices.iloc[-1]
                / close_prices.iloc[-22]
            ) - 1

            if len(close_prices) > 22

            else 0

        )

        returns_3m = (

            (
                close_prices.iloc[-1]
                / close_prices.iloc[-66]
            ) - 1

            if len(close_prices) > 66

            else 0

        )

        returns_6m = (

            (
                close_prices.iloc[-1]
                / close_prices.iloc[0]
            ) - 1

            if len(close_prices) > 1

            else 0

        )

        volume = info.get(
            "volume",
            0
        )

        avg_volume = info.get(
            "averageVolume",
            0
        )

        market_cap = info.get(
            "marketCap",
            0
        )

        pe_ratio = info.get(
            "trailingPE",
            0
        )

        pb_ratio = info.get(
            "priceToBook",
            0
        )

        eps = info.get(
            "trailingEps",
            0
        )

        beta = info.get(
            "beta",
            0
        )

        roe = info.get(
            "returnOnEquity",
            0
        )

        sector = info.get(
            "sector",
            "Unknown"
        )

        industry = info.get(
            "industry",
            "Unknown"
        )

        dividend_yield = info.get(
            "dividendYield",
            0
        )

        institutional_score = 50

        # =================================================
        # INSTITUTIONAL LOGIC
        # =================================================

        if market_cap > 50_000_000_000:

            institutional_score += 20

        elif market_cap > 10_000_000_000:

            institutional_score += 10

        if volume > 1_000_000:

            institutional_score += 15

        elif volume > 250_000:

            institutional_score += 8

        if returns_1m > 0.05:

            institutional_score += 10

        if returns_3m > 0.10:

            institutional_score += 10

        if pe_ratio > 0 and pe_ratio < 35:

            institutional_score += 5

        if pb_ratio > 0 and pb_ratio < 10:

            institutional_score += 5

        if roe and roe > 0.15:

            institutional_score += 10

        if eps and eps > 0:

            institutional_score += 5

        institutional_score = min(
            institutional_score,
            100
        )

        confidence = round(
            institutional_score * 0.93,
            2
        )

        buy_probability = round(
            confidence * 0.95,
            2
        )

        # =================================================
        # TRADE SIGNAL
        # =================================================

        if confidence >= 85:

            trade_signal = "STRONG BUY"

        elif confidence >= 75:

            trade_signal = "BUY"

        elif confidence >= 65:

            trade_signal = "WATCH"

        elif confidence >= 50:

            trade_signal = "HOLD"

        else:

            trade_signal = "AVOID"

        composite_score = round(

            (
                institutional_score
                + confidence
                + buy_probability
            ) / 3,

            2

        )

        results.append({

            "Stock": stock,

            "Sector": sector,

            "Industry": industry,

            "Current Price": current_price,

            "Previous Close": previous_close,

            "Volume": volume,

            "Average Volume": avg_volume,

            "Market Cap": market_cap,

            "PE Ratio": pe_ratio,

            "PB Ratio": pb_ratio,

            "EPS": eps,

            "ROE": roe,

            "Beta": beta,

            "Dividend Yield": dividend_yield,

            "1M Return": round(
                returns_1m * 100,
                2
            ),

            "3M Return": round(
                returns_3m * 100,
                2
            ),

            "6M Return": round(
                returns_6m * 100,
                2
            ),

            "Institutional Score": institutional_score,

            "Confidence": confidence,

            "Buy Probability": buy_probability,

            "Composite Score": composite_score,

            "Trade Signal": trade_signal

        })

        print(f"SUCCESS : {stock}")

        time.sleep(0.10)

    except Exception as e:

        print(f"FAILED : {stock}")

        print(str(e))

        continue

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

    final_df = pd.DataFrame(columns=[

        "Stock",
        "Trade Signal",
        "Institutional Score",
        "Confidence",
        "Current Price"

    ])

# =========================================================
# CLEAN DATA
# =========================================================

final_df = (

    final_df

    .drop_duplicates(subset=["Stock"])

    .fillna(0)

    .reset_index(drop=True)

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

        export_path = OUTPUT_DIR / filename

        dataframe.to_csv(

            export_path,

            index=False

        )

        print(f"EXPORTED : {filename}")

    except Exception as e:

        print(f"EXPORT FAILED : {filename}")

        print(str(e))

# =========================================================
# SAVE DUCKDB
# =========================================================

try:

    if not final_df.empty:

        conn.execute(
            "DROP TABLE IF EXISTS enriched_stocks"
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

    print(f"DUCKDB SAVE FAILED : {e}")

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

    print(f"PARQUET FAILED : {e}")

# =========================================================
# FINAL SUMMARY
# =========================================================

print("=" * 60)

print(
    f"FINAL STOCK COUNT : {len(final_df)}"
)

print(
    f"TOP PICKS COUNT : {len(top_picks_df)}"
)

print(
    f"PORTFOLIO COUNT : {len(portfolio_df)}"
)

print("=" * 60)

print("PIPELINE COMPLETED")

print("=" * 60)
