# =========================================================
# ULTRA FAST INSTITUTIONAL PIPELINE (STABLE BUILD)
# =========================================================

import os
import sys
import time
import random
import warnings
import multiprocessing

import pandas as pd
import yfinance as yf

from pathlib import Path

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
    TimeoutError
)

warnings.filterwarnings("ignore")

# =========================================================
# INTERNAL IMPORTS
# =========================================================

from utils.symbol_validator import validate_symbol
from utils.db_manager import get_connection
from utils.sector_mapper import get_sector_data
from utils.failure_handler import categorize_failure

from core.market_extractor import extract_market_data
from core.financial_extractor import extract_financials
from core.balance_extractor import extract_balance_sheet
from core.cashflow_extractor import extract_cashflow

from technicals.indicator_engine import (
    calculate_indicators
)

from ai.scoring_engine import (
    calculate_institutional_score
)

from analytics.quant_factor_engine import (
    calculate_quant_scores
)

from analytics.portfolio_engine import (
    build_portfolio
)

from ml.ml_prediction_engine import (
    train_ml_model,
    generate_predictions
)

from backtesting.backtest_engine import (
    run_backtest
)

# =========================================================
# CONFIG
# =========================================================

CPU_COUNT = multiprocessing.cpu_count()

MAX_WORKERS = 16

BATCH_SIZE = 50

BATCH_SLEEP = 2

CHECKPOINT_INTERVAL = 250

THREAD_TIMEOUT = 30

ENABLE_XLSX = False

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR
    / "input"
    / "yfinance_stock_urls.xlsx"
)

OUTPUT_DIR = BASE_DIR / "output"

DATABASE_DIR = BASE_DIR / "database"

LOG_DIR = BASE_DIR / "logs"

FAILED_DIR = BASE_DIR / "failed"

CACHE_DIR = BASE_DIR / "cache"

# =========================================================
# CREATE DIRECTORIES
# =========================================================

for directory in [

    OUTPUT_DIR,
    DATABASE_DIR,
    LOG_DIR,
    FAILED_DIR,
    CACHE_DIR

]:

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

# =========================================================
# YFINANCE CACHE
# =========================================================

yf.set_tz_cache_location(
    str(CACHE_DIR)
)

# =========================================================
# LOAD DATASET
# =========================================================

print("=" * 60)
print("LOADING DATASET...")
print("=" * 60)

sys.stdout.flush()

df = pd.read_excel(INPUT_FILE)

# =========================================================
# CLEAN SYMBOLS
# =========================================================

df["Stock"] = (

    df["Stock"]

    .astype(str)

    .str.strip()

    .str.upper()
)

df = df.drop_duplicates(
    subset=["Stock"]
)

df = df[
    df["Stock"].notna()
]

df = df[
    df["Stock"] != ""
]

df = df.reset_index(
    drop=True
)

print(
    f"Unique Stocks Loaded : "
    f"{df['Stock'].nunique()}"
)

print(
    f"CPU Count : {CPU_COUNT}"
)

print(
    f"Max Workers : {MAX_WORKERS}"
)

sys.stdout.flush()

# =========================================================
# DATABASE
# =========================================================

conn = get_connection()

print("DuckDB Connected")

sys.stdout.flush()

# =========================================================
# STORAGE
# =========================================================

results = []

failed = []

# =========================================================
# PROCESS STOCK
# =========================================================

def process_stock(row):

    stock = "UNKNOWN"

    try:

        stock = str(
            row["Stock"]
        ).strip()

        validation = validate_symbol(
            stock
        )

        if validation["valid"] is False:

            return None

        symbol = validation["symbol"]

        # =================================================
        # SAFE YFINANCE DOWNLOAD
        # =================================================

        try:

            hist = yf.download(

                symbol,

                period="6mo",

                interval="1d",

                progress=False,

                auto_adjust=True,

                threads=False
            )

        except Exception:

            return None

        if hist.empty:

            return None

        # =================================================
        # EXTRACTORS
        # =================================================

        market_data = extract_market_data(
            symbol,
            hist
        )

        financial_data = extract_financials(
            symbol
        )

        balance_data = extract_balance_sheet(
            symbol
        )

        cashflow_data = extract_cashflow(
            symbol
        )

        technical_data = calculate_indicators(
            hist
        )

        sector_data = get_sector_data(
            stock
        )

        combined_data = {

            **market_data,
            **financial_data,
            **balance_data,
            **cashflow_data,
            **technical_data
        }

        if not combined_data:

            return None

        ai_scores = calculate_institutional_score(
            combined_data
        )

        quant_scores = calculate_quant_scores(
            combined_data
        )

        final_record = {

            "Stock": stock,

            "Validated Symbol": symbol,

            **market_data,

            **financial_data,

            **balance_data,

            **cashflow_data,

            **technical_data,

            **sector_data,

            **ai_scores,

            **quant_scores
        }

        return final_record

    except Exception:

        return None

# =========================================================
# START TIMER
# =========================================================

start_time = time.time()

# =========================================================
# PROCESSING
# =========================================================

print("=" * 60)
print("STARTING PROCESSING...")
print("=" * 60)

sys.stdout.flush()

rows = df.to_dict(
    orient="records"
)

with ThreadPoolExecutor(
    max_workers=MAX_WORKERS
) as executor:

    futures = [

        executor.submit(
            process_stock,
            row
        )

        for row in rows
    ]

    for idx, future in enumerate(

        as_completed(futures),

        start=1
    ):

        try:

            result = future.result(
                timeout=THREAD_TIMEOUT
            )

            if result is not None:

                results.append(result)

            if idx % 50 == 0:

                print(
                    f"Processed : {idx}"
                )

                sys.stdout.flush()

        except Exception:

            pass

# =========================================================
# DATAFRAMES
# =========================================================

results_df = pd.DataFrame(
    results
)

# =========================================================
# EMPTY CHECK
# =========================================================

if results_df.empty:

    print("NO RESULTS FOUND")

    results_df = pd.DataFrame({

        "Stock": [],
        "Trade Signal": [],
        "Institutional Score": [],
        "Confidence": [],
        "Current Price": []

    })

# =========================================================
# FINAL DF
# =========================================================

final_df = (

    results_df

    .drop_duplicates(
        subset=["Stock"]
    )

    .reset_index(drop=True)
)

final_df = final_df.fillna(0)

# =========================================================
# ML MODEL
# =========================================================

if len(final_df) >= 100:

    try:

        ml_model, ml_accuracy = train_ml_model(
            final_df
        )

        if ml_model is not None:

            final_df = generate_predictions(

                ml_model,

                final_df
            )

    except Exception as e:

        print(
            f"ML Failed : {e}"
        )

# =========================================================
# PORTFOLIO
# =========================================================

portfolio_df = pd.DataFrame()

try:

    if not final_df.empty:

        portfolio_df = build_portfolio(
            final_df
        )

except Exception as e:

    print(
        f"Portfolio Failed : {e}"
    )

portfolio_df = portfolio_df.fillna(0)

# =========================================================
# BACKTEST
# =========================================================

try:

    if not portfolio_df.empty:

        run_backtest(
            portfolio_df
        )

except Exception as e:

    print(
        f"Backtest Failed : {e}"
    )

# =========================================================
# SAFE SORT
# =========================================================

sort_column = None

preferred_columns = [

    "Composite Score",

    "Institutional Score",

    "Confidence",

    "Buy Probability"

]

for column in preferred_columns:

    if column in final_df.columns:

        sort_column = column

        break

if sort_column is not None:

    final_df = final_df.sort_values(

        by=sort_column,

        ascending=False
    )

# =========================================================
# TOP PICKS
# =========================================================

top_picks_df = final_df.head(100)

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

        dataframe.to_csv(

            OUTPUT_DIR / filename,

            index=False
        )

        print(
            f"Exported : {filename}"
        )

    except Exception as e:

        print(
            f"Export Failed : {filename} | {e}"
        )

# =========================================================
# SAFE DUCKDB SAVE
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

    print(
        f"DuckDB Save Failed : {e}"
    )

# =========================================================
# CLOSE DB
# =========================================================

conn.close()

# =========================================================
# SUMMARY
# =========================================================

elapsed = round(
    time.time() - start_time,
    2
)

print("=" * 60)

print("PROCESS COMPLETED")

print(
    f"Successful Stocks : "
    f"{len(final_df)}"
)

print(
    f"Execution Time : "
    f"{elapsed} sec"
)

print("=" * 60)

sys.stdout.flush()
