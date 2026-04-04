import pandas as pd

from app.backtest import run_backtest, summarize_backtest
from app.data_loader import load_multi_timeframe_data
from app.indicators import (
    atr,
    ema,
    obv,
    obv_modified,
    rsi,
    stochastic,
    swing_high,
    swing_low,
    vwap,
)
from app.risk import build_trade_plan
from app.signals import generate_signal
from app.trade_manager import manage_open_trade
from app.trend_bias import get_15m_state, get_30m_bias
from app.trigger_engine import get_trigger
from app.performance import calculate_trade_pnl, summarize_performance


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["ema_9"] = ema(df["close"], 9)
    df["vwap"] = vwap(df)
    df["atr_14"] = atr(df, 14)
    df["obv"] = obv(df)

    obvm_df = obv_modified(df, 7, 10)
    df["obvm"] = obvm_df["obvm"]
    df["obvm_signal"] = obvm_df["obvm_signal"]

    df["rsi_14"] = rsi(df["close"], 14)

    stoch = stochastic(df, 14, 3)
    df["stoch_k"] = stoch["%K"]
    df["stoch_d"] = stoch["%D"]

    df["swing_high"] = swing_high(df)
    df["swing_low"] = swing_low(df)

    return df


def main() -> None:
    data = load_multi_timeframe_data("TQQQ", period="5d")

    df_5m = add_indicators(data["5m"])
    df_15m = add_indicators(data["15m"])
    df_30m = add_indicators(data["30m"])

    # Use 5m as the primary preview / signal / trigger dataframe for now
    df = df_5m

    print("\n=== DATASET INFO ===")
    print(f"5m rows: {len(df_5m)}")
    print(f"15m rows: {len(df_15m)}")
    print(f"30m rows: {len(df_30m)}")

    print("\n=== FIRST 5 ROWS (5M) ===")
    head_preview = df.head(5).copy()
    numeric_cols_full = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "ema_9",
        "vwap",
        "atr_14",
        "obv",
        "obvm",
        "obvm_signal",
        "rsi_14",
        "stoch_k",
        "stoch_d",
    ]
    head_preview[numeric_cols_full] = head_preview[numeric_cols_full].round(2)
    print(head_preview.to_string(index=False))

    print("\n=== LAST 5 ROWS (5M) ===")
    cols = [
        "datetime",
        "close",
        "ema_9",
        "vwap",
        "atr_14",
        "obv",
        "obvm",
        "obvm_signal",
        "rsi_14",
        "stoch_k",
        "stoch_d",
        "swing_high",
        "swing_low",
    ]
    preview = df[cols].tail(5).copy()
    numeric_cols = [
        "close",
        "ema_9",
        "vwap",
        "atr_14",
        "obv",
        "obvm",
        "obvm_signal",
        "rsi_14",
        "stoch_k",
        "stoch_d",
    ]
    preview[numeric_cols] = preview[numeric_cols].round(2)
    print(preview.to_string(index=False))

    signal_result = generate_signal(df)

    print("\n=== SIGNAL (5M) ===")
    print(f"Signal: {signal_result['signal']}")
    print(f"Score: {signal_result['score']}/4")

    print("\nReasons:")
    for reason in signal_result["reasons"]:
        print(f"- {reason}")

    bias_30m = get_30m_bias(df_30m)
    state_15m_call = get_15m_state(df_15m, "CALL")
    state_15m_put = get_15m_state(df_15m, "PUT")

    print("\n=== 30M BIAS ===")
    print(f"Bias: {bias_30m['bias']}")
    print(f"Bull Score: {bias_30m['bull_score']}")
    print(f"Bear Score: {bias_30m['bear_score']}")
    print("Reasons:")
    for reason in bias_30m["reasons"]:
        print(f"- {reason}")

    print("\n=== 15M STATE FOR CALL ===")
    print(f"State: {state_15m_call['state']}")
    print(f"Block Trade: {state_15m_call['block_trade']}")
    print("Reasons:")
    for reason in state_15m_call["reasons"]:
        print(f"- {reason}")

    print("\n=== 15M STATE FOR PUT ===")
    print(f"State: {state_15m_put['state']}")
    print(f"Block Trade: {state_15m_put['block_trade']}")
    print("Reasons:")
    for reason in state_15m_put["reasons"]:
        print(f"- {reason}")

    trigger_result = get_trigger(df_5m)

    print("\n=== LOWER TIMEFRAME TRIGGER (5M) ===")
    print(f"Trigger: {trigger_result['trigger']}")
    print(f"Score: {trigger_result['score']}")
    print("Reasons:")
    for reason in trigger_result["reasons"]:
        print(f"- {reason}")

    if trigger_result["trigger"] == "CALL_TRIGGER":
        trade_plan = build_trade_plan(df_5m, "CALL")
    elif trigger_result["trigger"] == "PUT_TRIGGER":
        trade_plan = build_trade_plan(df_5m, "PUT")
    else:
        trade_plan = None

    print("\n=== TRADE PLAN ===")
    if trade_plan is None:
        print("No trade plan generated.")
    else:
        print(f"Direction: {trade_plan['direction']}")
        print(f"Entry: {trade_plan['entry']}")
        print(f"Stop: {trade_plan['stop']}")
        print(f"TP1: {trade_plan['tp1']}")
        print(f"TP2: {trade_plan['tp2']}")
        print(f"Risk/Share: {trade_plan['risk_per_share']}")
        print(f"RR to TP1: {trade_plan['rr_tp1']}")
        print(f"RR to TP2: {trade_plan['rr_tp2']}")
        print(f"Reason: {trade_plan['reason']}")

    print("\n=== TRADE MANAGEMENT ===")
    if trade_plan is None:
        print("No management action because no trade plan exists.")
        trades_df = pd.DataFrame()
    else:
        management_result = manage_open_trade(df_5m, trade_plan, partial_taken=False)
        print(f"Action: {management_result['action']}")
        print(f"Reason: {management_result['reason']}")
        print(f"New Stop: {management_result['new_stop']}")

        trades_df = run_backtest(df_5m)

    summary = summarize_backtest(trades_df)

    print("\n=== BACKTEST SUMMARY ===")
    print(f"Total Trades: {summary['total_trades']}")
    print(f"Closed Trades: {summary['closed_trades']}")
    print(f"Trades With Partial Taken: {summary['partials']}")

    print("\n=== BACKTEST TRADES ===")
    if trades_df.empty:
        print("No trades generated.")
    else:
        print(trades_df.to_string(index=False))

        closed_df = calculate_trade_pnl(trades_df)
    performance = summarize_performance(closed_df)

    print("\n=== PERFORMANCE METRICS ===")
    print(f"Closed Trades: {performance['total_trades']}")
    print(f"Win Rate: {performance['win_rate']}%")
    print(f"Average P&L: {performance['avg_pnl']}")
    print(f"Average R: {performance['avg_r']}")
    print(f"Total P&L: {performance['total_pnl']}")
    print(f"Profit Factor: {performance['profit_factor']}")

    print("\n=== CLOSED TRADE METRICS ===")
    if closed_df.empty:
        print("No closed trades.")
    else:
        print(closed_df.to_string(index=False))


if __name__ == "__main__":
    main()
