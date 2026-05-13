# =========================================================
# IMPORTS
# =========================================================

import pandas as pd
import numpy as np
import yfinance as yf

# =========================================================
# SAFE NUMERIC
# =========================================================

def safe_numeric(series):

    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)

# =========================================================
# BULK LIVE MARKET FETCHER
# =========================================================

def bulk_fetch_market_data(symbols):

    try:

        # =================================================
        # CLEAN SYMBOLS
        # =================================================

        symbols = [

            str(symbol).strip()

            for symbol in symbols

            if pd.notna(symbol)
        ]

        symbols = list(set(symbols))

        # =================================================
        # LIMIT LIVE FETCHES
        # =================================================

        symbols = symbols[:200]

        # =================================================
        # BULK DOWNLOAD
        # =================================================

        data = yf.download(

            tickers=symbols,

            period="1mo",

            interval="1d",

            group_by="ticker",

            auto_adjust=True,

            progress=False,

            threads=False
        )

        live_data = {}

        # =================================================
        # PROCESS EACH SYMBOL
        # =================================================

        for symbol in symbols:

            try:

                if symbol not in data:

                    continue

                stock_data = data[symbol]

                if stock_data.empty:

                    continue

                # =========================================
                # CURRENT PRICE
                # =========================================

                current_price = float(

                    stock_data[
                        "Close"
                    ].iloc[-1]
                )

                # =========================================
                # RETURNS
                # =========================================

                ret_5d = 0
                ret_20d = 0

                if len(stock_data) >= 6:

                    ret_5d = (

                        (

                            stock_data[
                                "Close"
                            ].iloc[-1]

                            /

                            stock_data[
                                "Close"
                            ].iloc[-6]

                        ) - 1

                    ) * 100

                if len(stock_data) >= 21:

                    ret_20d = (

                        (

                            stock_data[
                                "Close"
                            ].iloc[-1]

                            /

                            stock_data[
                                "Close"
                            ].iloc[-21]

                        ) - 1

                    ) * 100

                # =========================================
                # VOLUME RATIO
                # =========================================

                avg_volume = (

                    stock_data[
                        "Volume"
                    ]

                    .tail(20)

                    .mean()
                )

                current_volume = (

                    stock_data[
                        "Volume"
                    ].iloc[-1]
                )

                volume_ratio = 1

                if avg_volume > 0:

                    volume_ratio = (

                        current_volume

                        /

                        avg_volume
                    )

                # =========================================
                # STORE
                # =========================================

                live_data[symbol] = {

                    "Current Price": round(
                        current_price,
                        2
                    ),

                    "5D Return": round(
                        ret_5d,
                        2
                    ),

                    "20D Return": round(
                        ret_20d,
                        2
                    ),

                    "Volume Ratio": round(
                        volume_ratio,
                        2
                    )
                }

            except:

                continue

        return live_data

    except Exception as e:

        print(
            f"Bulk market fetch error: {e}"
        )

        return {}

# =========================================================
# MARKET REGIME ENGINE
# =========================================================

def calculate_market_regime(df):

    avg_inst = df[
        "Institutional Score"
    ].mean()

    avg_alpha = df[
        "Alpha Score"
    ].mean()

    avg_rsi = df[
        "RSI"
    ].mean()

    avg_adx = df[
        "ADX"
    ].mean()

    avg_buy_prob = df[
        "Buy Probability"
    ].mean()

    regime_score = (

        avg_inst * 0.30

        +

        avg_alpha * 0.25

        +

        avg_buy_prob * 0.25

        +

        avg_rsi * 0.10

        +

        avg_adx * 0.10
    )

    if regime_score >= 80:

        return "🚀 Strong Bullish"

    elif regime_score >= 65:

        return "📈 Bullish"

    elif regime_score >= 50:

        return "⚖️ Neutral"

    elif regime_score >= 35:

        return "📉 Bearish"

    return "🩸 Strong Bearish"

# =========================================================
# BUILD TRADE DECISIONS
# =========================================================

def build_trade_decisions(df):

    df = df.copy()

    # =====================================================
    # SAFE NUMERIC
    # =====================================================

    numeric_columns = [

        "Institutional Score",

        "Alpha Score",

        "Buy Probability",

        "RSI",

        "ADX"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = safe_numeric(
                df[column]
            )

        else:

            df[column] = 0

    # =====================================================
    # SYMBOLS
    # =====================================================

    if "Stock" in df.columns:

        symbols = df[
            "Stock"
        ].dropna().tolist()

    else:

        symbols = []

    # =====================================================
    # BULK LIVE FETCH
    # =====================================================

    live_market_data = bulk_fetch_market_data(
        symbols
    )

    # =====================================================
    # STORE LIVE DATA
    # =====================================================

    current_prices = []
    ret_5d_list = []
    ret_20d_list = []
    volume_ratio_list = []

    for _, row in df.iterrows():

        symbol = row.get(
            "Stock",
            ""
        )

        market_data = live_market_data.get(
            symbol,
            {}
        )

        current_prices.append(

            market_data.get(
                "Current Price",
                0
            )
        )

        ret_5d_list.append(

            market_data.get(
                "5D Return",
                0
            )
        )

        ret_20d_list.append(

            market_data.get(
                "20D Return",
                0
            )
        )

        volume_ratio_list.append(

            market_data.get(
                "Volume Ratio",
                1
            )
        )

    # =====================================================
    # ASSIGN LIVE DATA
    # =====================================================

    df["Current Price"] = current_prices

    df["5D Return"] = ret_5d_list

    df["20D Return"] = ret_20d_list

    df["Volume Ratio"] = volume_ratio_list

    # =====================================================
    # MOMENTUM SCORE
    # =====================================================

    df["Momentum Score"] = (

        (

            df["5D Return"] * 0.40
        )

        +

        (

            df["20D Return"] * 0.60
        )
    )

    # =====================================================
    # VOLUME SCORE
    # =====================================================

    df["Volume Score"] = (

        df["Volume Ratio"]

        * 50

    ).clip(0, 100)

    # =====================================================
    # MARKET REGIME
    # =====================================================

    market_regime = calculate_market_regime(
        df
    )

    # =====================================================
    # REGIME WEIGHTS
    # =====================================================

    if "Bearish" in market_regime:

        institutional_weight = 0.45
        momentum_weight = 0.15
        volume_weight = 0.10
        alpha_weight = 0.20
        probability_weight = 0.10

    else:

        institutional_weight = 0.30
        momentum_weight = 0.25
        volume_weight = 0.15
        alpha_weight = 0.20
        probability_weight = 0.10

    # =====================================================
    # COMPOSITE SCORE
    # =====================================================

    df["Composite Score"] = (

        (

            df["Institutional Score"]

            * institutional_weight
        )

        +

        (

            df["Momentum Score"]

            * momentum_weight
        )

        +

        (

            df["Volume Score"]

            * volume_weight
        )

        +

        (

            df["Alpha Score"]

            * alpha_weight
        )

        +

        (

            df["Buy Probability"]

            * probability_weight
        )
    )

    # =====================================================
    # NORMALIZE SCORE
    # =====================================================

    df["Composite Score"] = (

        df["Composite Score"]

        .clip(0, 100)

        .round(2)
    )

    # =====================================================
    # PERCENTILE RANK
    # =====================================================

    df["Percentile Rank"] = (

        df["Composite Score"]

        .rank(pct=True)
    )

    # =====================================================
    # SIGNAL ENGINE
    # =====================================================

    def generate_signal(rank):

        if rank >= 0.95:

            return "Strong Buy"

        elif rank >= 0.80:

            return "Buy"

        elif rank >= 0.50:

            return "Watch"

        return "Avoid"

    df["Trade Signal"] = df[
        "Percentile Rank"
    ].apply(generate_signal)

    # =====================================================
    # TARGET PRICE
    # =====================================================

    df["Target Price"] = (

        df["Current Price"]

        * (

            1

            +

            (
                df["Composite Score"]

                / 100
            ) * 0.25
        )

    ).round(2)

    # =====================================================
    # STOPLOSS
    # =====================================================

    df["Stoploss"] = (

        df["Current Price"]

        * 0.93

    ).round(2)

    # =====================================================
    # CONFIDENCE
    # =====================================================

    df["Confidence"] = (

        df["Composite Score"]

        .clip(0, 100)

        .round(2)
    )

    # =====================================================
    # REMOVE INVALID PRICES
    # =====================================================

    df = df[
        df["Current Price"] > 0
    ]

    # =====================================================
    # SORTING
    # =====================================================

    df = df.sort_values(

        by="Composite Score",

        ascending=False
    )

    # =====================================================
    # FINAL COLUMNS
    # =====================================================

    final_columns = [

        "Stock",

        "Trade Signal",

        "Current Price",

        "Target Price",

        "Stoploss",

        "Confidence",

        "Institutional Score",

        "Alpha Score",

        "Buy Probability",

        "Momentum Score",

        "Volume Score",

        "5D Return",

        "20D Return",

        "Volume Ratio",

        "Composite Score"
    ]

    available_columns = [

        col

        for col in final_columns

        if col in df.columns
    ]

    df = df[
        available_columns
    ]

    return df
