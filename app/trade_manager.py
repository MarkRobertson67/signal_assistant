import pandas as pd


def manage_open_trade(
    df: pd.DataFrame,
    trade_plan: dict,
    partial_taken: bool = False,
) -> dict:
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    direction = trade_plan["direction"]
    stop = trade_plan["stop"]

    # CALL logic
    if direction == "CALL":
        # Hard stop
        if latest["low"] <= stop:
            return {
                "action": "EXIT_FULL",
                "reason": "Stop hit",
                "new_stop": stop,
            }

        # Take first partial sooner
        if not partial_taken:
            risk = trade_plan["entry"] - trade_plan["stop"]
            tp1_dynamic = trade_plan["entry"] + risk * 1.0

            if latest["high"] >= tp1_dynamic:
                return {
                    "action": "TAKE_PARTIAL",
                    "reason": "Reached 1R partial",
                    "new_stop": trade_plan["entry"],
                }

        # Momentum fade exit
        if (
            latest["stoch_k"] < previous["stoch_k"]
            and latest["close"] < latest["ema_9"]
        ):
            return {
                "action": "EXIT_RUNNER",
                "reason": "Momentum reversal",
                "new_stop": latest["ema_9"],
            }

        # Trail runner
        new_stop = max(stop, latest["ema_9"] - latest["atr_14"])
        return {
            "action": "HOLD",
            "reason": "Trend intact",
            "new_stop": round(new_stop, 2),
        }

    # PUT logic
    else:
        if latest["high"] >= stop:
            return {
                "action": "EXIT_FULL",
                "reason": "Stop hit",
                "new_stop": stop,
            }

        if not partial_taken:
            risk = trade_plan["stop"] - trade_plan["entry"]
            tp1_dynamic = trade_plan["entry"] - risk * 1.0

            if latest["low"] <= tp1_dynamic:
                return {
                    "action": "TAKE_PARTIAL",
                    "reason": "Reached 1R partial",
                    "new_stop": trade_plan["entry"],
                }

        if (
            latest["stoch_k"] > previous["stoch_k"]
            and latest["close"] > latest["ema_9"]
        ):
            return {
                "action": "EXIT_RUNNER",
                "reason": "Momentum reversal",
                "new_stop": latest["ema_9"],
            }

        new_stop = min(stop, latest["ema_9"] + latest["atr_14"])
        return {
            "action": "HOLD",
            "reason": "Trend intact",
            "new_stop": round(new_stop, 2),
        }
