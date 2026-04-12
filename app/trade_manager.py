import pandas as pd


def manage_open_trade(
    df: pd.DataFrame,
    trade_plan: dict,
    partial_taken: bool = False,
) -> dict:
    if len(df) < 2:
        return {
            "action": "HOLD",
            "reason": "Not enough bars to manage trade",
            "new_stop": trade_plan["stop"],
        }

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    direction = trade_plan["direction"]
    stop = float(trade_plan["stop"])
    entry = float(trade_plan["entry"])
    tp1 = float(trade_plan["tp1"])
    tp2 = float(trade_plan["tp2"])

    # -------------------------
    # CALL trade management
    # -------------------------
    if direction == "CALL":
        # Hard stop
        if latest["low"] <= stop:
            return {
                "action": "EXIT_FULL",
                "reason": "Hard stop hit",
                "new_stop": stop,
            }

        # First target / scale out
        if not partial_taken and latest["high"] >= tp1:
            return {
                "action": "TAKE_PARTIAL",
                "reason": "Target 1 hit (0.5 ATR objective)",
                "new_stop": entry,
            }

        # Runner target after partial
        if partial_taken and latest["high"] >= tp2:
            return {
                "action": "EXIT_RUNNER",
                "reason": "Target 2 hit (1.0 ATR objective)",
                "new_stop": entry,
            }

        # Optional failure exit for runner after partial
        if partial_taken:
            if (
                latest["close"] < latest["ema_9"]
                and latest["close"] < previous["close"]
            ):
                return {
                    "action": "EXIT_RUNNER",
                    "reason": "Runner lost momentum below EMA9",
                    "new_stop": entry,
                }

        return {
            "action": "HOLD",
            "reason": "CALL trade still valid",
            "new_stop": stop if not partial_taken else entry,
        }

    # -------------------------
    # PUT trade management
    # -------------------------
    if latest["high"] >= stop:
        return {
            "action": "EXIT_FULL",
            "reason": "Hard stop hit",
            "new_stop": stop,
        }

    # First target / scale out
    if not partial_taken and latest["low"] <= tp1:
        return {
            "action": "TAKE_PARTIAL",
            "reason": "Target 1 hit (0.5 ATR objective)",
            "new_stop": entry,
        }

    # Runner target after partial
    if partial_taken and latest["low"] <= tp2:
        return {
            "action": "EXIT_RUNNER",
            "reason": "Target 2 hit (1.0 ATR objective)",
            "new_stop": entry,
        }

    # Optional failure exit for runner after partial
    if partial_taken:
        if (
            latest["close"] > latest["ema_9"]
            and latest["close"] > previous["close"]
        ):
            return {
                "action": "EXIT_RUNNER",
                "reason": "Runner lost momentum above EMA9",
                "new_stop": entry,
            }

    return {
        "action": "HOLD",
        "reason": "PUT trade still valid",
        "new_stop": stop if not partial_taken else entry,
    }
