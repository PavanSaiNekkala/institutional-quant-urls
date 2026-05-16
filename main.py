# =========================================================
# INSTITUTIONAL QUANT PLATFORM
# FINAL PRODUCTION MAIN.PY
# =========================================================

import os
import time
import json
import traceback
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
# REQUEST HEADERS
# =========================================================

HEADERS = {

    "User-Agent": (

        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"

    )

}

# =========================================================
# LOAD XLSX INPUT
# =========================================================

def load_stock_input():

    try:

        print("=" * 60)
        print("LOADING XLSX INPUT")
        print("=" * 60)

        if not INPUT_XLSX.exists():

            print("INPUT FILE NOT FOUND")

            return pd.DataFrame()

        df = pd.read_excel(INPUT_XLSX)

        if df.empty:

            print("INPUT XLSX EMPTY")

            return pd.DataFrame()

        required_columns = [

            "Stock",
            "QuoteAPI",
            "ChartAPI",
            "FinancialsAPI",
            "InstitutionalHoldersAPI",
            "RecommendationsAPI"

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

    try:

        stock = row["Stock"]

        quote_api = row["QuoteAPI"]

        print("=" * 60)
        print(f"PROCESSING : {stock}")
        print("=" * 60)

        session = requests.Session()
        retry_strategy = Retry(

            total=3,

            backoff_factor=1,

            status_forcelist=[429, 500, 502, 503, 504],

            allowed_methods=["GET"]

        )

        adapter = HTTPAdapter(

            max_retries=retry_strategy
        )

        session.mount("https://", adapter)
        session.mount("http://", adapter)

        session.headers.update(HEADERS)
        
        try:

            response = session.get(

                quote_api,

                timeout=30

            )

            if response.status_code != 200:

                print(
                    f"API FAILED : {stock} | "
                    f"STATUS : {response.status_code}"
                )

                time.sleep(0.5)

                continue

            try:

                quote_json = response.json()
        
            except Exception:

                print(f"INVALID JSON : {stock}")

                continue
        
        except requests.exceptions.Timeout:

            print(f"TIMEOUT : {stock}")

            continue

        except requests.exceptions.ConnectionError:

            print(f"CONNECTION ERROR : {stock}")

            continue

        except Exception as e:

            print(f"REQUEST FAILED : {stock}")

            print(str(e))

            continue

        quote_result = (

            quote_json

            .get("quoteResponse", {})

            .get("result", [])

        )

        if not quote_result:

            print(f"NO QUOTE DATA : {stock}")

            continue

        data = quote_result[0]

        current_price = data.get(
            "regularMarketPrice",
            0
        )

        previous_close = data.get(
            "regularMarketPreviousClose",
            0
        )

        open_price = data.get(
            "regularMarketOpen",
            0
        )

        day_high = data.get(
            "regularMarketDayHigh",
            0
        )

        day_low = data.get(
            "regularMarketDayLow",
            0
        )

        volume = data.get(
            "regularMarketVolume",
            0
        )

        market_cap = data.get(
            "marketCap",
            0
        )

        change_percent = data.get(
            "regularMarketChangePercent",
            0
        )

        avg_volume = data.get(
            "averageDailyVolume3Month",
            0
        )

        pe_ratio = data.get(
            "trailingPE",
            0
        )

        eps = data.get(
            "epsTrailingTwelveMonths",
            0
        )

        institutional_score = 50

        # =================================================
        # INSTITUTIONAL LOGIC
        # =================================================

        if market_cap > 1_000_000_000:

            institutional_score += 15

        if volume > 500000:

            institutional_score += 15

        if change_percent > 2:

            institutional_score += 10

        if pe_ratio > 0 and pe_ratio < 35:

            institutional_score += 5

        if eps > 0:

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
        # TRADE SIGNALS
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

            "Current Price": current_price,

            "Previous Close": previous_close,

            "Open": open_price,

            "Day High": day_high,

            "Day Low": day_low,

            "Volume": volume,

            "Average Volume": avg_volume,

            "Market Cap": market_cap,

            "PE Ratio": pe_ratio,

            "EPS": eps,

            "Change Percent": change_percent,

            "Institutional Score": institutional_score,

            "Confidence": confidence,

            "Buy Probability": buy_probability,

            "Composite Score": composite_score,

            "Trade Signal": trade_signal

        })

        print(f"SUCCESS : {stock}")
        time.sleep(0.35)

    except Exception as e:

        print(f"FAILED : {stock}")

        print(str(e))

        continue

# =========================================================
# CREATE FINAL DATAFRAME
# =========================================================

try:

    final_df = pd.DataFrame(results)

except Exception as e:

    print(f"FINAL DF FAILED : {e}")

    final_df = pd.DataFrame()

# =========================================================
# FINAL DATA SAFETY
# =========================================================

if final_df is None:

    final_df = pd.DataFrame()

if not isinstance(final_df, pd.DataFrame):

    final_df = pd.DataFrame()

# =========================================================
# ENSURE REQUIRED COLUMNS
# =========================================================

required_columns = [

    "Stock",
    "Trade Signal",
    "Institutional Score",
    "Confidence",
    "Current Price"

]

for column in required_columns:

    if column not in final_df.columns:

        if column == "Trade Signal":

            final_df[column] = "WATCH"

        else:

            final_df[column] = 0

# =========================================================
# HANDLE EMPTY DATAFRAME
# =========================================================

if final_df.empty:

    print("=" * 60)
    print("NO VALID STOCK DATA GENERATED")
    print("=" * 60)

    final_df = pd.DataFrame({

        "Stock": [],
        "Trade Signal": [],
        "Institutional Score": [],
        "Confidence": [],
        "Current Price": []

    })

# =========================================================
# REMOVE DUPLICATES
# =========================================================

if "Stock" in final_df.columns:

    final_df = (

        final_df

        .drop_duplicates(
            subset=["Stock"]
        )

        .reset_index(drop=True)

    )

# =========================================================
# FILL MISSING VALUES
# =========================================================

final_df = final_df.fillna(0)

# =========================================================
# SAFE SORTING
# =========================================================

preferred_columns = [

    "Composite Score",
    "Institutional Score",
    "Confidence",
    "Buy Probability"

]

sort_column = None

for column in preferred_columns:

    if column in final_df.columns:

        sort_column = column
        break

try:

    if (

        sort_column is not None
        and not final_df.empty

    ):

        final_df = final_df.sort_values(

            by=sort_column,

            ascending=False

        )

except Exception as e:

    print(f"SORT FAILED : {e}")

# =========================================================
# RESET INDEX
# =========================================================

final_df = final_df.reset_index(drop=True)

# =========================================================
# TOP PICKS
# =========================================================

try:

    if not final_df.empty:

        top_picks_df = final_df.head(100)

    else:

        top_picks_df = pd.DataFrame(
            columns=final_df.columns
        )

except Exception as e:

    print(f"TOP PICKS FAILED : {e}")

    top_picks_df = pd.DataFrame()

# =========================================================
# PORTFOLIO
# =========================================================

portfolio_df = top_picks_df.copy()

# =========================================================
# EXPORT CSV FILES
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

        if dataframe is None:

            dataframe = pd.DataFrame()

        if not isinstance(
            dataframe,
            pd.DataFrame
        ):

            dataframe = pd.DataFrame()

        export_path = (
            OUTPUT_DIR / filename
        )

        dataframe.to_csv(

            export_path,

            index=False

        )

        print(f"EXPORTED : {filename}")

    except Exception as e:

        print(
            f"EXPORT FAILED : "
            f"{filename} | {e}"
        )

# =========================================================
# SAFE DUCKDB SAVE
# =========================================================

try:

    if (

        not final_df.empty

        and len(final_df.columns) > 0

    ):

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

    else:

        print(
            "DUCKDB SKIPPED : EMPTY DATAFRAME"
        )

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

    print(f"PARQUET FAILED : {e}")

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

print("=" * 60)

print("PIPELINE COMPLETED")
print("=" * 60)
