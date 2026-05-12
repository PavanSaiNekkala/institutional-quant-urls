import yfinance as yf
import pandas as pd
import ta

def calculate_indicators(symbol):

    ticker = yf.Ticker(symbol)

    hist = ticker.history(period="1y")

    close = hist["Close"]

    data = {

        "RSI": None,
        "SMA50": None,
        "SMA200": None

    }

    try:

        data["RSI"] = ta.momentum.RSIIndicator(close).rsi().iloc[-1]

        data["SMA50"] = close.rolling(50).mean().iloc[-1]

        data["SMA200"] = close.rolling(200).mean().iloc[-1]

    except:
        pass

    return data
