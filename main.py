import pandas as pd
import time

from utils.symbol_validator import validate_symbol

from core.market_extractor import extract_market_data
from core.financial_extractor import extract_financials
from core.balance_extractor import extract_balance_sheet
from core.cashflow_extractor import extract_cashflow

from technicals.indicator_engine import calculate_indicators

from utils.failure_handler import categorize_failure

# ====================================================
# LOAD INPUT
# ====================================================

df = pd.read_excel(
    "input/yfinance_stock_urls.xlsx"
)

results = []

failed = []

# ====================================================
# MAIN LOOP
# ====================================================

for idx, row in df.iterrows():

    stock = str(row["Stock"]).strip()

    print(f"Processing {stock}")

    validation = validate_symbol(stock)

    if validation["valid"] is False:

        failed.append({
            "Stock": stock,
            "Reason": "INVALID_SYMBOL"
        })

        continue

    symbol = validation["symbol"]

    try:

        # ==========================================
        # EXTRACTORS
        # ==========================================

        market_data = extract_market_data(symbol)

        financial_data = extract_financials(symbol)

        balance_data = extract_balance_sheet(symbol)

        cashflow_data = extract_cashflow(symbol)

        technical_data = calculate_indicators(symbol)

        # ==========================================
        # MERGE ALL
        # ==========================================

        final_record = {

            "Stock": stock,

            "Validated Symbol": symbol,

            **market_data,

            **financial_data,

            **balance_data,

            **cashflow_data,

            **technical_data
        }

        results.append(final_record)

        time.sleep(1)

    except Exception as e:

        failed.append({

            "Stock": stock,

            "Reason": categorize_failure(e)
        })

# ====================================================
# EXPORT
# ====================================================

results_df = pd.DataFrame(results)

failed_df = pd.DataFrame(failed)

with pd.ExcelWriter(
    "output/enriched_stock_data.xlsx",
    engine="openpyxl"
) as writer:

    results_df.to_excel(
        writer,
        sheet_name="Enriched Data",
        index=False
    )

    failed_df.to_excel(
        writer,
        sheet_name="Failed Symbols",
        index=False
    )

print("Completed Successfully")
