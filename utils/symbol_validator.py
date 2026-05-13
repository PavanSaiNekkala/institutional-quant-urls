# =========================================================
# SYMBOL VALIDATOR
# =========================================================

import yfinance as yf

# =========================================================
# INVALID KEYWORDS
# =========================================================

INVALID_KEYWORDS = [

    "ETF",

    "LIQUID",

    "GOLD",

    "SILVER",

    "BEES",

    "FUND",

    "INDEX"
]

# =========================================================
# VALIDATE SYMBOL
# =========================================================

def validate_symbol(symbol):

    try:

        if symbol is None:

            return {

                "valid": False,

                "symbol": symbol
            }

        symbol = str(symbol).strip().upper()

        # =============================================
        # REMOVE EMPTY
        # =============================================

        if symbol == "":

            return {

                "valid": False,

                "symbol": symbol
            }

        # =============================================
        # REMOVE ETF / MF
        # =============================================

        for keyword in INVALID_KEYWORDS:

            if keyword in symbol:

                return {

                    "valid": False,

                    "symbol": symbol
                }

        # =============================================
        # ENSURE .NS
        # =============================================

        if not symbol.endswith(".NS"):

            symbol = f"{symbol}.NS"

        # =============================================
        # QUICK VALIDATION
        # =============================================

        ticker = yf.Ticker(symbol)

        info = ticker.fast_info

        last_price = info.get(

            "lastPrice",

            None
        )

        if last_price is None:

            return {

                "valid": False,

                "symbol": symbol
            }

        return {

            "valid": True,

            "symbol": symbol
        }

    except Exception:

        return {

            "valid": False,

            "symbol": symbol
        }
