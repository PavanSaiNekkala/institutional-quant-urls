# =========================================================
# IMPORTS
# =========================================================

import pandas as pd
import yfinance as yf
# =========================================================
# IMPORTS
# =========================================================

import pandas as pd
import yfinance as yf

# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(value):

    try:

        return float(value)

    except:

        return 0

# =========================================================
# SAFE INT
# =========================================================

def safe_int(value):

    try:

        return int(value)

    except:

        return 0

# =========================================================
# FETCH LIVE MARKET DATA
# =========================================================

def fetch_live_market_data(symbols):

    results = []

    for symbol in symbols:

        try:

            ticker = yf.Ticker(symbol)

            hist = ticker.history(
                period="1d"
            )

            if hist.empty:

                continue

            current_close = safe_float(
                hist["Close"].iloc[-1]
            )

            current_volume = safe_int(
                hist["Volume"].iloc[-1]
            )

            results.append({

                "Stock": symbol,

                "Current Price": round(
                    current_close,
                    2
                ),

                "Volume": current_volume
            })

        except:

            pass

    return pd.DataFrame(results)
# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(value):

    try:

        return float(value)

    except:

        return 0

# =========================================================
# SAFE INT
# =========================================================

def safe_int(value):

    try:

        return int(value)

    except:

        return 0

# =========================================================
# FETCH LIVE MARKET DATA
# =========================================================

def fetch_live_market_data(symbols):

    results = []

    for symbol in symbols:

        try:

            ticker = yf.Ticker(symbol)

            hist = ticker.history(
                period="2d"
            )

            # =============================================
            # EMPTY CHECK
            # =============================================

            if hist.empty:

                continue

            # =============================================
            # CURRENT + PREVIOUS
            # =============================================

            current_close = safe_float(
                hist["Close"].iloc[-1]
            )

            if len(hist) > 1:

                previous_close = safe_float(
                    hist["Close"].iloc[-2]
                )

            else:

                previous_close = current_close

            current_volume = safe_int(
                hist["Volume"].iloc[-1]
            )

            # =============================================
            # % CHANGE
            # =============================================

            if previous_close > 0:

                percent_change = (

                    (
                        current_close
                        - previous_close
                    )

                    / previous_close

                ) * 100

            else:

                percent_change = 0

            # =============================================
            # MARKET CAP
            # =============================================

            try:

                info = ticker.fast_info

                market_cap = safe_float(
                    info.get(
                        "market_cap",
                        0
                    )
                )

            except:

                market_cap = 0

            # =============================================
            # FINAL RECORD
            # =============================================

            results.append({

                "Stock": symbol,

                "Current Price": round(
                    current_close,
                    2
                ),

                "Previous Close": round(
                    previous_close,
                    2
                ),

                "% Change": round(
                    percent_change,
                    2
                ),

                "Volume": current_volume,

                "Market Cap": market_cap
            })

        except Exception as e:

            print(
                f"Live Market Failure : "
                f"{symbol} | {e}"
            )

    return pd.DataFrame(results)

# =========================================================
# TOP GAINERS
# =========================================================

def get_top_gainers(
    live_df,
    top_n=10
):

    if live_df.empty:

        return pd.DataFrame()

    return live_df.sort_values(

        by="% Change",

        ascending=False

    ).head(top_n)

# =========================================================
# TOP LOSERS
# =========================================================

def get_top_losers(
    live_df,
    top_n=10
):

    if live_df.empty:

        return pd.DataFrame()

    return live_df.sort_values(

        by="% Change",

        ascending=True

    ).head(top_n)

# =========================================================
# VOLUME SHOCKS
# =========================================================

def get_volume_shocks(
    live_df,
    top_n=10
):

    if live_df.empty:

        return pd.DataFrame()

    return live_df.sort_values(

        by="Volume",

        ascending=False

    ).head(top_n)

# =========================================================
# MARKET BREADTH
# =========================================================

def calculate_market_breadth(
    live_df
):

    if live_df.empty:

        return {

            "Advancing": 0,

            "Declining": 0,

            "Unchanged": 0,

            "Breadth Ratio": 0
        }

    advancing = len(

        live_df[
            live_df["% Change"] > 0
        ]
    )

    declining = len(

        live_df[
            live_df["% Change"] < 0
        ]
    )

    unchanged = len(

        live_df[
            live_df["% Change"] == 0
        ]
    )

    if declining == 0:

        breadth_ratio = advancing

    else:

        breadth_ratio = round(

            advancing / declining,

            2
        )

    return {

        "Advancing": advancing,

        "Declining": declining,

        "Unchanged": unchanged,

        "Breadth Ratio": breadth_ratio
    }
