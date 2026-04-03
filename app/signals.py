import pandas as pd


def generate_signal(df: pd.DataFrame) -> dict:
    if len(df) < 2:
        return {
            "signal": "WAIT",
            "score": 0,
            "reasons": ["Not enough data"]
        }

    latest = df.iloc[-1]

    bullish_score = 0
    bearish_score = 0
    reasons = []

    # Price vs VWAP
    if latest["close"] > latest["vwap"]:
        bullish_score += 1
        reasons.append("Close above VWAP")
    else:
        bearish_score += 1
        reasons.append("Close below VWAP")

    # Price vs EMA
    if latest["close"] > latest["ema_9"]:
        bullish_score += 1
        reasons.append("Close above EMA9")
    else:
        bearish_score += 1
        reasons.append("Close below EMA9")

    # Stochastic
    if latest["stoch_k"] > latest["stoch_d"]:
        bullish_score += 1
        reasons.append("Stochastic bullish crossover")
    else:
        bearish_score += 1
        reasons.append("Stochastic bearish crossover")

    # OBV Modified
    if latest["obvm"] > latest["obvm_signal"]:
        bullish_score += 1
        reasons.append("OBVM above signal")
    else:
        bearish_score += 1
        reasons.append("OBVM below signal")

    # Final signal
    if bullish_score >= 3:
        signal = "CALL"
        score = bullish_score
    elif bearish_score >= 3:
        signal = "PUT"
        score = bearish_score
    else:
        signal = "WAIT"
        score = max(bullish_score, bearish_score)

    return {
        "signal": signal,
        "score": score,
        "reasons": reasons
    }
