import pandas as pd


def get_trigger(df: pd.DataFrame) -> dict:
    if len(df) < 2:
        return {
            "trigger": "NO_TRIGGER",
            "score": 0,
            "reasons": ["Not enough trigger data"],
        }

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    bullish_score = 0
    bearish_score = 0

    bullish_reasons = []
    bearish_reasons = []

    # 1) Stochastic cross / alignment
    bullish_stoch = (
        latest["stoch_k"] > latest["stoch_d"]
        and previous["stoch_k"] <= previous["stoch_d"]
    )
    bearish_stoch = (
        latest["stoch_k"] < latest["stoch_d"]
        and previous["stoch_k"] >= previous["stoch_d"]
    )

    if bullish_stoch:
        bullish_score += 1
        bullish_reasons.append("Bullish stochastic crossover")

    if bearish_stoch:
        bearish_score += 1
        bearish_reasons.append("Bearish stochastic crossover")

    # 2) Stochastic location
    if latest["stoch_k"] <= 40:
        bullish_score += 1
        bullish_reasons.append("Stochastic in lower zone")

    if latest["stoch_k"] >= 60:
        bearish_score += 1
        bearish_reasons.append("Stochastic in upper zone")

    # 3) OBVM alignment
    if latest["obvm"] > latest["obvm_signal"]:
        bullish_score += 1
        bullish_reasons.append("OBVM above signal")

    if latest["obvm"] < latest["obvm_signal"]:
        bearish_score += 1
        bearish_reasons.append("OBVM below signal")

    # 4) Price vs EMA
    if latest["close"] > latest["ema_9"]:
        bullish_score += 1
        bullish_reasons.append("Close above EMA9")

    if latest["close"] < latest["ema_9"]:
        bearish_score += 1
        bearish_reasons.append("Close below EMA9")

    # 5) Price vs VWAP
    if latest["close"] > latest["vwap"]:
        bullish_score += 1
        bullish_reasons.append("Close above VWAP")

    if latest["close"] < latest["vwap"]:
        bearish_score += 1
        bearish_reasons.append("Close below VWAP")

    # 6) ATR supportive
    if (
        pd.notna(latest["atr_14"])
        and pd.notna(previous["atr_14"])
        and latest["atr_14"] >= previous["atr_14"]
    ):
        bullish_score += 1
        bearish_score += 1

    if bullish_score >= 4 and bullish_score > bearish_score:
        return {
            "trigger": "CALL_TRIGGER",
            "score": bullish_score,
            "reasons": bullish_reasons,
        }

    if bearish_score >= 4 and bearish_score > bullish_score:
        return {
            "trigger": "PUT_TRIGGER",
            "score": bearish_score,
            "reasons": bearish_reasons,
        }

    return {
        "trigger": "NO_TRIGGER",
        "score": max(bullish_score, bearish_score),
        "reasons": ["No clean trigger"],
    }
