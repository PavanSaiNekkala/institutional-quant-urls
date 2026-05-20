# =========================================================
# INSTITUTIONAL QUANT PLATFORM
# ELITE PRODUCTION-GRADE MAIN.PY
# =========================================================

import sys
import gc
import time
import logging
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
# LOGGER
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

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

            logger.error(
                f"INPUT FILE NOT FOUND : {INPUT_XLSX}"
            )

            return pd.DataFrame()

        df = pd.read_excel(INPUT_XLSX)

        if df.empty:

            logger.error("INPUT XLSX EMPTY")

            return pd.DataFrame()

        df.columns = [
            c.strip()
            for c in df.columns
        ]

        if "Stock" not in df.columns:

            logger.error("STOCK COLUMN MISSING")

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

        logger.info(
            f"TOTAL STOCKS LOADED : {len(df)}"
        )

        return df

    except Exception as e:

        logger.error(f"LOAD FAILED : {e}")

        return pd.DataFrame()

# =========================================================
# LOAD INPUT
# =========================================================

stock_input_df = load_stock_input()

if stock_input_df.empty:

    logger.error("NO STOCK INPUT")

    sys.exit(0)

# =========================================================
# MARKET REGIME
# =========================================================

def detect_market_regime(
    current_price,
    sma_20,
    sma_50,
    rsi,
    macd
):

    bullish = (
        current_price > sma_20 and
        sma_20 > sma_50 and
        macd > 0 and
        rsi > 55
    )

    bearish = (
        current_price < sma_20 and
        sma_20 < sma_50 and
        macd < 0 and
        rsi < 45
    )

    if bullish:
        return "BULLISH"

    elif bearish:
        return "BEARISH"

    else:
        return "SIDEWAYS"

# =========================================================
# TRADE SIGNAL
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

        logger.info(f"PROCESSING : {stock}")

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
        # VALIDATION
        # =================================================

        if hist is None or hist.empty:

            logger.error(f"FAILED : {stock}")

            return None

        required_cols = [
            "Close",
            "High",
            "Low"
        ]

        if not all(
            col in hist.columns
            for col in required_cols
        ):

            logger.error(f"FAILED : {stock}")

            return None

        hist = hist.dropna(subset=["Close"])

        if len(hist) < 50:

            logger.error(f"FAILED : {stock}")

            return None

        close_prices = hist["Close"]

        current_price = float(
            close_prices.iloc[-1]
        )

        if (
            pd.isna(current_price)
            or current_price <= 0
        ):

            logger.error(f"FAILED : {stock}")

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
            (close_prices.iloc[-1] /
             close_prices.iloc[-22]) - 1
            if len(close_prices) > 22
            else 0
        )

        returns_3m = (
            (close_prices.iloc[-1] /
             close_prices.iloc[-66]) - 1
            if len(close_prices) > 66
            else 0
        )

        returns_6m = (
            (close_prices.iloc[-1] /
             close_prices.iloc[0]) - 1
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
        # INSTITUTIONAL SCORING
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

        # =================================================
        # VOLATILITY ENGINE
        # =================================================

        volatility_ratio = atr / current_price

        if volatility_ratio > 0.08:
            institutional_score -= 10

        elif volatility_ratio < 0.03:
            institutional_score += 5

        # =================================================
        # TREND ENGINE
        # =================================================

        trend_strength = (
            (
                current_price - sma_50
            ) / sma_50
        ) * 100

        if trend_strength > 20:
            institutional_score += 10

        elif trend_strength > 10:
            institutional_score += 5

        elif trend_strength < -10:
            institutional_score -= 10

        institutional_score = max(
            0,
            min(institutional_score, 100)
        )

        # =================================================
        # MARKET REGIME
        # =================================================

        market_regime = detect_market_regime(
            current_price,
            sma_20,
            sma_50,
            rsi,
            macd
        )

        # =================================================
        # CONFIDENCE
        # =================================================

        confidence = institutional_score

        if market_regime == "BULLISH":
            confidence += 5

        elif market_regime == "BEARISH":
            confidence -= 10

        confidence = max(
            0,
            min(confidence, 100)
        )

        confidence = round(
            confidence,
            2
        )

        buy_probability = round(
            confidence * 0.95,
            2
        )

        trade_signal = classify_signal(
            confidence
        )

        if (
            market_regime == "BULLISH" and
            confidence >= 85 and
            returns_3m > 0.15
        ):
            trade_signal = "STRONG BUY"

        composite_score = round(
            (
                institutional_score +
                confidence +
                buy_probability
            ) / 3,
            2
        )

        buy_quality = round(
            (
                confidence +
                institutional_score +
                (100 - volatility_ratio * 100)
            ) / 3,
            2
        )

        logger.info(f"SUCCESS : {stock}")

        return {

            "Stock": stock,

            "Current Price":
            round(current_price, 2),

            "Previous Close":
            round(previous_close, 2),

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
            round(returns_1m * 100, 2),

            "3M Return":
            round(returns_3m * 100, 2),

            "6M Return":
            round(returns_6m * 100, 2),

            "RSI":
            round(rsi, 2),

            "SMA20":
            round(sma_20, 2),

            "SMA50":
            round(sma_50, 2),

            "MACD":
            round(macd, 2),

            "ATR":
            round(atr, 2),

            "Volatility Ratio":
            round(volatility_ratio, 4),

            "Trend Strength":
            round(trend_strength, 2),

            "Market Regime":
            market_regime,

            "Institutional Score":
            institutional_score,

            "Confidence":
            confidence,

            "Buy Probability":
            buy_probability,

            "Buy Quality":
            buy_quality,

            "Composite Score":
            composite_score,

            "Trade Signal":
            trade_signal
        }

    except Exception as e:

        logger.error(
            f"FAILED : {stock} | {str(e)}"
        )

        return None

# =========================================================
# PARALLEL ENGINE
# =========================================================

results = []

success_count = 0
failed_count = 0

MAX_WORKERS = 3

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

    logger.error(
        "NO VALID DATA GENERATED"
    )

    sys.exit(0)

final_df = (

    final_df

    .drop_duplicates(subset=["Stock"])

    .fillna(0)

    .infer_objects(copy=False)

    .reset_index(drop=True)

)

# =========================================================
# FILTERING
# =========================================================

final_df = final_df[
    final_df["Confidence"] >= 60
]

# =========================================================
# FINAL RANKING
# =========================================================

final_df["Final Rank Score"] = (

    final_df["Composite Score"] * 0.45 +

    final_df["Buy Quality"] * 0.35 +

    final_df["Confidence"] * 0.20

)

# =========================================================
# SORTING
# =========================================================

final_df = final_df.sort_values(
    by="Final Rank Score",
    ascending=False
)

# =========================================================
# TOP PICKS
# =========================================================

top_picks_df = final_df.head(100)

portfolio_df = top_picks_df.copy()

# =========================================================
# EXPORTS
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
            index=False,
            compression="gzip"
        )

    except Exception as e:

        logger.error(
            f"EXPORT FAILED : {filename}"
        )

        logger.error(str(e))

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

    logger.error(
        f"DB SAVE FAILED : {e}"
    )

# =========================================================
# PARQUET
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

    logger.error(
        f"PARQUET FAILED : {e}"
    )

# =========================================================
# EXCEL
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

    logger.error(
        f"EXCEL FAILED : {e}"
    )

# =========================================================
# MEMORY CLEANUP
# =========================================================

gc.collect()

# =========================================================
# FINAL SUMMARY
# =========================================================

logger.info("=" * 60)

logger.info(
    f"FINAL STOCK COUNT : {len(final_df)}"
)

logger.info(
    f"TOP PICKS COUNT : {len(top_picks_df)}"
)

logger.info(
    f"PORTFOLIO COUNT : {len(portfolio_df)}"
)

logger.info(
    f"SUCCESS COUNT : {success_count}"
)

logger.info(
    f"FAILED COUNT : {failed_count}"
)

logger.info(

    f"SUCCESS RATE : "

    f"{round((success_count / max(len(stock_input_df),1))*100,2)}%"

)

logger.info("=" * 60)

logger.info("PIPELINE COMPLETED")

logger.info("=" * 60)

conn.close()
