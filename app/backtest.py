import pandas as pd

from app.signals import generate_signal
from app.trigger_engine import get_trigger
from app.risk import build_trade_plan
from app.trade_manager import manage_open_trade


def run_backtest(df: pd.DataFrame) -> pd.DataFrame:
    trades = []
    in_trade = False
    partial_taken = False
    trade_plan = None
    entry_index = None

    for i in range(15, len(df)):
        current_df = df.iloc[: i + 1].copy()
        latest = current_df.iloc[-1]

        if not in_trade:
            signal_result = generate_signal(current_df)
            trigger_result = get_trigger(current_df)

            if (
                signal_result["signal"] == "CALL"
                and trigger_result["trigger"] == "CALL_TRIGGER"
            ):
                trade_plan = build_trade_plan(current_df, "CALL")
                in_trade = True
                partial_taken = False
                entry_index = i

                trades.append(
                    {
                        "entry_time": latest["datetime"],
                        "direction": "CALL",
                        "entry": trade_plan["entry"],
                        "stop": trade_plan["stop"],
                        "tp1": trade_plan["tp1"],
                        "tp2": trade_plan["tp2"],
                        "exit_time": None,
                        "exit_price": None,
                        "result": "OPEN",
                        "partial_taken": False,
                    }
                )

            elif (
                signal_result["signal"] == "PUT"
                and trigger_result["trigger"] == "PUT_TRIGGER"
            ):
                trade_plan = build_trade_plan(current_df, "PUT")
                in_trade = True
                partial_taken = False
                entry_index = i

                trades.append(
                    {
                        "entry_time": latest["datetime"],
                        "direction": "PUT",
                        "entry": trade_plan["entry"],
                        "stop": trade_plan["stop"],
                        "tp1": trade_plan["tp1"],
                        "tp2": trade_plan["tp2"],
                        "exit_time": None,
                        "exit_price": None,
                        "result": "OPEN",
                        "partial_taken": False,
                    }
                )

        else:
            management = manage_open_trade(
                current_df, trade_plan, partial_taken=partial_taken
            )
            current_trade = trades[-1]

            if management["action"] == "TAKE_PARTIAL":
                partial_taken = True
                current_trade["partial_taken"] = True

            elif management["action"] in ["EXIT_FULL", "EXIT_RUNNER"]:
                current_trade["exit_time"] = latest["datetime"]
                current_trade["exit_price"] = latest["close"]
                current_trade["result"] = management["action"]
                in_trade = False
                partial_taken = False
                trade_plan = None
                entry_index = None

            elif management["action"] == "TIGHTEN_STOP":
                trade_plan["stop"] = management["new_stop"]

    return pd.DataFrame(trades)


def summarize_backtest(trades_df: pd.DataFrame) -> dict:
    if trades_df.empty:
        return {
            "total_trades": 0,
            "closed_trades": 0,
            "partials": 0,
        }

    closed = trades_df[trades_df["result"] != "OPEN"]

    return {
        "total_trades": len(trades_df),
        "closed_trades": len(closed),
        "partials": int(trades_df["partial_taken"].sum()),
    }
