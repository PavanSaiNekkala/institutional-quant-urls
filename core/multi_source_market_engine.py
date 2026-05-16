# =========================================================
# IMPORTS
# =========================================================

import time
import traceback
import requests
import yfinance as yf

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.api_keys import (

    ALPHA_VANTAGE_API_KEY,

    FINNHUB_API_KEY,

    TWELVEDATA_API_KEY
)

# =========================================================
# GLOBAL REQUEST SESSION
# =========================================================

retry_strategy = Retry(

    total=3,

    backoff_factor=1,

    status_forcelist=[
        429,
        500,
        502,
        503,
        504
    ]
)

adapter = HTTPAdapter(

    max_retries=retry_strategy
)

http = requests.Session()

http.mount(
    "https://",
    adapter
)

http.mount(
    "http://",
    adapter
)

# =========================================================
# REQUEST HEADERS
# =========================================================

HEADERS = {

    "User-Agent":

    (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

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
            .replace("%", "")
            .strip()
        )

    except:

        return 0.0


# =========================================================
# SAFE INT
# =========================================================

def safe_int(value):

    try:

        if value is None:

            return 0

        return int(float(

            str(value)
            .replace(",", "")
            .strip()
        ))

    except:

        return 0


# =========================================================
# YAHOO FINANCE
# IMPORTANT:
# NEVER PASS session=
# =========================================================

def fetch_yfinance(symbol):

    try:

        time.sleep(0.25)

        # =================================================
        # DO NOT USE requests.Session()
        # =================================================

        ticker = yf.Ticker(symbol)

        fast_info = ticker.fast_info

        current_price = safe_float(

            fast_info.get(
                "lastPrice",

                fast_info.get(
                    "last_price",
                    0
                )
            )
        )

        if current_price <= 0:

            return None

        market_data = {

            "Source": "Yahoo",

            "Current Price":
            current_price,

            "Market Cap":

            safe_float(

                fast_info.get(
                    "marketCap",

                    fast_info.get(
                        "market_cap",
                        0
                    )
                )
            ),

            "Volume":

            safe_int(

                fast_info.get(
                    "lastVolume",

                    fast_info.get(
                        "last_volume",
                        0
                    )
                )
            ),

            "Previous Close":

            safe_float(

                fast_info.get(
                    "previousClose",

                    fast_info.get(
                        "previous_close",
                        0
                    )
                )
            ),

            "Day High":

            safe_float(

                fast_info.get(
                    "dayHigh",

                    fast_info.get(
                        "day_high",
                        0
                    )
                )
            ),

            "Day Low":

            safe_float(

                fast_info.get(
                    "dayLow",

                    fast_info.get(
                        "day_low",
                        0
                    )
                )
            ),

            "Currency":

            fast_info.get(
                "currency",
                "INR"
            ),

            "Exchange":

            fast_info.get(
                "exchange",
                "NSE"
            )
        }

        return market_data

    except Exception as e:

        print(
            f"Yahoo Failure | "
            f"{symbol} | "
            f"{str(e)}"
        )

        return None


# =========================================================
# ALPHA VANTAGE
# =========================================================

def fetch_alpha_vantage(symbol):

    try:

        time.sleep(0.2)

        url = (

            "https://www.alphavantage.co/query"

            "?function=GLOBAL_QUOTE"

            f"&symbol={symbol}"

            f"&apikey={ALPHA_VANTAGE_API_KEY}"
        )

        response = http.get(

            url,

            headers=HEADERS,

            timeout=15
        )

        data = response.json()

        quote = data.get(
            "Global Quote",
            {}
        )

        current_price = safe_float(
            quote.get(
                "05. price",
                0
            )
        )

        if current_price <= 0:

            return None

        return {

            "Source": "AlphaVantage",

            "Current Price":
            current_price,

            "Previous Close":

            safe_float(
                quote.get(
                    "08. previous close",
                    0
                )
            ),

            "Volume":

            safe_int(
                quote.get(
                    "06. volume",
                    0
                )
            )
        }

    except Exception as e:

        print(
            f"AlphaVantage Failure | "
            f"{symbol} | "
            f"{str(e)}"
        )

        return None


# =========================================================
# FINNHUB
# =========================================================

def fetch_finnhub(symbol):

    try:

        time.sleep(0.2)

        url = (

            "https://finnhub.io/api/v1/quote"

            f"?symbol={symbol}"

            f"&token={FINNHUB_API_KEY}"
        )

        response = http.get(

            url,

            headers=HEADERS,

            timeout=15
        )

        data = response.json()

        current_price = safe_float(
            data.get("c", 0)
        )

        if current_price <= 0:

            return None

        return {

            "Source": "Finnhub",

            "Current Price":
            current_price,

            "Previous Close":
            safe_float(
                data.get("pc", 0)
            ),

            "Day High":
            safe_float(
                data.get("h", 0)
            ),

            "Day Low":
            safe_float(
                data.get("l", 0)
            )
        }

    except Exception as e:

        print(
            f"Finnhub Failure | "
            f"{symbol} | "
            f"{str(e)}"
        )

        return None


# =========================================================
# TWELVE DATA
# =========================================================

def fetch_twelvedata(symbol):

    try:

        time.sleep(0.2)

        url = (

            "https://api.twelvedata.com/price"

            f"?symbol={symbol}"

            f"&apikey={TWELVEDATA_API_KEY}"
        )

        response = http.get(

            url,

            headers=HEADERS,

            timeout=15
        )

        data = response.json()

        current_price = safe_float(
            data.get(
                "price",
                0
            )
        )

        if current_price <= 0:

            return None

        return {

            "Source": "TwelveData",

            "Current Price":
            current_price
        }

    except Exception as e:

        print(
            f"TwelveData Failure | "
            f"{symbol} | "
            f"{str(e)}"
        )

        return None


# =========================================================
# MASTER FETCHER
# =========================================================

def fetch_market_data(symbol):

    try:

        yahoo_data = fetch_yfinance(symbol)

        if yahoo_data is not None:

            return yahoo_data

        finnhub_data = fetch_finnhub(symbol)

        if finnhub_data is not None:

            return finnhub_data

        alpha_data = fetch_alpha_vantage(symbol)

        if alpha_data is not None:

            return alpha_data

        twelvedata_data = fetch_twelvedata(symbol)

        if twelvedata_data is not None:

            return twelvedata_data

        return {

            "Source": "Unavailable",

            "Market Cap": 0,

            "Current Price": 0,

            "Previous Close": 0,

            "Day High": 0,

            "Day Low": 0,

            "Volume": 0
        }

    except Exception as e:

        print(
            f"Market Data Failure | "
            f"{symbol} | "
            f"{str(e)}"
        )

        traceback.print_exc()

        return {}
