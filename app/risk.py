import pandas as pd


def build_trade_plan(df: pd.DataFrame, direction: str) -> dict:
    if len(df) < 2:
        return {
            "direction": direction,
            "entry": None,
            "stop": None,
            "tp1": None,
            "tp2": None,
            "risk_per_share": None,
            "rr_tp1": None,
            "rr_tp2": None,
            "reason": "Not enough data",
        }

    latest = df.iloc[-1]      # confirmation / trigger candle
    previous = df.iloc[-2]    # rejection candle

    atr_value = latest.get("atr_14")

    if pd.isna(atr_value) or atr_value is None:
        return {
            "direction": direction,
            "entry": None,
            "stop": None,
            "tp1": None,
            "tp2": None,
            "risk_per_share": None,
            "rr_tp1": None,
            "rr_tp2": None,
            "reason": "ATR not available",
        }

    entry = float(latest["close"])

    if direction == "CALL":
        rejection_low = float(previous["low"])

        stop = rejection_low - (0.1 * atr_value)
        tp1 = entry + (0.5 * atr_value)
        tp2 = entry + (1.0 * atr_value)
        risk_per_share = entry - stop

    elif direction == "PUT":
        rejection_high = float(previous["high"])

        stop = rejection_high + (0.1 * atr_value)
        tp1 = entry - (0.5 * atr_value)
        tp2 = entry - (1.0 * atr_value)
        risk_per_share = stop - entry

    else:
        return {
            "direction": direction,
            "entry": None,
            "stop": None,
            "tp1": None,
            "tp2": None,
            "risk_per_share": None,
            "rr_tp1": None,
            "rr_tp2": None,
            "reason": "Direction must be CALL or PUT",
        }

    if risk_per_share <= 0:
        return {
            "direction": direction,
            "entry": None,
            "stop": None,
            "tp1": None,
            "tp2": None,
            "risk_per_share": None,
            "rr_tp1": None,
            "rr_tp2": None,
            "reason": "Invalid stop placement relative to entry",
        }

    rr_tp1 = abs(tp1 - entry) / abs(risk_per_share)
    rr_tp2 = abs(tp2 - entry) / abs(risk_per_share)

    return {
        "direction": direction,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "tp1": round(tp1, 2),
        "tp2": round(tp2, 2),
        "risk_per_share": round(risk_per_share, 2),
        "rr_tp1": round(rr_tp1, 2),
        "rr_tp2": round(rr_tp2, 2),
        "reason": "Trade plan built from rejection candle + ATR framework",
    }
