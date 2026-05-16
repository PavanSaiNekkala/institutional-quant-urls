import yfinance as yf
import pandas as pd

def get_market_regime():

    try:
        nifty = yf.download("^NSEI", period="6mo", progress=False)
        banknifty = yf.download("^NSEBANK", period="6mo", progress=False)

        nifty["SMA50"] = nifty["Close"].rolling(50).mean()
        nifty["SMA200"] = nifty["Close"].rolling(200).mean()

        latest_close = nifty["Close"].iloc[-1]
        sma50 = nifty["SMA50"].iloc[-1]

        if latest_close > sma50:
            regime = "BULLISH"
            color = "#006400"

        elif latest_close < sma50 * 0.95:
            regime = "BEARISH"
            color = "#FF4B4B"

        else:
            regime = "NEUTRAL"
            color = "#1E90FF"

        return regime, color

    except:
        return "UNKNOWN", "#808080"
