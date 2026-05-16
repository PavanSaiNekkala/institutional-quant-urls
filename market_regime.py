# =========================================================
# market_regime.py
# =========================================================

import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta

# =========================================================
# CACHE
# =========================================================

@st.cache_data(ttl=1800)
@st.cache_data(ttl=1800)
def fetch_nifty_data():

    symbols = [
        "^NSEI",
        "^BSESN",
        "RELIANCE.NS"
    ]

    for symbol in symbols:

        try:

            df = yf.download(
                symbol,
                period="1y",
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=False
            )

            if (
                df is not None
                and not df.empty
                and "Close" in df.columns
            ):

                close_series = df["Close"].dropna()

                if len(close_series) > 220:
                    return df

        except Exception as e:
            print(f"{symbol} failed: {e}")

    return pd.DataFrame()
# =========================================================
# MARKET REGIME
# =========================================================

def get_market_regime():

    try:

        df = fetch_nifty_data()

        # =================================================
        # FALLBACK IF DATA FAILS
        # =================================================

        if df.empty:

            return (
                "SIDEWAYS MARKET",
                "#808080",
                {
                    "NIFTY": "N/A",
                    "SMA50": "N/A",
                    "SMA200": "N/A",
                    "RSI": "N/A"
                }
            )

        # =================================================
        # PRICE
        # =================================================

        close = float(df["Close"].iloc[-1])

        # =================================================
        # MOVING AVERAGES
        # =================================================

        sma50 = float(df["Close"].rolling(50).mean().iloc[-1])

        sma200 = float(df["Close"].rolling(200).mean().iloc[-1])

        # =================================================
        # RSI
        # =================================================

        delta = df["Close"].diff()

        gain = delta.clip(lower=0)

        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(14).mean()

        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        rsi = float(rsi.iloc[-1])

        # =================================================
        # BULL MARKET
        # =================================================

        if close > sma50 > sma200 and rsi >= 60:

            regime = "BULL MARKET"

            color = "#008000"

        # =================================================
        # BEAR MARKET
        # =================================================

        elif close < sma50 < sma200 and rsi < 45:

            regime = "BEAR MARKET"

            color = "#CC0000"

        # =================================================
        # SIDEWAYS MARKET
        # =================================================

        else:

            regime = "SIDEWAYS MARKET"

            color = "#808080"

        # =================================================
        # RETURN
        # =================================================

        details = {

            "NIFTY": round(close, 2),
            "SMA50": round(sma50, 2),
            "SMA200": round(sma200, 2),
            "RSI": round(rsi, 2)

        }

        return regime, color, details

    except Exception as e:

        print(f"Market regime failed: {e}")

        return (
            "SIDEWAYS MARKET",
            "#808080",
            {
                "NIFTY": "N/A",
                "SMA50": "N/A",
                "SMA200": "N/A",
                "RSI": "N/A"
            }
        )
