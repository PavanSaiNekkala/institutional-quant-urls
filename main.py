# =========================================================
# ULTRA FAST INSTITUTIONAL PIPELINE
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

MAX_WORKERS = min(32, CPU_COUNT * 4)

BATCH_SIZE = 100

BATCH_SLEEP = 0

CHECKPOINT_INTERVAL = 500

THREAD_TIMEOUT = 45

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
# CHECKPOINT FILES
# =========================================================

PARTIAL_RESULTS_FILE = (
    OUTPUT_DIR
    / "partial_results.csv"
)

PARTIAL_FAILED_FILE = (
    OUTPUT_DIR
    / "partial_failed.csv"
)

# =========================================================
# AUTO RESUME
# =========================================================

if PARTIAL_RESULTS_FILE.exists():

    try:

        partial_df = pd.read_csv(
            PARTIAL_RESULTS_FILE
        )

        results = partial_df.to_dict(
            orient="records"
        )

        processed_stocks = set(

            partial_df["Stock"]
            .astype(str)
        )

        df = df[

            ~df["Stock"].isin(
                processed_stocks
            )
        ]

        print(
            f"Resuming from "
            f"{len(results)} stocks"
        )

        sys.stdout.flush()

    except Exception as e:

        print(
            f"Resume Failed : {e}"
        )

        sys.stdout.flush()

success_count = len(results)

failure_count = 0

# =========================================================
# CHUNK GENERATOR
# =========================================================

def chunk_dataframe(
    dataframe,
    chunk_size
):

    for i in range(
        0,
        len(dataframe),
        chunk_size
    ):

        yield dataframe.iloc[
            i:i + chunk_size
        ]

# =========================================================
# PROCESS STOCK
# =========================================================

def process_stock(row):

    stock = "UNKNOWN"

    try:

        stock = str(
            row["Stock"]
        ).strip()

        # =================================================
        # LIGHT LOGGING
        # =================================================

        if random.randint(1, 100) == 1:

            print(
                f"Running : {stock}"
            )

            sys.stdout.flush()

        # =================================================
        # VALIDATE
        # =================================================

        validation = validate_symbol(
            stock
        )

        if validation["valid"] is False:

            return {

                "status": "FAILED",

                "data": {

                    "Stock": stock,

                    "Reason": "INVALID_SYMBOL"
                }
            }

        symbol = validation["symbol"]

        # =================================================
        # FAST DOWNLOAD
        # =================================================

        hist = yf.download(

            symbol,

            period="1y",

            interval="1d",

            progress=False,

            threads=False,

            auto_adjust=True
        )

        if hist.empty:

            raise ValueError(
                "NO_MARKET_DATA"
            )

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

        # =================================================
        # COMBINED
        # =================================================

        combined_data = {

            **market_data,

            **financial_data,

            **balance_data,

            **cashflow_data,

            **technical_data
        }

        if not combined_data:

            raise ValueError(
                "EMPTY_DATA"
            )

        # =================================================
        # AI
        # =================================================

        ai_scores = calculate_institutional_score(
            combined_data
        )

        quant_scores = calculate_quant_scores(
            combined_data
        )

        # =================================================
        # FINAL RECORD
        # =================================================

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

        return {

            "status": "SUCCESS",

            "data": final_record
        }

    except Exception as e:

        return {

            "status": "FAILED",

            "data": {

                "Stock": stock,

                "Reason": categorize_failure(e),

                "Error": str(e)
            }
        }

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

total_batches = (

    len(df) + BATCH_SIZE - 1

) // BATCH_SIZE

print(
    f"Total Batches : "
    f"{total_batches}"
)

sys.stdout.flush()

# =========================================================
# BATCH LOOP
# =========================================================

for batch_num, batch_df in enumerate(

    chunk_dataframe(
        df,
        BATCH_SIZE
    ),

    start=1
):

    print("=" * 60)

    print(
        f"BATCH "
        f"{batch_num}/{total_batches}"
    )

    print("=" * 60)

    sys.stdout.flush()

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        rows = batch_df.to_dict(
            orient="records"
        )

        futures = {

            executor.submit(
                process_stock,
                row
            ): row

            for row in rows
        }

        for future in as_completed(futures):

            try:

                result = future.result(
                    timeout=THREAD_TIMEOUT
                )

                if result["status"] == "SUCCESS":

                    results.append(
                        result["data"]
                    )

                    success_count += 1

                    if success_count % 25 == 0:

                        print(
                            f"SUCCESS : "
                            f"{success_count}"
                        )

                        sys.stdout.flush()

                    # =============================
                    # CHECKPOINT
                    # =============================

                    if (

                        success_count
                        %
                        CHECKPOINT_INTERVAL
                        ==
                        0
                    ):

                        pd.DataFrame(
                            results
                        ).to_csv(

                            PARTIAL_RESULTS_FILE,

                            index=False
                        )

                        pd.DataFrame(
                            failed
                        ).to_csv(

                            PARTIAL_FAILED_FILE,

                            index=False
                        )

                else:

                    failed.append(
                        result["data"]
                    )

                    failure_count += 1

            except TimeoutError:

                failure_count += 1

                failed.append({

                    "Stock": "UNKNOWN",

                    "Reason": "TIMEOUT"
                })

            except Exception as e:

                failure_count += 1

                failed.append({

                    "Stock": "UNKNOWN",

                    "Reason": "THREAD_ERROR",

                    "Error": str(e)
                })

# =========================================================
# DATAFRAMES
# =========================================================

results_df = pd.DataFrame(
    results
)

failed_df = pd.DataFrame(
    failed
)

# =========================================================
# SAVE CHECKPOINTS
# =========================================================

results_df.to_csv(

    PARTIAL_RESULTS_FILE,

    index=False
)

failed_df.to_csv(

    PARTIAL_FAILED_FILE,

    index=False
)

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

# =========================================================
# FILL NULLS
# =========================================================

final_df = final_df.fillna(0)

# =========================================================
# ML MODEL
# =========================================================

ml_model = None

ml_accuracy = 0

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

if not final_df.empty:

    try:

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
# SAVE DATABASE
# =========================================================

try:

    conn.execute(
        "DROP TABLE IF EXISTS enriched_stocks"
    )

    conn.execute(
        "DROP TABLE IF EXISTS institutional_portfolio"
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

    conn.register(
        "portfolio_df",
        portfolio_df
    )

    conn.execute(
        """
        CREATE TABLE institutional_portfolio AS
        SELECT * FROM portfolio_df
        """
    )

except Exception as e:

    print(
        f"DuckDB Save Failed : {e}"
    )

# =========================================================
# EXPORTS
# =========================================================

sort_column = None

for column in [

    "Composite Score",

    "Institutional Score",

    "Confidence",

    "Buy Probability"
]:

    if column in final_df.columns:

        sort_column = column

        break

if sort_column is None:

    sort_column = final_df.columns[0]

sorted_df = final_df.sort_values(

    by=sort_column,

    ascending=False
)

top_picks_df = sorted_df.head(100)

csv_exports = {

    "enriched_stock_data.csv":
    final_df,

    "institutional_portfolio.csv":
    portfolio_df,

    "failed_symbols.csv":
    failed_df,

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
# CLEAN CHECKPOINTS
# =========================================================

try:

    if PARTIAL_RESULTS_FILE.exists():

        PARTIAL_RESULTS_FILE.unlink()

    if PARTIAL_FAILED_FILE.exists():

        PARTIAL_FAILED_FILE.unlink()

except:
    pass

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
    f"Failed Stocks : "
    f"{len(failed_df)}"
)

print(
    f"Execution Time : "
    f"{elapsed} sec"
)

print("=" * 60)

sys.stdout.flush()
