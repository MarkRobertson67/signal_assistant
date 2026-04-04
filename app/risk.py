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

    latest = df.iloc[-1]

    if direction == "CALL":
        entry = latest["close"]

        swing_lows = df[df["swing_low"] == True]
        if not swing_lows.empty:
            stop = swing_lows.iloc[-1]["low"]
        else:
            stop = entry - latest["atr_14"]

        risk_per_share = entry - stop
        tp1 = entry + (risk_per_share * 1.5)
        tp2 = entry + (risk_per_share * 2.0)

    elif direction == "PUT":
        entry = latest["close"]

        swing_highs = df[df["swing_high"] == True]
        if not swing_highs.empty:
            stop = swing_highs.iloc[-1]["high"]
        else:
            stop = entry + latest["atr_14"]

        risk_per_share = stop - entry
        tp1 = entry - (risk_per_share * 1.5)
        tp2 = entry - (risk_per_share * 2.0)

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

    rr_tp1 = abs(tp1 - entry) / abs(risk_per_share) if risk_per_share != 0 else None
    rr_tp2 = abs(tp2 - entry) / abs(risk_per_share) if risk_per_share != 0 else None

    return {
        "direction": direction,
        "entry": round(entry, 2),
        "stop": round(stop, 2),
        "tp1": round(tp1, 2),
        "tp2": round(tp2, 2),
        "risk_per_share": round(risk_per_share, 2),
        "rr_tp1": round(rr_tp1, 2) if rr_tp1 is not None else None,
        "rr_tp2": round(rr_tp2, 2) if rr_tp2 is not None else None,
        "reason": "Trade plan built successfully",
    }
