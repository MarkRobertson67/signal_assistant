import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

NY_TZ = "America/New_York"


def plot_day_trades(
    df: pd.DataFrame,
    trades_df: pd.DataFrame,
    trade_date: str | None = None,
    session_start: str = "04:00",
    session_end: str = "18:00",
    trade_marker_start: str = "09:30",
    trade_marker_end: str = "18:00",
) -> None:
    if df.empty:
        print("Price dataframe is empty.")
        return

    temp_df = df.copy()

    # Convert timestamps to New York time
    temp_df["datetime"] = pd.to_datetime(temp_df["datetime"], utc=True)
    temp_df["datetime_ny"] = temp_df["datetime"].dt.tz_convert(NY_TZ)
    temp_df["trade_date"] = temp_df["datetime_ny"].dt.date

    if trade_date is None:
        selected_date = temp_df["trade_date"].max()
    else:
        selected_date = pd.to_datetime(trade_date).date()

    session_open = pd.Timestamp(f"{selected_date} {session_start}", tz=NY_TZ)
    session_close = pd.Timestamp(f"{selected_date} {session_end}", tz=NY_TZ)
    marker_open = pd.Timestamp(f"{selected_date} {trade_marker_start}", tz=NY_TZ)
    marker_close = pd.Timestamp(f"{selected_date} {trade_marker_end}", tz=NY_TZ)
    regular_open = pd.Timestamp(f"{selected_date} 09:30", tz=NY_TZ)
    regular_close = pd.Timestamp(f"{selected_date} 16:00", tz=NY_TZ)

    # Show full session window, including premarket / after-hours if data exists
    day_df = temp_df[
        (temp_df["trade_date"] == selected_date)
        & (temp_df["datetime_ny"] >= session_open)
        & (temp_df["datetime_ny"] <= session_close)
    ].copy()

    if day_df.empty:
        print(
            f"No price data found for {selected_date} between "
            f"{session_start} and {session_end} New York time."
        )
        return

    temp_trades = trades_df.copy()

    if not temp_trades.empty:
        temp_trades["entry_time"] = pd.to_datetime(temp_trades["entry_time"], utc=True)
        temp_trades["entry_time_ny"] = temp_trades["entry_time"].dt.tz_convert(NY_TZ)
        temp_trades["entry_date"] = temp_trades["entry_time_ny"].dt.date

        if "exit_time" in temp_trades.columns:
            temp_trades["exit_time"] = pd.to_datetime(
                temp_trades["exit_time"], utc=True
            )
            temp_trades["exit_time_ny"] = temp_trades["exit_time"].dt.tz_convert(NY_TZ)
            temp_trades["exit_date"] = temp_trades["exit_time_ny"].dt.date
        else:
            temp_trades["exit_time"] = pd.NaT
            temp_trades["exit_time_ny"] = pd.NaT
            temp_trades["exit_date"] = pd.NaT

        day_trades = temp_trades[
            (temp_trades["entry_date"] == selected_date)
            | (temp_trades["exit_date"] == selected_date)
        ].copy()
    else:
        day_trades = pd.DataFrame()

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(16, 10),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1.5, 1.5]},
    )

    ax_price, ax_obvm, ax_stoch = axes

    # ---------- PRICE PANEL ----------
    ax_price.plot(day_df["datetime_ny"], day_df["close"], label="Close")
    ax_price.plot(day_df["datetime_ny"], day_df["ema_9"], label="EMA9")
    ax_price.plot(day_df["datetime_ny"], day_df["vwap"], label="VWAP")

    if "psar" in day_df.columns:
        ax_price.scatter(
            day_df["datetime_ny"],
            day_df["psar"],
            s=14,
            label="PSAR",
            zorder=4,
        )

    entry_label_added = False
    exit_label_added = False

    if not day_trades.empty:
        for _, trade in day_trades.iterrows():
            if (
                trade["entry_date"] == selected_date
                and pd.notna(trade["entry_time_ny"])
                and marker_open <= trade["entry_time_ny"] <= marker_close
            ):
                entry_marker = "^" if trade["direction"] == "CALL" else "v"

                ax_price.scatter(
                    trade["entry_time_ny"],
                    trade["entry"],
                    marker=entry_marker,
                    s=120,
                    label="Entry" if not entry_label_added else None,
                    zorder=5,
                )
                entry_label_added = True

            if (
                pd.notna(trade["exit_time_ny"])
                and trade["exit_date"] == selected_date
                and marker_open <= trade["exit_time_ny"] <= marker_close
            ):
                ax_price.scatter(
                    trade["exit_time_ny"],
                    trade["exit_price"],
                    marker="x",
                    s=120,
                    label="Exit" if not exit_label_added else None,
                    zorder=5,
                )
                exit_label_added = True

    ax_price.set_title(
        f"Trades for {selected_date} (NY time, session {session_start}-{session_end})"
    )
    ax_price.grid(True)
    ax_price.legend(loc="upper left")
    ax_price.set_xlim(session_open, session_close)

    # ---------- OBVM PANEL ----------
    ax_obvm.plot(day_df["datetime_ny"], day_df["obvm"], label="OBVM")
    ax_obvm.plot(day_df["datetime_ny"], day_df["obvm_signal"], label="OBVM Signal")
    ax_obvm.set_title("OBVM")
    ax_obvm.grid(True)
    ax_obvm.legend(loc="upper left")
    ax_obvm.set_xlim(session_open, session_close)

    # ---------- STOCHASTIC PANEL ----------
    ax_stoch.plot(day_df["datetime_ny"], day_df["stoch_k"], label="%K")
    ax_stoch.plot(day_df["datetime_ny"], day_df["stoch_d"], label="%D")
    ax_stoch.axhline(80, linestyle="--")
    ax_stoch.axhline(20, linestyle="--")
    ax_stoch.set_title("Stochastic")
    ax_stoch.grid(True)
    ax_stoch.legend(loc="upper left")
    ax_stoch.set_xlim(session_open, session_close)

    # ---------- SESSION SHADING ----------
    # Premarket: 04:00 -> 09:30
    if session_open < regular_open:
        ax_price.axvspan(session_open, regular_open, alpha=0.10)
        ax_obvm.axvspan(session_open, regular_open, alpha=0.10)
        ax_stoch.axvspan(session_open, regular_open, alpha=0.10)

    # After-hours: 16:00 -> 18:00
    if session_close > regular_close:
        ax_price.axvspan(regular_close, session_close, alpha=0.10)
        ax_obvm.axvspan(regular_close, session_close, alpha=0.10)
        ax_stoch.axvspan(regular_close, session_close, alpha=0.10)

    # ---------- X-AXIS FORMATTING ----------
    locator = mdates.HourLocator(interval=1, tz=day_df["datetime_ny"].dt.tz)
    formatter = mdates.DateFormatter("%H:%M", tz=day_df["datetime_ny"].dt.tz)

    ax_stoch.xaxis.set_major_locator(locator)
    ax_stoch.xaxis.set_major_formatter(formatter)

    # force exact session window
    for ax in axes:
        ax.set_xlim(session_open, session_close)

    fig.autofmt_xdate()

    plt.tight_layout()
    plt.show()


def plot_last_n_days(
    df: pd.DataFrame,
    trades_df: pd.DataFrame,
    num_days: int = 5,
    session_start: str = "04:00",
    session_end: str = "18:00",
    trade_marker_start: str = "09:30",
    trade_marker_end: str = "18:00",
) -> None:
    if df.empty:
        print("Price dataframe is empty.")
        return

    temp_df = df.copy()
    temp_df["datetime"] = pd.to_datetime(temp_df["datetime"], utc=True)
    temp_df["datetime_ny"] = temp_df["datetime"].dt.tz_convert(NY_TZ)
    temp_df["trade_date"] = temp_df["datetime_ny"].dt.date

    # Only keep rows that fall inside the display session
    start_time = pd.Timestamp(session_start).time()
    end_time = pd.Timestamp(session_end).time()

    temp_df = temp_df[
        temp_df["datetime_ny"].dt.time.between(
            start_time,
            end_time,
            inclusive="both",
        )
    ].copy()

    unique_days = sorted(temp_df["trade_date"].dropna().unique())

    if not unique_days:
        print("No trading days found.")
        return

    selected_days = unique_days[-num_days:]

    for day in selected_days:
        plot_day_trades(
            df=df,
            trades_df=trades_df,
            trade_date=str(day),
            session_start=session_start,
            session_end=session_end,
            trade_marker_start=trade_marker_start,
            trade_marker_end=trade_marker_end,
        )
