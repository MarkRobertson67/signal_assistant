import pandas as pd
import yfinance as yf


def load_yfinance_data(
    symbol: str,
    period: str = "5d",
    interval: str = "5m",
) -> pd.DataFrame:
    df = yf.download(
        tickers=symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        group_by="column",
    )

    if df.empty:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    df = df.reset_index()
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]

    if "datetime" not in df.columns:
        if "date" in df.columns:
            df = df.rename(columns={"date": "datetime"})
        elif "index" in df.columns:
            df = df.rename(columns={"index": "datetime"})

    df = df[["datetime", "open", "high", "low", "close", "volume"]].copy()
    df["datetime"] = pd.to_datetime(df["datetime"])

    return df


def load_multi_timeframe_data(symbol: str, period: str = "5d") -> dict[str, pd.DataFrame]:
    return {
        "3m": load_yfinance_data(symbol, period=period, interval="5m"),   # placeholder until broker data
        "5m": load_yfinance_data(symbol, period=period, interval="5m"),
        "15m": load_yfinance_data(symbol, period=period, interval="15m"),
        "30m": load_yfinance_data(symbol, period=period, interval="30m"),
    }
