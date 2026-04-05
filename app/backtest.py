import pandas as pd

from app.signals import generate_signal
from app.trigger_engine import get_trigger
from app.risk import build_trade_plan
from app.trade_manager import manage_open_trade

NY_TZ = "America/New_York"
ENTRY_START = "09:35"
ENTRY_END = "15:30"
FORCED_EXIT = "15:55"
COOLDOWN_MINUTES = 15


def _to_ny_timestamp(value) -> pd.Timestamp:
    ts = pd.to_datetime(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.tz_convert(NY_TZ)


def run_backtest(df: pd.DataFrame) -> pd.DataFrame:
    trades = []
    in_trade = False
    partial_taken = False
    trade_plan = None
    entry_index = None
    last_exit_time = None

    entry_start_time = pd.Timestamp(ENTRY_START).time()
    entry_end_time = pd.Timestamp(ENTRY_END).time()
    forced_exit_time = pd.Timestamp(FORCED_EXIT).time()

    for i in range(15, len(df)):
        current_df = df.iloc[: i + 1].copy()
        latest = current_df.iloc[-1]

        current_dt = _to_ny_timestamp(latest["datetime"])
        current_time = current_dt.time()

        if in_trade:
            # Force-flat rule at 15:55 NY time
            if current_time >= forced_exit_time:
                current_trade = trades[-1]
                current_trade["exit_time"] = latest["datetime"]
                current_trade["exit_price"] = latest["close"]
                current_trade["result"] = "FORCED_EOD_EXIT"

                in_trade = False
                partial_taken = False
                trade_plan = None
                entry_index = None
                last_exit_time = current_dt
                continue

            management = manage_open_trade(
                current_df, trade_plan, partial_taken=partial_taken
            )
            current_trade = trades[-1]

            if management["action"] == "TAKE_PARTIAL":
                partial_taken = True
                current_trade["partial_taken"] = True
                trade_plan["stop"] = management["new_stop"]

            elif management["action"] in ["EXIT_FULL", "EXIT_RUNNER"]:
                current_trade["exit_time"] = latest["datetime"]
                current_trade["exit_price"] = latest["close"]
                current_trade["result"] = management["action"]

                in_trade = False
                partial_taken = False
                trade_plan = None
                entry_index = None
                last_exit_time = current_dt

            elif management["action"] == "TIGHTEN_STOP":
                trade_plan["stop"] = management["new_stop"]

            elif management["action"] == "HOLD":
                trade_plan["stop"] = management["new_stop"]

            continue

        # Entry time window rule: only allow new entries from 09:35 to 15:30 NY time
        if current_time < entry_start_time or current_time > entry_end_time:
            continue

        # 15-minute cooldown after any exit
        if last_exit_time is not None:
            minutes_since_exit = (current_dt - last_exit_time).total_seconds() / 60
            if minutes_since_exit < COOLDOWN_MINUTES:
                continue

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
