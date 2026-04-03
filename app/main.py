import pandas as pd

from app.indicators import (
    ema, vwap, atr, obv, rsi,
    stochastic, swing_high, swing_low,
    obv_modified
)
from app.signals import generate_signal


def build_sample_data() -> pd.DataFrame:
    data = {
        "datetime": pd.date_range("2026-04-03 09:30", periods=20, freq="3min"),
        "open": [
            100.0, 100.2, 100.4, 100.3, 100.6,
            100.9, 101.1, 101.0, 101.3, 101.5,
            101.2, 101.0, 100.8, 100.7, 100.5,
            100.3, 100.4, 100.6, 100.9, 101.1,
        ],
        "high": [
            100.3, 100.5, 100.6, 100.7, 101.0,
            101.2, 101.3, 101.4, 101.6, 101.7,
            101.3, 101.1, 100.9, 100.8, 100.6,
            100.5, 100.7, 101.0, 101.2, 101.4,
        ],
        "low": [
            99.9, 100.1, 100.2, 100.2, 100.5,
            100.8, 100.9, 100.9, 101.1, 101.1,
            100.9, 100.7, 100.6, 100.4, 100.2,
            100.1, 100.2, 100.5, 100.8, 101.0,
        ],
        "close": [
            100.2, 100.4, 100.3, 100.6, 100.9,
            101.1, 101.0, 101.3, 101.5, 101.2,
            101.0, 100.8, 100.7, 100.5, 100.3,
            100.4, 100.6, 100.9, 101.1, 101.3,
        ],
        "volume": [
            1200, 1500, 1400, 1700, 1800,
            2200, 2100, 2300, 2500, 2400,
            2600, 2000, 1900, 1800, 1700,
            1600, 1750, 2100, 2300, 2400,
        ],
    }
    return pd.DataFrame(data)


def main() -> None:
    df = build_sample_data()

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

    print("\n=== FULL DATA WITH INDICATORS ===")
    full_preview = df.copy()
    numeric_cols_full = [
        "open", "high", "low", "close", "volume",
        "ema_9", "vwap", "atr_14", "obv",
        "obvm", "obvm_signal",
        "rsi_14", "stoch_k", "stoch_d",
    ]
    full_preview[numeric_cols_full] = full_preview[numeric_cols_full].round(2)
    print(full_preview.to_string(index=False))

    print("\n=== LAST 5 ROWS ===")
    cols = [
        "datetime", "close", "ema_9", "vwap", "atr_14",
        "obv", "obvm", "obvm_signal",
        "rsi_14", "stoch_k", "stoch_d",
        "swing_high", "swing_low",
    ]
    preview = df[cols].tail(5).copy()
    numeric_cols = [
        "close", "ema_9", "vwap", "atr_14", "obv",
        "obvm", "obvm_signal",
        "rsi_14", "stoch_k", "stoch_d",
    ]
    preview[numeric_cols] = preview[numeric_cols].round(2)
    print(preview.to_string(index=False))

    signal = generate_signal(df)

    signal_result = generate_signal(df)

    print("\n=== SIGNAL ===")
    print(f"Signal: {signal_result['signal']}")
    print(f"Score: {signal_result['score']}/4")

    print("\nReasons:")
    for reason in signal_result["reasons"]:
        print(f"- {reason}")


if __name__ == "__main__":
    main()
