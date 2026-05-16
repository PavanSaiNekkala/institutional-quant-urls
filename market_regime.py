# =========================================================
# LIVE MARKET REGIME ENGINE
# =========================================================

import yfinance as yf
import pandas as pd


def get_market_regime():

    try:

        # =========================================
        # DOWNLOAD NIFTY DATA
        # =========================================

        nifty = yf.download(
            "^NSEI",
            period="1y",
            interval="1d",
            progress=False
        )

        # =========================================
        # EMPTY SAFETY
        # =========================================

        if nifty.empty:

            return (
                "UNKNOWN",
                "#808080",
                {
                    "NIFTY": "N/A",
                    "SMA50": "N/A",
                    "SMA200": "N/A",
                    "RSI": "N/A"
                }
            )

        # =========================================
        # CLOSE PRICE
        # =========================================

        close = nifty["Close"]

        # =========================================
        # MOVING AVERAGES
        # =========================================

        sma50 = close.rolling(50).mean().iloc[-1]

        sma200 = close.rolling(200).mean().iloc[-1]

        latest = float(close.iloc[-1])

        # =========================================
        # RSI
        # =========================================

        delta = close.diff()

        gain = delta.clip(lower=0)

        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(14).mean()

        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        latest_rsi = float(rsi.iloc[-1])

        # =========================================
        # REGIME LOGIC
        # =========================================

        if latest > sma50 > sma200 and latest_rsi > 55:

            regime = "BULL MARKET"
            color = "#006400"

        elif latest > sma200:

            regime = "SIDEWAYS MARKET"
            color = "#FF8C00"

        else:

            regime = "BEAR MARKET"
            color = "#8B0000"

        # =========================================
        # RETURN
        # =========================================

        return (

            regime,

            color,

            {
                "NIFTY": round(latest, 2),
                "SMA50": round(float(sma50), 2),
                "SMA200": round(float(sma200), 2),
                "RSI": round(latest_rsi, 2)
            }

        )

    except Exception as e:

        print(f"Market regime failed: {e}")

        return (

            "UNKNOWN",

            "#808080",

            {
                "NIFTY": "N/A",
                "SMA50": "N/A",
                "SMA200": "N/A",
                "RSI": "N/A"
            }

        )
