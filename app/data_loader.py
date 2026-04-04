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
        return pd.DataFrame(
            columns=["datetime", "open", "high", "low", "close", "volume"]
        )

    # Flatten MultiIndex columns if yfinance returns them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    df = df.reset_index()

    # Normalize names
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]

    # Handle datetime/date column
    if "datetime" not in df.columns:
        if "date" in df.columns:
            df = df.rename(columns={"date": "datetime"})
        elif "index" in df.columns:
            df = df.rename(columns={"index": "datetime"})

    # Make sure expected columns exist
    expected_map = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }

    missing = [
        col
        for col in ["datetime", "open", "high", "low", "close", "volume"]
        if col not in df.columns
    ]
    if missing:
        raise KeyError(
            f"Missing expected columns after yfinance load: {missing}. Actual columns: {list(df.columns)}"
        )

    df = df[["datetime", "open", "high", "low", "close", "volume"]].copy()
    df["datetime"] = pd.to_datetime(df["datetime"])

    return df
