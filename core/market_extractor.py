# =========================================================
# MARKET EXTRACTOR
# =========================================================

import time
import random
import yfinance as yf

from core.multi_source_market_engine import (
    fetch_market_data
)

from utils.retry_engine import (
    retry_request
)

# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(value):

    try:

        if value is None:
            return 0.0

        return float(
            str(value)
            .replace(",", "")
            .strip()
        )

    except:

        return 0.0


# =========================================================
# EXTRACT MARKET DATA
# =========================================================

def extract_market_data(ticker):

    try:

        # =================================================
        # SYMBOL
        # =================================================

        symbol = getattr(
            ticker,
            "ticker",
            None
        )

        if symbol is None:

            return {}

        symbol = str(symbol).strip().upper()

        # =================================================
        # NSE FORMAT
        # =================================================

        if not symbol.endswith(".NS"):

            symbol = f"{symbol}.NS"

        # =================================================
        # SMALL HUMAN DELAY
        # =================================================

        time.sleep(
            random.uniform(0.5, 1.5)
        )

        # =================================================
        # FETCH MARKET DATA
        # =================================================

        market_data = retry_request(

            lambda: fetch_market_data(
                symbol
            ),

            retries=3,

            base_delay=2
        )

        # =================================================
        # EMPTY SAFETY
        # =================================================

        if market_data is None:

            market_data = {}

        if not isinstance(
            market_data,
            dict
        ):

            market_data = {}

        # =================================================
        # YFINANCE FALLBACK
        # =================================================

        fallback_price = 0
        fallback_volume = 0
        fallback_market_cap = 0
        fallback_day_high = 0
        fallback_day_low = 0
        fallback_prev_close = 0

        try:

            # =============================================
            # IMPORTANT FIX:
            # DO NOT PASS SESSION=
            # =============================================

            yf_ticker = yf.Ticker(symbol)

            fast_info = yf_ticker.fast_info

            fallback_price = safe_float(
                fast_info.get(
                    "lastPrice",
                    fast_info.get(
                        "last_price",
                        0
                    )
                )
            )

            fallback_volume = safe_float(
                fast_info.get(
                    "lastVolume",
                    fast_info.get(
                        "last_volume",
                        0
                    )
                )
            )

            fallback_market_cap = safe_float(
                fast_info.get(
                    "marketCap",
                    fast_info.get(
                        "market_cap",
                        0
                    )
                )
            )

            fallback_day_high = safe_float(
                fast_info.get(
                    "dayHigh",
                    fast_info.get(
                        "day_high",
                        0
                    )
                )
            )

            fallback_day_low = safe_float(
                fast_info.get(
                    "dayLow",
                    fast_info.get(
                        "day_low",
                        0
                    )
                )
            )

            fallback_prev_close = safe_float(
                fast_info.get(
                    "previousClose",
                    fast_info.get(
                        "previous_close",
                        0
                    )
                )
            )

        except Exception as yf_error:

            print(
                f"YFinance Fallback Failed | "
                f"{symbol} | "
                f"{yf_error}"
            )

        # =================================================
        # SAFE MARKET DATA
        # =================================================

        safe_market_data = {

            "Current Price":

            safe_float(

                market_data.get(
                    "Current Price",
                    fallback_price
                )
            ),

            "Market Cap":

            safe_float(

                market_data.get(
                    "Market Cap",
                    fallback_market_cap
                )
            ),

            "Volume":

            safe_float(

                market_data.get(
                    "Volume",
                    fallback_volume
                )
            ),

            "Day High":

            safe_float(

                market_data.get(
                    "Day High",
                    fallback_day_high
                )
            ),

            "Day Low":

            safe_float(

                market_data.get(
                    "Day Low",
                    fallback_day_low
                )
            ),

            "Previous Close":

            safe_float(

                market_data.get(
                    "Previous Close",
                    fallback_prev_close
                )
            ),

            "52 Week High":

            safe_float(

                market_data.get(
                    "52 Week High",
                    0
                )
            ),

            "52 Week Low":

            safe_float(

                market_data.get(
                    "52 Week Low",
                    0
                )
            ),

            "PE Ratio":

            safe_float(

                market_data.get(
                    "PE Ratio",
                    0
                )
            ),

            "PB Ratio":

            safe_float(

                market_data.get(
                    "PB Ratio",
                    0
                )
            ),

            "Dividend Yield":

            safe_float(

                market_data.get(
                    "Dividend Yield",
                    0
                )
            ),

            "ROE":

            safe_float(

                market_data.get(
                    "ROE",
                    0
                )
            ),

            "ROCE":

            safe_float(

                market_data.get(
                    "ROCE",
                    0
                )
            )
        }

        return safe_market_data

    except Exception as e:

        print(
            f"Market Extractor Failed | "
            f"{str(e)}"
        )

        return {}
