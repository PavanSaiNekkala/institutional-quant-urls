import yfinance as yf

EXCHANGE_SUFFIXES = [
    ".NS",
    ".BO",
    ""
]

def validate_symbol(stock):

    stock = str(stock).replace(".NS", "").replace(".BO", "")

    for suffix in EXCHANGE_SUFFIXES:

        symbol = stock + suffix

        try:

            ticker = yf.Ticker(symbol)

            hist = ticker.history(period="5d")

            if not hist.empty:

                return {
                    "valid": True,
                    "symbol": symbol
                }

        except:
            continue

    return {
        "valid": False,
        "symbol": None
    }
