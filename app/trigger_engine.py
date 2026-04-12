import pandas as pd


def _safe(value):
    if pd.isna(value):
        return None
    return float(value)


def _is_bearish_rejection(candle: pd.Series) -> bool:
    open_ = _safe(candle["open"])
    high = _safe(candle["high"])
    low = _safe(candle["low"])
    close = _safe(candle["close"])

    if None in [open_, high, low, close]:
        return False

    body = abs(close - open_)
    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low

    return (
        upper_wick > body
        and upper_wick > lower_wick
        and close <= open_
    )


def _is_bullish_rejection(candle: pd.Series) -> bool:
    open_ = _safe(candle["open"])
    high = _safe(candle["high"])
    low = _safe(candle["low"])
    close = _safe(candle["close"])

    if None in [open_, high, low, close]:
        return False

    body = abs(close - open_)
    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low

    return (
        lower_wick > body
        and lower_wick > upper_wick
        and close >= open_
    )


def get_trigger(df: pd.DataFrame) -> dict:
    if len(df) < 2:
        return {
            "trigger": "NO_TRIGGER",
            "score": 0,
            "reasons": ["Not enough trigger data"],
        }

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    # Need ema_5 for your intended strategy
    if "ema_5" not in df.columns:
        return {
            "trigger": "NO_TRIGGER",
            "score": 0,
            "reasons": ["ema_5 not available"],
        }

    # -------------------------
    # PUT trigger logic
    # reject high -> break prior low -> short
    # -------------------------
    put_reasons = []
    put_score = 0

    previous_is_bear_reject = _is_bearish_rejection(previous)
    if previous_is_bear_reject:
        put_score += 1
        put_reasons.append("Prior candle is bearish rejection candle")

    if latest["low"] < previous["low"]:
        put_score += 1
        put_reasons.append("Current candle broke prior low")

    if latest["close"] < latest["open"]:
        put_score += 1
        put_reasons.append("Current candle closed red")

    if latest["close"] < latest["ema_5"]:
        put_score += 1
        put_reasons.append("Current candle closed below EMA5")

    put_confirmation_hits = 0

    if latest["close"] < latest["vwap"]:
        put_confirmation_hits += 1
        put_reasons.append("Close below VWAP")

    if latest["close"] < latest["ema_9"]:
        put_confirmation_hits += 1
        put_reasons.append("Close below EMA9")

    if pd.notna(latest.get("psar")) and latest["close"] < latest["psar"]:
        put_confirmation_hits += 1
        put_reasons.append("PSAR bearish")

    if put_confirmation_hits >= 1:
        put_score += 1

    # -------------------------
    # CALL trigger logic
    # reject low -> break prior high -> long
    # -------------------------
    call_reasons = []
    call_score = 0

    previous_is_bull_reject = _is_bullish_rejection(previous)
    if previous_is_bull_reject:
        call_score += 1
        call_reasons.append("Prior candle is bullish rejection candle")

    if latest["high"] > previous["high"]:
        call_score += 1
        call_reasons.append("Current candle broke prior high")

    if latest["close"] > latest["open"]:
        call_score += 1
        call_reasons.append("Current candle closed green")

    if latest["close"] > latest["ema_5"]:
        call_score += 1
        call_reasons.append("Current candle closed above EMA5")

    call_confirmation_hits = 0

    if latest["close"] > latest["vwap"]:
        call_confirmation_hits += 1
        call_reasons.append("Close above VWAP")

    if latest["close"] > latest["ema_9"]:
        call_confirmation_hits += 1
        call_reasons.append("Close above EMA9")

    if pd.notna(latest.get("psar")) and latest["close"] > latest["psar"]:
        call_confirmation_hits += 1
        call_reasons.append("PSAR bullish")

    if call_confirmation_hits >= 1:
        call_score += 1

    # Final trigger decision
    if put_score >= 5 and put_score > call_score:
        return {
            "trigger": "PUT_TRIGGER",
            "score": put_score,
            "reasons": put_reasons,
        }

    if call_score >= 5 and call_score > put_score:
        return {
            "trigger": "CALL_TRIGGER",
            "score": call_score,
            "reasons": call_reasons,
        }

    return {
        "trigger": "NO_TRIGGER",
        "score": max(call_score, put_score),
        "reasons": ["No clean trigger"],
    }
