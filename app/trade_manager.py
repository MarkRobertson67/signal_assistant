import pandas as pd


def manage_open_trade(
    df: pd.DataFrame, trade_plan: dict, partial_taken: bool = False
) -> dict:
    if trade_plan is None or len(df) < 2:
        return {
            "action": "NO_ACTION",
            "reason": "No trade plan or insufficient data",
            "new_stop": None,
        }

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    direction = trade_plan["direction"]
    entry = trade_plan["entry"]
    stop = trade_plan["stop"]
    tp1 = trade_plan["tp1"]

    # CALL trade management
    if direction == "CALL":
        # full stop loss
        if latest["close"] <= stop:
            return {
                "action": "EXIT_FULL",
                "reason": "Price hit stop level",
                "new_stop": stop,
            }

        # take partial at TP1
        if not partial_taken and latest["close"] >= tp1:
            return {
                "action": "TAKE_PARTIAL",
                "reason": "Price reached TP1",
                "new_stop": entry,
            }

        # after partial: move stop to breakeven and manage runner
        if partial_taken:
            if latest["stoch_k"] < latest["stoch_d"]:
                return {
                    "action": "EXIT_RUNNER",
                    "reason": "Stochastic rolled over after partial",
                    "new_stop": entry,
                }

            if latest["obvm"] < latest["obvm_signal"]:
                return {
                    "action": "EXIT_RUNNER",
                    "reason": "OBVM fell below signal after partial",
                    "new_stop": entry,
                }

            if (
                pd.notna(latest["atr_14"])
                and pd.notna(previous["atr_14"])
                and latest["atr_14"] < previous["atr_14"]
            ):
                return {
                    "action": "TIGHTEN_STOP",
                    "reason": "ATR weakening after partial",
                    "new_stop": entry,
                }

            return {
                "action": "HOLD_RUNNER",
                "reason": "Momentum still supportive after partial",
                "new_stop": entry,
            }

        return {
            "action": "HOLD",
            "reason": "Trade active, TP1 not reached",
            "new_stop": stop,
        }

    # PUT trade management
    if direction == "PUT":
        if latest["close"] >= stop:
            return {
                "action": "EXIT_FULL",
                "reason": "Price hit stop level",
                "new_stop": stop,
            }

        if not partial_taken and latest["close"] <= tp1:
            return {
                "action": "TAKE_PARTIAL",
                "reason": "Price reached TP1",
                "new_stop": entry,
            }

        if partial_taken:
            if latest["stoch_k"] > latest["stoch_d"]:
                return {
                    "action": "EXIT_RUNNER",
                    "reason": "Stochastic turned up after partial",
                    "new_stop": entry,
                }

            if latest["obvm"] > latest["obvm_signal"]:
                return {
                    "action": "EXIT_RUNNER",
                    "reason": "OBVM rose above signal after partial",
                    "new_stop": entry,
                }

            if (
                pd.notna(latest["atr_14"])
                and pd.notna(previous["atr_14"])
                and latest["atr_14"] < previous["atr_14"]
            ):
                return {
                    "action": "TIGHTEN_STOP",
                    "reason": "ATR weakening after partial",
                    "new_stop": entry,
                }

            return {
                "action": "HOLD_RUNNER",
                "reason": "Momentum still supportive after partial",
                "new_stop": entry,
            }

        return {
            "action": "HOLD",
            "reason": "Trade active, TP1 not reached",
            "new_stop": stop,
        }

    return {
        "action": "NO_ACTION",
        "reason": "Unknown trade direction",
        "new_stop": None,
    }
