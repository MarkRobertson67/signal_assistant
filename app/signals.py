import pandas as pd


def _safe_value(value) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _bearish_rejection_candle(candle: pd.Series) -> tuple[bool, list[str]]:
    reasons = []

    open_ = _safe_value(candle["open"])
    high = _safe_value(candle["high"])
    low = _safe_value(candle["low"])
    close = _safe_value(candle["close"])

    if None in [open_, high, low, close]:
        return False, ["Bearish rejection check unavailable"]

    body = abs(close - open_)
    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low
    candle_range = high - low

    if candle_range <= 0:
        return False, ["Zero-range candle"]

    if upper_wick > body:
        reasons.append("Large upper wick rejection")
    if close < open_:
        reasons.append("Bearish close on rejection candle")
    if upper_wick > lower_wick:
        reasons.append("Upper wick dominates lower wick")

    is_valid = (
        upper_wick > body
        and close <= open_
        and upper_wick > lower_wick
    )

    return is_valid, reasons


def _bullish_rejection_candle(candle: pd.Series) -> tuple[bool, list[str]]:
    reasons = []

    open_ = _safe_value(candle["open"])
    high = _safe_value(candle["high"])
    low = _safe_value(candle["low"])
    close = _safe_value(candle["close"])

    if None in [open_, high, low, close]:
        return False, ["Bullish rejection check unavailable"]

    body = abs(close - open_)
    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low
    candle_range = high - low

    if candle_range <= 0:
        return False, ["Zero-range candle"]

    if lower_wick > body:
        reasons.append("Large lower wick rejection")
    if close > open_:
        reasons.append("Bullish close on rejection candle")
    if lower_wick > upper_wick:
        reasons.append("Lower wick dominates upper wick")

    is_valid = (
        lower_wick > body
        and close >= open_
        and lower_wick > upper_wick
    )

    return is_valid, reasons


def _put_trend_weakening(df: pd.DataFrame) -> tuple[bool, list[str]]:
    reasons = []

    if len(df) < 4:
        return False, ["Not enough bars for PUT trend weakening"]

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    conditions = 0

    # 5 EMA flat/down
    if latest["ema_9"] <= prev["ema_9"]:
        conditions += 1
        reasons.append("EMA9 flat/down")

    # Lower high
    if prev["high"] < prev2["high"]:
        conditions += 1
        reasons.append("Lower high formed")

    # Break of prior low
    if latest["low"] < prev["low"]:
        conditions += 1
        reasons.append("Prior candle low broken")

    # Price below EMA9
    if latest["close"] < latest["ema_9"]:
        conditions += 1
        reasons.append("Close below EMA9")

    return conditions >= 1, reasons


def _call_trend_weakening(df: pd.DataFrame) -> tuple[bool, list[str]]:
    reasons = []

    if len(df) < 4:
        return False, ["Not enough bars for CALL trend weakening"]

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    conditions = 0

    # 5 EMA flat/up
    if latest["ema_9"] >= prev["ema_9"]:
        conditions += 1
        reasons.append("EMA9 flat/up")

    # Higher low after decline
    if prev["low"] > prev2["low"]:
        conditions += 1
        reasons.append("Higher low formed")

    # Break of prior high
    if latest["high"] > prev["high"]:
        conditions += 1
        reasons.append("Prior candle high broken")

    # Price above EMA9
    if latest["close"] > latest["ema_9"]:
        conditions += 1
        reasons.append("Close above EMA9")

    return conditions >= 1, reasons


def _put_location_ok(df: pd.DataFrame) -> tuple[bool, list[str]]:
    latest = df.iloc[-1]
    reasons = []
    hits = 0

    if pd.notna(latest["atr_14"]) and pd.notna(latest["vwap"]):
        if latest["close"] > latest["vwap"] + latest["atr_14"]:
            hits += 1
            reasons.append("Extended > 1 ATR above VWAP")

    if bool(latest.get("swing_high", False)):
        hits += 1
        reasons.append("At local swing high")

    if latest["close"] > latest["ema_9"]:
        hits += 1
        reasons.append("Price still elevated above EMA9")

    return hits >= 1, reasons


def _call_location_ok(df: pd.DataFrame) -> tuple[bool, list[str]]:
    latest = df.iloc[-1]
    reasons = []
    hits = 0

    if pd.notna(latest["atr_14"]) and pd.notna(latest["vwap"]):
        if latest["close"] < latest["vwap"] - latest["atr_14"]:
            hits += 1
            reasons.append("Extended > 1 ATR below VWAP")

    if bool(latest.get("swing_low", False)):
        hits += 1
        reasons.append("At local swing low")

    if latest["close"] < latest["ema_9"]:
        hits += 1
        reasons.append("Price still depressed below EMA9")

    return hits >= 1, reasons


def _put_confirmation_ok(candle: pd.Series) -> tuple[bool, list[str]]:
    reasons = []
    hits = 0

    if candle["close"] < candle["vwap"]:
        hits += 1
        reasons.append("Close below VWAP")

    if candle["close"] < candle["ema_9"]:
        hits += 1
        reasons.append("Close below EMA9")

    if pd.notna(candle.get("psar")) and candle["close"] < candle["psar"]:
        hits += 1
        reasons.append("PSAR bearish")

    return hits >= 1, reasons


def _call_confirmation_ok(candle: pd.Series) -> tuple[bool, list[str]]:
    reasons = []
    hits = 0

    if candle["close"] > candle["vwap"]:
        hits += 1
        reasons.append("Close above VWAP")

    if candle["close"] > candle["ema_9"]:
        hits += 1
        reasons.append("Close above EMA9")

    if pd.notna(candle.get("psar")) and candle["close"] > candle["psar"]:
        hits += 1
        reasons.append("PSAR bullish")

    return hits >= 1, reasons


def generate_signal(df: pd.DataFrame) -> dict:
    if len(df) < 4:
        return {
            "signal": "WAIT",
            "score": 0,
            "reasons": ["Not enough data"],
        }

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    put_reasons = []
    call_reasons = []

    # We treat PREV candle as the rejection candle candidate.
    put_trend_ok, reasons = _put_trend_weakening(df.iloc[:-1])
    put_reasons.extend(reasons)

    put_location_ok, reasons = _put_location_ok(df.iloc[:-1])
    put_reasons.extend(reasons)

    put_rejection_ok, reasons = _bearish_rejection_candle(prev)
    put_reasons.extend(reasons)

    put_confirm_ok, reasons = _put_confirmation_ok(latest)
    put_reasons.extend(reasons)

    put_score = sum([
        int(put_trend_ok),
        int(put_location_ok),
        int(put_rejection_ok),
        int(put_confirm_ok),
    ])

    call_trend_ok, reasons = _call_trend_weakening(df.iloc[:-1])
    call_reasons.extend(reasons)

    call_location_ok, reasons = _call_location_ok(df.iloc[:-1])
    call_reasons.extend(reasons)

    call_rejection_ok, reasons = _bullish_rejection_candle(prev)
    call_reasons.extend(reasons)

    call_confirm_ok, reasons = _call_confirmation_ok(latest)
    call_reasons.extend(reasons)

    call_score = sum([
        int(call_trend_ok),
        int(call_location_ok),
        int(call_rejection_ok),
        int(call_confirm_ok),
    ])

    if put_score >= 3 and put_score > call_score:
        return {
            "signal": "PUT_SETUP",
            "score": put_score,
            "reasons": put_reasons,
        }

    if call_score >= 3 and call_score > put_score:
        return {
            "signal": "CALL_SETUP",
            "score": call_score,
            "reasons": call_reasons,
        }

    return {
        "signal": "WAIT",
        "score": max(call_score, put_score),
        "reasons": ["No valid reversal setup"],
    }
