
# =========================================================
# IMPORTS
# =========================================================

import time
import random
import pandas as pd
import yfinance as yf
import multiprocessing

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from pathlib import Path

from utils.symbol_validator import validate_symbol
from utils.retry_engine import retry_request
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
# CPU + WORKER CONFIG
# =========================================================

CPU_COUNT = multiprocessing.cpu_count()

MAX_WORKERS = 3

# =========================================================
# BATCH CONFIG
# =========================================================

BATCH_SIZE = 25

BATCH_SLEEP = 12

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR
    / "input"
    / "yfinance_stock_urls.xlsx"
)

OUTPUT_DIR = (
    BASE_DIR
    / "output"
)

DATABASE_DIR = (
    BASE_DIR
    / "database"
)

LOG_DIR = (
    BASE_DIR
    / "logs"
)

# =========================================================
# CREATE DIRECTORIES
# =========================================================

OUTPUT_DIR.mkdir(
    exist_ok=True
)

DATABASE_DIR.mkdir(
    exist_ok=True
)

LOG_DIR.mkdir(
    exist_ok=True
)

# =========================================================
# START
# =========================================================

print("=" * 60)
print("LOADING DATASET...")
print("=" * 60)

# =========================================================
# LOAD INPUT
# =========================================================

df = pd.read_excel(
    INPUT_FILE
)

# =========================================================
# CLEAN STOCK SYMBOLS
# =========================================================

df["Stock"] = (

    df["Stock"]

    .astype(str)

    .str.strip()

    .str.upper()
)

# =========================================================
# REMOVE DUPLICATES
# =========================================================

df = df.drop_duplicates(
    subset=["Stock"]
)

# =========================================================
# REMOVE EMPTY VALUES
# =========================================================

df = df[
    df["Stock"].notna()
]

df = df[
    df["Stock"] != ""
]

# =========================================================
# RESET INDEX
# =========================================================

df = df.reset_index(
    drop=True
)

print(
    f"Unique Stocks Loaded : "
    f"{df['Stock'].nunique()}"
)

print(
    f"CPU Count : "
    f"{CPU_COUNT}"
)

print(
    f"Max Workers : "
    f"{MAX_WORKERS}"
)

# =========================================================
# DATABASE CONNECTION
# =========================================================

conn = get_connection()

print("DuckDB Connected")

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

            partial_df[
                "Stock"
            ].astype(str)
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

    except:

        pass

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

        print(
            f"Processing : {stock}"
        )

        # =================================================
        # HUMAN-LIKE DELAY
        # =================================================

        time.sleep(

            random.uniform(

                1.5,

                4.0
            )
        )

        # =================================================
        # VALIDATE SYMBOL
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
        # YFINANCE TICKER
        # =================================================

        ticker = retry_request(
            lambda: yf.Ticker(symbol)
        )

        # =================================================
        # DATA EXTRACTION
        # =================================================

        market_data = extract_market_data(
            ticker
        )

        financial_data = extract_financials(
            ticker
        )

        balance_data = extract_balance_sheet(
            ticker
        )

        cashflow_data = extract_cashflow(
            ticker
        )

        technical_data = calculate_indicators(
            ticker
        )

        sector_data = get_sector_data(
            stock
        )

        # =================================================
        # COMBINED DATA
        # =================================================

        combined_data = {

            **market_data,

            **financial_data,

            **balance_data,

            **cashflow_data,

            **technical_data
        }

        # =================================================
        # AI SCORES
        # =================================================

        ai_scores = calculate_institutional_score(
            combined_data
        )

        # =================================================
        # QUANT SCORES
        # =================================================

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
# PROCESSING START
# =========================================================

print("=" * 60)
print("STARTING PROCESSING...")
print("=" * 60)

batches = list(

    chunk_dataframe(
        df,
        BATCH_SIZE
    )
)

total_batches = len(batches)

print(
    f"Total Batches : "
    f"{total_batches}"
)

# =========================================================
# BATCH LOOP
# =========================================================

for batch_num, batch_df in enumerate(
    batches,
    start=1
):

    print("=" * 60)

    print(
        f"PROCESSING BATCH "
        f"{batch_num}/{total_batches}"
    )

    print("=" * 60)

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = [

            executor.submit(
                process_stock,
                row
            )

            for _, row in batch_df.iterrows()
        ]

        for future in as_completed(futures):

            try:

                result = future.result()

                if result["status"] == "SUCCESS":

                    results.append(
                        result["data"]
                    )

                    success_count += 1

                    # =========================================================
                    # SAVE PARTIAL PROGRESS
                    # =========================================================

                    if success_count % 50 == 0:

                        partial_df = pd.DataFrame(
                            results
                        )

                        partial_df.to_csv(

                            PARTIAL_RESULTS_FILE,

                            index=False
                        )

                        failed_partial_df = pd.DataFrame(
                            failed
                        )

                        failed_partial_df.to_csv(

                            PARTIAL_FAILED_FILE,

                            index=False
                        )

                        print(
                            f"Checkpoint Saved : "
                            f"{success_count}"
                        )

                    print(
                        f"SUCCESS : "
                        f"{success_count}"
                    )

                elif result["status"] == "FAILED":

                    failed.append(
                        result["data"]
                    )

                    failure_count += 1

                    print(
                        f"FAILED : "
                        f"{failure_count}"
                    )

            except Exception as e:

                failed.append({

                    "Stock": "UNKNOWN",

                    "Reason": "THREAD_ERROR",

                    "Error": str(e)
                })

    print(
        f"Sleeping {BATCH_SLEEP} sec..."
    )

    time.sleep(
        BATCH_SLEEP
    )

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
# REMOVE DUPLICATES
# =========================================================

final_df = (

    results_df

    .drop_duplicates(
        subset=["Stock"]
    )

    .reset_index(drop=True)
)

print(
    f"Final Unique Stocks : "
    f"{final_df['Stock'].nunique()}"
)

# =========================================================
# ML MODEL
# =========================================================

print("=" * 60)
print("TRAINING ML MODEL...")
print("=" * 60)

# =========================================================
# SAFE ML TRAINING
# =========================================================

if final_df.empty:

    print(
        "No valid stocks processed."
    )

    ml_model = None

    ml_accuracy = 0

else:

    ml_model, ml_accuracy = train_ml_model(
        final_df
    )

print(
    f"ML Accuracy : "
    f"{ml_accuracy}%"
)

if ml_model is not None:

    final_df = generate_predictions(

        ml_model,

        final_df
    )

# =========================================================
# BUILD PORTFOLIO
# =========================================================

portfolio_df = build_portfolio(
    final_df
)

# =========================================================
# RUN BACKTEST
# =========================================================

print("=" * 60)
print("RUNNING BACKTEST...")
print("=" * 60)

backtest_results = run_backtest(
    portfolio_df
)

# =========================================================
# SAVE DATABASE
# =========================================================

print("=" * 60)
print("SAVING TO DUCKDB...")
print("=" * 60)

conn.execute(
    """
    DROP TABLE IF EXISTS
    enriched_stocks
    """
)

conn.execute(
    """
    DROP TABLE IF EXISTS
    institutional_portfolio
    """
)

conn.register(
    "final_df",
    final_df
)

conn.execute(
    """
    CREATE TABLE
    enriched_stocks AS

    SELECT *
    FROM final_df
    """
)

conn.register(
    "portfolio_df",
    portfolio_df
)

conn.execute(
    """
    CREATE TABLE
    institutional_portfolio AS

    SELECT *
    FROM portfolio_df
    """
)

# =========================================================
# EXPORT FILES
# =========================================================

print("=" * 60)
print("EXPORTING CSV + XLSX FILES...")
print("=" * 60)

OUTPUT_DIR.mkdir(
    exist_ok=True
)

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
            f"CSV Exported : {filename}"
        )

    except Exception as e:

        print(
            f"CSV Export Failed : "
            f"{filename} | {e}"
        )

xlsx_exports = {

    "enriched_stock_data.xlsx":
    final_df,

    "institutional_portfolio.xlsx":
    portfolio_df,

    "failed_symbols.xlsx":
    failed_df,

    "top_institutional_picks.xlsx":
    top_picks_df
}

for filename, dataframe in xlsx_exports.items():

    try:

        dataframe.to_excel(

            OUTPUT_DIR / filename,

            index=False
        )

        print(
            f"XLSX Exported : {filename}"
        )

    except Exception as e:

        print(
            f"XLSX Export Failed : "
            f"{filename} | {e}"
        )

print("=" * 60)
print("ALL CSV + XLSX EXPORTS COMPLETED")
print("=" * 60)

# =========================================================
# CLOSE DATABASE
# =========================================================

conn.close()

# =========================================================
# FINAL SUMMARY
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
