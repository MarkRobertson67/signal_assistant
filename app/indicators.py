import pandas as pd
import numpy as np


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def vwap(df: pd.DataFrame) -> pd.Series:
    temp = df.copy()

    if "datetime" not in temp.columns:
        raise KeyError("DataFrame must contain a 'datetime' column for VWAP calculation.")

    temp["session_date"] = pd.to_datetime(temp["datetime"]).dt.date
    typical_price = (temp["high"] + temp["low"] + temp["close"]) / 3
    tpv = typical_price * temp["volume"]

    cumulative_tpv = tpv.groupby(temp["session_date"]).cumsum()
    cumulative_volume = temp["volume"].groupby(temp["session_date"]).cumsum()

    return cumulative_tpv / cumulative_volume


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift(1))
    low_close = np.abs(df["low"] - df["close"].shift(1))

    true_range = pd.concat(
        [high_low, high_close, low_close], axis=1
    ).max(axis=1)

    return true_range.rolling(window=period).mean()


def obv(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["close"].diff()).fillna(0)
    volume_flow = direction * df["volume"]
    return volume_flow.cumsum()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    lowest_low = df["low"].rolling(window=k_period).min()
    highest_high = df["high"].rolling(window=k_period).max()

    denominator = (highest_high - lowest_low).replace(0, np.nan)
    percent_k = 100 * ((df["close"] - lowest_low) / denominator)
    percent_d = percent_k.rolling(window=d_period).mean()

    return pd.DataFrame({
        "%K": percent_k,
        "%D": percent_d
    })


def swing_high(df: pd.DataFrame, lookback: int = 3) -> pd.Series:
    return df["high"] == df["high"].rolling(window=lookback * 2 + 1, center=True).max()


def swing_low(df: pd.DataFrame, lookback: int = 3) -> pd.Series:
    return df["low"] == df["low"].rolling(window=lookback * 2 + 1, center=True).min()


def obv_modified(
    df: pd.DataFrame,
    fast_period: int = 7,
    signal_period: int = 10
) -> pd.DataFrame:
    raw_obv = obv(df)

    obvm = raw_obv.ewm(span=fast_period, adjust=False).mean()
    signal = obvm.ewm(span=signal_period, adjust=False).mean()

    return pd.DataFrame({
        "obvm": obvm,
        "obvm_signal": signal
    })
