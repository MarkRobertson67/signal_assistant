import pandas as pd

from app.signals import generate_signal
from app.trigger_engine import get_trigger
from app.risk import build_trade_plan
from app.trade_manager import manage_open_trade

NY_TZ = "America/New_York"
ENTRY_START = "09:35"
ENTRY_END = "15:45"
FORCED_EXIT = "15:55"
COOLDOWN_MINUTES = 30

REGULAR_OPEN = "09:30"
MIN_FIRST_BAR_VOL_PCT = 0.80  # trade only if first bar volume >= 80% of prior average


def _to_ny_timestamp(value) -> pd.Timestamp:
    ts = pd.to_datetime(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.tz_convert(NY_TZ)


def _build_daily_first_bar_filter(
    df: pd.DataFrame,
    regular_open: str = REGULAR_OPEN,
    min_pct: float = MIN_FIRST_BAR_VOL_PCT,
) -> dict:
    """
    Build a per-day allow/skip map based on the first regular-session bar volume.

    Uses PRIOR days only to avoid look-ahead bias.
    """
    temp = df.copy()
    temp["datetime"] = pd.to_datetime(temp["datetime"], utc=True)
    temp["datetime_ny"] = temp["datetime"].dt.tz_convert(NY_TZ)
    temp["ny_date"] = temp["datetime_ny"].dt.date
    temp["ny_time"] = temp["datetime_ny"].dt.time

    regular_open_time = pd.Timestamp(regular_open).time()

    first_bar_rows = temp[temp["ny_time"] == regular_open_time].copy()
    first_bar_rows = first_bar_rows.sort_values("datetime_ny")

    day_filter = {}
    prior_volumes = []

    for _, row in first_bar_rows.iterrows():
        trade_date = row["ny_date"]
        first_bar_volume = pd.to_numeric(row["volume"], errors="coerce")

        if pd.isna(first_bar_volume):
            day_filter[trade_date] = False
            continue

        # No prior history yet -> allow the day
        if len(prior_volumes) == 0:
            day_filter[trade_date] = True
        else:
            prior_avg = sum(prior_volumes) / len(prior_volumes)
            threshold = prior_avg * min_pct
            day_filter[trade_date] = first_bar_volume >= threshold

        prior_volumes.append(float(first_bar_volume))

    return day_filter


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

    # Build day-level first-bar volume filter once
    day_allowed_map = _build_daily_first_bar_filter(df)

    for i in range(15, len(df)):
        current_df = df.iloc[: i + 1].copy()
        latest = current_df.iloc[-1]

        current_dt = _to_ny_timestamp(latest["datetime"])
        current_time = current_dt.time()
        current_date = current_dt.date()

        # Default to allow if the day is missing from the map
        day_is_allowed = day_allowed_map.get(current_date, True)

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

        # Skip the whole day if first regular-session bar volume is too weak
        if not day_is_allowed:
            continue

        # Entry time window rule
        if current_time < entry_start_time or current_time > entry_end_time:
            continue

        # Cooldown after exit
        if last_exit_time is not None:
            minutes_since_exit = (current_dt - last_exit_time).total_seconds() / 60
            if minutes_since_exit < COOLDOWN_MINUTES:
                continue

        signal_result = generate_signal(current_df)
        trigger_result = get_trigger(current_df)

        close_price = latest["close"]
        psar_value = latest["psar"] if "psar" in latest.index else pd.NA

        call_psar_ok = pd.notna(psar_value) and close_price > psar_value
        put_psar_ok = pd.notna(psar_value) and close_price < psar_value

        if (
            signal_result["signal"] == "CALL"
            and trigger_result["trigger"] == "CALL_TRIGGER"
            and call_psar_ok
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
            and put_psar_ok
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

    # Safety close if sample ends while still in trade
    if in_trade and len(trades) > 0 and trades[-1]["exit_time"] is None:
        final_bar = df.iloc[-1]
        trades[-1]["exit_time"] = final_bar["datetime"]
        trades[-1]["exit_price"] = final_bar["close"]
        trades[-1]["result"] = "FINAL_BAR_EXIT"

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
