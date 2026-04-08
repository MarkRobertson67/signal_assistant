import os
import pandas as pd
from dotenv import load_dotenv
from schwab.auth import easy_client

load_dotenv()


def get_client():
    return easy_client(
        api_key=os.getenv("SCHWAB_APP_KEY"),
        app_secret=os.getenv("SCHWAB_APP_SECRET"),
        callback_url=os.getenv("SCHWAB_CALLBACK_URL"),
        token_path=os.getenv("SCHWAB_TOKEN_PATH"),
    )


def get_empty_frame():
    return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])


def _candles_to_df(candles: list[dict]) -> pd.DataFrame:
    if not candles:
        return get_empty_frame()

    df = pd.DataFrame(candles).copy()

    df["datetime"] = pd.to_datetime(df["datetime"], unit="ms", utc=True)

    df = df[["datetime", "open", "high", "low", "close", "volume"]].copy()

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values("datetime").reset_index(drop=True)
    return df


def resample_ohlcv(df: pd.DataFrame, interval: str) -> pd.DataFrame:
    if df.empty:
        return get_empty_frame()

    temp = df.copy().set_index("datetime")

    resampled = temp.resample(interval).agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )

    resampled = resampled.dropna().reset_index()
    return resampled


def get_price_history_1m(symbol: str = "QQQ") -> pd.DataFrame:
    client = get_client()
    response = client.get_price_history_every_minute(
        symbol,
        need_extended_hours_data=True,
        need_previous_close=True,
    )
    return _candles_to_df(response.json().get("candles", []))


def get_price_history_5m(symbol: str = "QQQ") -> pd.DataFrame:
    client = get_client()
    response = client.get_price_history_every_five_minutes(
        symbol,
        need_extended_hours_data=True,
        need_previous_close=True,
    )
    return _candles_to_df(response.json().get("candles", []))


def get_price_history_15m(symbol: str = "QQQ") -> pd.DataFrame:
    client = get_client()
    response = client.get_price_history_every_fifteen_minutes(
        symbol,
        need_extended_hours_data=True,
        need_previous_close=True,
    )
    return _candles_to_df(response.json().get("candles", []))


def get_price_history_30m(symbol: str = "QQQ") -> pd.DataFrame:
    client = get_client()
    response = client.get_price_history_every_thirty_minutes(
        symbol,
        need_extended_hours_data=True,
        need_previous_close=True,
    )
    return _candles_to_df(response.json().get("candles", []))


def load_multi_timeframe_data(symbol: str = "QQQ") -> dict[str, pd.DataFrame]:
    df_1m = get_price_history_1m(symbol)
    df_5m = get_price_history_5m(symbol)
    df_15m = get_price_history_15m(symbol)
    df_30m = get_price_history_30m(symbol)

    return {
        "1m": df_1m,
        "3m": resample_ohlcv(df_1m, "3min"),
        "5m": df_5m,
        "15m": df_15m,
        "30m": df_30m,
    }


if __name__ == "__main__":
    data = load_multi_timeframe_data("QQQ")

    print("1m rows:", len(data["1m"]))
    print("3m rows:", len(data["3m"]))
    print("5m rows:", len(data["5m"]))
    print("15m rows:", len(data["15m"]))
    print("30m rows:", len(data["30m"]))

    print("\nFirst 5 rows (5m):")
    print(data["5m"].head().to_string(index=False))

    print("\nLast 5 rows (5m):")
    print(data["5m"].tail().to_string(index=False))
