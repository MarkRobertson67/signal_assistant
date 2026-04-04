import pandas as pd


def _bool_to_int(value: bool) -> int:
    return 1 if value else 0


def get_30m_bias(df: pd.DataFrame) -> dict:
    """
    Determine primary trend bias from 30m data.

    Bullish signals:
    - close > ema_9
    - stoch_k > stoch_d
    - obvm > obvm_signal
    - atr rising or stable

    Bearish signals:
    - inverse of the above
    """
    if len(df) < 2:
        return {
            "bias": "NEUTRAL",
            "bull_score": 0,
            "bear_score": 0,
            "reasons": ["Not enough 30m data"],
        }

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    bullish_conditions = {
        "Close above EMA9": latest["close"] > latest["ema_9"],
        "Stochastic bullish": latest["stoch_k"] > latest["stoch_d"],
        "OBVM above signal": latest["obvm"] > latest["obvm_signal"],
        "ATR rising or stable": latest["atr_14"] >= previous["atr_14"],
    }

    bearish_conditions = {
        "Close below EMA9": latest["close"] < latest["ema_9"],
        "Stochastic bearish": latest["stoch_k"] < latest["stoch_d"],
        "OBVM below signal": latest["obvm"] < latest["obvm_signal"],
        "ATR rising or stable": latest["atr_14"] >= previous["atr_14"],
    }

    bull_score = sum(_bool_to_int(v) for v in bullish_conditions.values())
    bear_score = sum(_bool_to_int(v) for v in bearish_conditions.values())

    reasons = []
    for label, passed in bullish_conditions.items():
        if passed:
            reasons.append(f"30m bullish: {label}")
    for label, passed in bearish_conditions.items():
        if passed:
            reasons.append(f"30m bearish: {label}")

    if bull_score >= 3 and bull_score > bear_score:
        bias = "BULLISH"
    elif bear_score >= 3 and bear_score > bull_score:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    return {
        "bias": bias,
        "bull_score": bull_score,
        "bear_score": bear_score,
        "reasons": reasons,
    }


def get_15m_state(df: pd.DataFrame, direction: str) -> dict:
    """
    15m does NOT need to be perfect.
    It should be:
    - SUPPORTIVE
    - NEUTRAL
    - CONTRADICTORY

    For CALLs, only block if 2+ bearish conditions.
    For PUTs, only block if 2+ bullish conditions.
    """
    if len(df) < 2:
        return {
            "state": "NEUTRAL",
            "block_trade": False,
            "score": 0,
            "reasons": ["Not enough 15m data"],
        }

    latest = df.iloc[-1]

    bullish_flags = {
        "Close above EMA9": latest["close"] > latest["ema_9"],
        "Stochastic bullish": latest["stoch_k"] > latest["stoch_d"],
        "OBVM above signal": latest["obvm"] > latest["obvm_signal"],
    }

    bearish_flags = {
        "Close below EMA9": latest["close"] < latest["ema_9"],
        "Stochastic bearish": latest["stoch_k"] < latest["stoch_d"],
        "OBVM below signal": latest["obvm"] < latest["obvm_signal"],
    }

    bullish_score = sum(_bool_to_int(v) for v in bullish_flags.values())
    bearish_score = sum(_bool_to_int(v) for v in bearish_flags.values())

    reasons = []

    if direction == "CALL":
        for label, passed in bullish_flags.items():
            if passed:
                reasons.append(f"15m supportive for CALL: {label}")
        for label, passed in bearish_flags.items():
            if passed:
                reasons.append(f"15m bearish warning for CALL: {label}")

        if bearish_score >= 2:
            state = "CONTRADICTORY"
            block_trade = True
            score = bearish_score
        elif bullish_score >= 2:
            state = "SUPPORTIVE"
            block_trade = False
            score = bullish_score
        else:
            state = "NEUTRAL"
            block_trade = False
            score = bullish_score

    elif direction == "PUT":
        for label, passed in bearish_flags.items():
            if passed:
                reasons.append(f"15m supportive for PUT: {label}")
        for label, passed in bullish_flags.items():
            if passed:
                reasons.append(f"15m bullish warning for PUT: {label}")

        if bullish_score >= 2:
            state = "CONTRADICTORY"
            block_trade = True
            score = bullish_score
        elif bearish_score >= 2:
            state = "SUPPORTIVE"
            block_trade = False
            score = bearish_score
        else:
            state = "NEUTRAL"
            block_trade = False
            score = bearish_score
    else:
        state = "NEUTRAL"
        block_trade = False
        score = 0
        reasons.append("Unknown direction")

    return {
        "state": state,
        "block_trade": block_trade,
        "score": score,
        "reasons": reasons,
    }
