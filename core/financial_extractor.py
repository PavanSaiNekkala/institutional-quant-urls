import yfinance as yf
import numpy as np

def extract_financials(symbol):

    ticker = yf.Ticker(symbol)

    financials = ticker.financials

    data = {

        "Revenue": np.nan,
        "Net Income": np.nan,
        "EBITDA": np.nan

    }

    try:
        data["Revenue"] = financials.loc["Total Revenue"].iloc[0]
    except:
        pass

    try:
        data["Net Income"] = financials.loc["Net Income"].iloc[0]
    except:
        pass

    try:
        data["EBITDA"] = financials.loc["EBITDA"].iloc[0]
    except:
        pass

    return data
