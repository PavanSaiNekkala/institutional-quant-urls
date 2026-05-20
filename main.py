# =========================================================
# INSTITUTIONAL QUANT PLATFORM
# FINAL PRODUCTION-GRADE MAIN.PY
# =========================================================

import sys
import time
import traceback
import warnings
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import duckdb
import numpy as np
import pandas as pd
import yfinance as yf

from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, MACD
from ta.volatility import AverageTrueRange

warnings.filterwarnings("ignore")

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
# LOAD STOCK INPUT
# =========================================================

def load_stock_input():

    try:

        if not INPUT_XLSX.exists():

            print(f"INPUT FILE NOT FOUND : {INPUT_XLSX}")

            return pd.DataFrame()

        df = pd.read_excel(INPUT_XLSX)

        if df.empty:

            print("INPUT XLSX EMPTY")

            return pd.DataFrame()

        df.columns = [
            c.strip()
            for c in df.columns
        ]

        if "Stock" not in df.columns:

            print("STOCK COLUMN MISSING")

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

            .drop_duplicates(subset=["Stock"])

            .reset_index(drop=True)

        )

        print(f"TOTAL STOCKS LOADED : {len(df)}")

        return df

    except Exception as e:

        print(f"LOAD FAILED : {e}")

        return pd.DataFrame()

# =========================================================
# LOAD INPUT
# =========================================================

stock_input_df = load_stock_input()

if stock_input_df.empty:

    print("NO STOCK INPUT")

    sys.exit(0)

# =========================================================
# TRADE SIGNAL CLASSIFIER
# =========================================================

def classify_signal(confidence):

    if confidence >= 90:

        return "STRONG BUY"

    elif confidence >= 75:

        return "BUY"

    elif confidence >= 60:

        return "WATCH"

    elif confidence >= 45:

        return "HOLD"

    else:

        return "AVOID"

# =========================================================
# PROCESS STOCK
# =========================================================

def process_stock(row):

    stock = row["Stock"]

    try:

        time.sleep(1.2)

        ticker = yf.Ticker(stock)

        hist = pd.DataFrame()

        # =================================================
        # RETRY ENGINE
        # =================================================

        for _ in range(3):

            try:

                hist = ticker.history(
                    period="6mo",
                    interval="1d",
                    auto_adjust=True,
                    repair=True,
                    timeout=30
                )

                if hist is not None and not hist.empty:

                    break

            except Exception:

                time.sleep(2)

        # =================================================
        # EMPTY CHECK
        # =================================================

        if hist is None or hist.empty:

            return None

        required_cols = [
            "Close",
            "High",
            "Low"
        ]

        if not all(col in hist.columns for col in required_cols):

            return None

        hist = hist.dropna(subset=["Close"])

        if len(hist) < 50:

            return None

        close_prices = hist["Close"]

        current_price = float(
            close_prices.iloc[-1]
        )

        if pd.isna(current_price):

            return None

        previous_close = (

            float(close_prices.iloc[-2])

            if len(close_prices) > 1

            else current_price

        )

        # =================================================
        # TECHNICALS
        # =================================================

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

        # =================================================
        # NULL SAFETY
        # =================================================

        if pd.isna(rsi):
                rsi = 50

        if pd.isna(sma_20):
                sma_20 = current_price

        if pd.isna(sma_50):
                sma_50 = current_price

        if pd.isna(macd):
                macd = 0

        if pd.isna(atr):
                atr = current_price * 0.02

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
        # FAST INFO
        # =================================================

        try:

            info = ticker.fast_info

        except Exception:

            info = {}

        volume = info.get(
            "lastVolume",
            0
        ) or 0

        market_cap = info.get(
            "marketCap",
            0
        ) or 0

        day_high = info.get(
            "dayHigh",
            current_price
        )

        day_low = info.get(
            "dayLow",
            current_price
        )

        year_high = info.get(
            "yearHigh",
            current_price
        )

        year_low = info.get(
            "yearLow",
            current_price
        )

        # =================================================
        # SCORING ENGINE
        # =================================================

        institutional_score = 0

        if market_cap > 500_000_000_000:

            institutional_score += 25

        elif market_cap > 100_000_000_000:

            institutional_score += 18

        elif market_cap > 10_000_000_000:

            institutional_score += 10

        if volume > 5_000_000:

            institutional_score += 20

        elif volume > 1_000_000:

            institutional_score += 15

        elif volume > 250_000:

            institutional_score += 8

        if returns_1m > 0.05:

            institutional_score += 10

        if returns_3m > 0.10:

            institutional_score += 10

        if returns_6m > 0.20:

            institutional_score += 10

        if 45 <= rsi <= 70:

            institutional_score += 10

        elif rsi > 80:

            institutional_score -= 5

        if current_price > sma_20:

            institutional_score += 5

        if current_price > sma_50:

            institutional_score += 5

        if macd > 0:

            institutional_score += 5

        if atr < current_price * 0.04:

            institutional_score += 5

        institutional_score = max(
            0,
            min(institutional_score, 100)
        )

        # =================================================
        # CONFIDENCE
        # =================================================

        confidence = round(
            institutional_score * 0.95,
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
                + confidence
                + buy_probability
            ) / 3,

            2

        )

        # =================================================
        # RESULT
        # =================================================

        return {

            "Stock": stock,

            "Current Price": round(current_price, 2),

            "Previous Close": round(previous_close, 2),

            "Volume": volume,

            "Market Cap": market_cap,

            "Day High": day_high,

            "Day Low": day_low,

            "52W High": year_high,

            "52W Low": year_low,

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

            "RSI": round(rsi, 2),

            "SMA20": round(sma_20, 2),

            "SMA50": round(sma_50, 2),

            "MACD": round(macd, 2),

            "ATR": round(atr, 2),

            "Institutional Score": institutional_score,

            "Confidence": confidence,

            "Buy Probability": buy_probability,

            "Composite Score": composite_score,

            "Trade Signal": trade_signal

        }

    except Exception:

        return None

# =========================================================
# PARALLEL ENGINE
# =========================================================

results = []

success_count = 0
failed_count = 0

MAX_WORKERS = 2

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

        except Exception:

            failed_count += 1

# =========================================================
# FINAL DATAFRAME
# =========================================================

final_df = pd.DataFrame(results)

if final_df.empty:

    print("NO VALID DATA GENERATED")

    sys.exit(0)

final_df = (

    final_df

    .drop_duplicates(subset=["Stock"])

    .fillna(0)

    .reset_index(drop=True)

)

# =========================================================
# SORTING
# =========================================================

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

for filename, dataframe in csv_exports.items():

    try:

        export_path = OUTPUT_DIR / filename

        dataframe.to_csv(
            export_path,
            index=False
        )

    except Exception as e:

        print(f"EXPORT FAILED : {filename}")
        print(str(e))

# =========================================================
# SAVE DATABASE
# =========================================================

try:

    conn.execute(
        """
        DROP TABLE IF EXISTS enriched_stocks
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

except Exception as e:

    print(f"DB SAVE FAILED : {e}")

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

except Exception as e:

    print(f"PARQUET FAILED : {e}")

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

except Exception as e:

    print(f"EXCEL FAILED : {e}")

# =========================================================
# FINAL SUMMARY
# =========================================================

print("=" * 60)

print(f"FINAL STOCK COUNT : {len(final_df)}")

print(f"TOP PICKS COUNT : {len(top_picks_df)}")

print(f"PORTFOLIO COUNT : {len(portfolio_df)}")

print(f"SUCCESS COUNT : {success_count}")

print(f"FAILED COUNT : {failed_count}")

print(

    f"SUCCESS RATE : "

    f"{round((success_count / max(len(stock_input_df),1))*100,2)}%"

)

print("=" * 60)

print("PIPELINE COMPLETED")

print("=" * 60)

conn.close()
