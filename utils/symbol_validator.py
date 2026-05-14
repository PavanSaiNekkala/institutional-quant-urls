# =========================================================
# SYMBOL VALIDATOR
# =========================================================

BLACKLIST = [

    "ETF",

    "BEES",

    "LIQUID",

    "GOLD",

    "SILVER",

    "FUND",

    "INDEX",

    "NIFTY",

    "SENSEX",

    "BANKBEES",

    "JUNIORBEES"
]

# =========================================================
# VALIDATE SYMBOL
# =========================================================

def validate_symbol(stock):

    try:

        if stock is None:

            return {

                "valid": False,

                "symbol": None
            }

        stock = str(
            stock
        ).strip().upper()

        # =================================================
        # EMPTY CHECK
        # =================================================

        if stock == "":

            return {

                "valid": False,

                "symbol": stock
            }

        # =================================================
        # BLACKLIST CHECK
        # =================================================

        for word in BLACKLIST:

            if word in stock:

                return {

                    "valid": False,

                    "symbol": stock
                }

        # =================================================
        # NSE FORMAT
        # =================================================

        if not stock.endswith(".NS"):

            stock = f"{stock}.NS"

        # =================================================
        # LENGTH SAFETY
        # =================================================

        if len(stock) < 3:

            return {

                "valid": False,

                "symbol": stock
            }

        # =================================================
        # RETURN VALID
        # =================================================

        return {

            "valid": True,

            "symbol": stock
        }

    except:

        return {

            "valid": False,

            "symbol": None
        }
