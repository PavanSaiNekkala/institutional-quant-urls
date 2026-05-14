# =========================================================
# MARKET EXTRACTOR
# MULTI-SOURCE INSTITUTIONAL MARKET ENGINE
# =========================================================

import time
import random
import requests
import yfinance as yf

from core.multi_source_market_engine import (
    fetch_market_data
)

from utils.retry_engine import (
    retry_request
)

# =========================================================
# SHARED SESSION
# =========================================================

session = requests.Session()

# =========================================================
# EXTRACT MARKET DATA
# =========================================================

def extract_market_data(ticker):

    try:

        # =================================================
        # VALIDATE TICKER
        # =================================================

        if ticker is None:

            return {}

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

        symbol = str(
            symbol
        ).strip().upper()

        # =================================================
        # ENSURE NSE FORMAT
        # =================================================

        if not symbol.endswith(".NS"):

            symbol = f"{symbol}.NS"

        # =================================================
        # HUMAN-LIKE DELAY
        # =================================================

        time.sleep(

            random.uniform(

                1.0,

                3.0
            )
        )

        # =================================================
        # REFRESH TICKER USING SHARED SESSION
        # =================================================

        refreshed_ticker = yf.Ticker(

            symbol,

            session=session
        )

        # =================================================
        # RETRY MULTI-SOURCE FETCH
        # =================================================

        market_data = retry_request(

            lambda: fetch_market_data(
                symbol
            ),

            retries=5,

            base_delay=3
        )

        # =================================================
        # EMPTY SAFETY
        # =================================================

        if market_data is None:

            return {}

        if not isinstance(
            market_data,
            dict
        ):

            return {}

        # =================================================
        # BASIC FALLBACKS
        # =================================================

        fallback_price = None

        try:

            fast_info = refreshed_ticker.fast_info

            fallback_price = fast_info.get(

                "lastPrice",

                None
            )

        except:

            fallback_price = None

        # =================================================
        # SAFE DEFAULT VALUES
        # =================================================

        safe_market_data = {

            "Current Price":

            market_data.get(

                "Current Price",

                fallback_price
                if fallback_price is not None
                else 0
            ),

            "Market Cap":

            market_data.get(

                "Market Cap",

                0
            ),

            "Volume":

            market_data.get(

                "Volume",

                0
            ),

            "52 Week High":

            market_data.get(

                "52 Week High",

                0
            ),

            "52 Week Low":

            market_data.get(

                "52 Week Low",

                0
            ),

            "PE Ratio":

            market_data.get(

                "PE Ratio",

                0
            ),

            "PB Ratio":

            market_data.get(

                "PB Ratio",

                0
            ),

            "Dividend Yield":

            market_data.get(

                "Dividend Yield",

                0
            ),

            "ROE":

            market_data.get(

                "ROE",

                0
            ),

            "ROCE":

            market_data.get(

                "ROCE",

                0
            )
        }

        # =================================================
        # CLEAN NUMERIC VALUES
        # =================================================

        for key, value in safe_market_data.items():

            try:

                if value is None:

                    safe_market_data[key] = 0

                elif isinstance(
                    value,
                    str
                ):

                    safe_market_data[key] = float(
                        str(value)
                        .replace(",", "")
                    )

            except:

                safe_market_data[key] = 0

        # =================================================
        # RETURN CLEAN DATA
        # =================================================

        return safe_market_data

    except Exception as e:

        print(
            f"Market Extractor Failed | "
            f"{str(e)}"
        )

        return {}
