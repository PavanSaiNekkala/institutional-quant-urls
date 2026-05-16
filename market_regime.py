import pandas as pd
import numpy as np
import yfinance as yf

# =========================================================
# RSI CALCULATION
# =========================================================

def calculate_rsi(series, period=14):

        delta = series.diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        return rsi

# =========================================================
# LIVE MARKET REGIME
# =========================================================

def get_market_regime():

        try:

                # =========================================
                # DOWNLOAD NIFTY DATA
                # =========================================

                nifty = yf.download(

                        "^NSEI",

                        period="1y",

                        interval="1d",

                        auto_adjust=True,

                        progress=False,

                        threads=False

                )

                if nifty.empty:

                        return (
                                "UNKNOWN",
                                "#808080",
                                {}
                        )

                # =========================================
                # INDICATORS
                # =========================================

                nifty["SMA50"] = (
                        nifty["Close"]
                        .rolling(50)
                        .mean()
                )

                nifty["SMA200"] = (
                        nifty["Close"]
                        .rolling(200)
                        .mean()
                )

                nifty["RSI"] = calculate_rsi(
                        nifty["Close"]
                )

                # =========================================
                # LATEST VALUES
                # =========================================

                latest_close = float(
                        nifty["Close"].iloc[-1]
                )

                sma50 = float(
                        nifty["SMA50"].iloc[-1]
                )

                sma200 = float(
                        nifty["SMA200"].iloc[-1]
                )

                rsi = float(
                        nifty["RSI"].iloc[-1]
                )

                # =========================================
                # MARKET REGIME LOGIC
                # =========================================

                # STRONG BULL
                if (
                        latest_close > sma200
                        and latest_close > sma50
                        and rsi >= 60
                ):

                        regime = "STRONG BULL"
                        color = "#006400"

                # BULLISH
                elif (
                        latest_close > sma50
                ):

                        regime = "BULLISH"
                        color = "#00AA00"

                # SIDEWAYS
                elif (
                        latest_close > sma200
                ):

                        regime = "SIDEWAYS"
                        color = "#FF8C00"

                # BEARISH
                else:

                        regime = "BEARISH"
                        color = "#FF0000"

                # =========================================
                # DETAILS
                # =========================================

                details = {
                        "NIFTY": round(float(latest_close), 2),
                        "SMA50": round(float(sma50), 2),
                        "SMA200": round(float(sma200), 2),
                        "RSI": round(float(rsi_value), 2)
                }

                return regime, color, details

        except Exception as e:

                print(
                        f"Market regime failed: {e}"
                )

                return (
                        "UNKNOWN",
                        "#808080",
                        {}
                )
