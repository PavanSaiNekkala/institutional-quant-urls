import yfinance as yf
import numpy as np

def extract_cashflow(symbol):

    ticker = yf.Ticker(symbol)

    cashflow = ticker.cashflow

    data = {

        "Operating Cashflow": np.nan,
        "Free Cashflow": np.nan,
        "Capex": np.nan

    }

    try:
        data["Operating Cashflow"] = cashflow.loc["Operating Cash Flow"].iloc[0]
    except:
        pass

    try:
        data["Free Cashflow"] = cashflow.loc["Free Cash Flow"].iloc[0]
    except:
        pass

    try:
        data["Capex"] = cashflow.loc["Capital Expenditure"].iloc[0]
    except:
        pass

    return data
