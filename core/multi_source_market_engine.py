# =========================================================
# IMPORTS
# =========================================================

import time
import requests
import yfinance as yf

from config.api_keys import (

    ALPHA_VANTAGE_API_KEY,

    FINNHUB_API_KEY,

    TWELVEDATA_API_KEY
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

            return 0

        return float(value)

    except:

        return 0


# =========================================================
# SAFE INT
# =========================================================

def safe_int(value):

    try:

        if value is None:

            return 0

        return int(value)

    except:

        return 0


# =========================================================
# YAHOO FINANCE
# =========================================================

def fetch_yfinance(symbol):

    try:

        # =============================================
        # RATE LIMIT PROTECTION
        # =============================================

        time.sleep(0.25)

        # =============================================
        # YFINANCE
        # =============================================

        ticker = yf.Ticker(symbol)

        info = ticker.fast_info

        market_cap = safe_float(
            info.get("market_cap", 0)
        )

        current_price = safe_float(
            info.get("last_price", 0)
        )

        volume = safe_int(
            info.get("last_volume", 0)
        )

        previous_close = safe_float(
            info.get("previous_close", 0)
        )

        day_high = safe_float(
            info.get("day_high", 0)
        )

        day_low = safe_float(
            info.get("day_low", 0)
        )

        currency = info.get(
            "currency",
            "INR"
        )

        exchange = info.get(
            "exchange",
            "NSE"
        )

        # =============================================
        # VALIDITY CHECK
        # =============================================

        if current_price <= 0:

            return None

        return {

            "Source": "Yahoo",

            "Market Cap": market_cap,

            "Current Price": current_price,

            "Previous Close": previous_close,

            "Day High": day_high,

            "Day Low": day_low,

            "Volume": volume,

            "Currency": currency,

            "Exchange": exchange
        }

    except Exception as e:

        print(
            f"Yahoo Failure : "
            f"{symbol} | {e}"
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

        response = requests.get(

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

        volume = safe_int(
            quote.get(
                "06. volume",
                0
            )
        )

        previous_close = safe_float(
            quote.get(
                "08. previous close",
                0
            )
        )

        if current_price <= 0:

            return None

        return {

            "Source": "AlphaVantage",

            "Current Price": current_price,

            "Previous Close": previous_close,

            "Volume": volume
        }

    except Exception as e:

        print(
            f"AlphaVantage Failure : "
            f"{symbol} | {e}"
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

        response = requests.get(

            url,

            headers=HEADERS,

            timeout=15
        )

        data = response.json()

        current_price = safe_float(
            data.get("c", 0)
        )

        previous_close = safe_float(
            data.get("pc", 0)
        )

        day_high = safe_float(
            data.get("h", 0)
        )

        day_low = safe_float(
            data.get("l", 0)
        )

        if current_price <= 0:

            return None

        return {

            "Source": "Finnhub",

            "Current Price": current_price,

            "Previous Close": previous_close,

            "Day High": day_high,

            "Day Low": day_low
        }

    except Exception as e:

        print(
            f"Finnhub Failure : "
            f"{symbol} | {e}"
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

        response = requests.get(

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

            "Current Price": current_price
        }

    except Exception as e:

        print(
            f"TwelveData Failure : "
            f"{symbol} | {e}"
        )

        return None


# =========================================================
# NSE FALLBACK
# =========================================================

def fetch_nse(symbol):

    try:

        time.sleep(0.3)

        clean_symbol = symbol.replace(
            ".NS",
            ""
        )

        url = (

            "https://www.nseindia.com/api/"
            f"quote-equity?symbol={clean_symbol}"
        )

        response = requests.get(

            url,

            headers=HEADERS,

            timeout=15
        )

        data = response.json()

        price_info = data.get(
            "priceInfo",
            {}
        )

        current_price = safe_float(
            price_info.get(
                "lastPrice",
                0
            )
        )

        previous_close = safe_float(
            price_info.get(
                "previousClose",
                0
            )
        )

        intra = price_info.get(
            "intraDayHighLow",
            {}
        )

        day_high = safe_float(
            intra.get("max", 0)
        )

        day_low = safe_float(
            intra.get("min", 0)
        )

        if current_price <= 0:

            return None

        return {

            "Source": "NSE",

            "Current Price": current_price,

            "Previous Close": previous_close,

            "Day High": day_high,

            "Day Low": day_low
        }

    except Exception as e:

        print(
            f"NSE Failure : "
            f"{symbol} | {e}"
        )

        return None


# =========================================================
# MASTER FETCHER
# =========================================================

def fetch_market_data(symbol):

    # =====================================================
    # YAHOO FIRST
    # =====================================================

    yahoo_data = fetch_yfinance(symbol)

    if yahoo_data is not None:

        return yahoo_data

    # =====================================================
    # NSE SECOND
    # =====================================================

    nse_data = fetch_nse(symbol)

    if nse_data is not None:

        return nse_data

    # =====================================================
    # ALPHA VANTAGE
    # =====================================================

    alpha_data = fetch_alpha_vantage(symbol)

    if alpha_data is not None:

        return alpha_data

    # =====================================================
    # FINNHUB
    # =====================================================

    finnhub_data = fetch_finnhub(symbol)

    if finnhub_data is not None:

        return finnhub_data

    # =====================================================
    # TWELVE DATA
    # =====================================================

    twelvedata_data = fetch_twelvedata(symbol)

    if twelvedata_data is not None:

        return twelvedata_data

    # =====================================================
    # FINAL FAILURE
    # =====================================================

    return {

        "Source": "Unavailable",

        "Market Cap": 0,

        "Current Price": 0,

        "Previous Close": 0,

        "Day High": 0,

        "Day Low": 0,

        "Volume": 0
    }
