from schwab_client.market_data import load_multi_timeframe_data as load_schwab_data


def load_multi_timeframe_data(
    symbol: str,
    period: str = "364d",
    include_extended_hours: bool = True,
) -> dict:
    """
    Schwab-backed loader.

    Parameters are kept for compatibility with existing calls in main.py,
    even though Schwab loading here does not use period/include_extended_hours
    the same way yfinance did.
    """
    return load_schwab_data(symbol)


# import pandas as pd
# import yfinance as yf


# def load_yfinance_data(
#     symbol: str,
#     period: str = "5d",
#     interval: str = "5m",
#     include_extended_hours: bool = True,
# ) -> pd.DataFrame:
#     df = yf.download(
#         tickers=symbol,
#         period=period,
#         interval=interval,
#         auto_adjust=False,
#         progress=False,
#         group_by="column",
#         prepost=include_extended_hours,
#     )

#     if df.empty:
#         return pd.DataFrame(
#             columns=["datetime", "open", "high", "low", "close", "volume"]
#         )

#     if isinstance(df.columns, pd.MultiIndex):
#         df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

#     df = df.reset_index()
#     df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]

#     if "datetime" not in df.columns:
#         if "date" in df.columns:
#             df = df.rename(columns={"date": "datetime"})
#         elif "index" in df.columns:
#             df = df.rename(columns={"index": "datetime"})

#     required_cols = ["datetime", "open", "high", "low", "close", "volume"]
#     df = df[required_cols].copy()
#     df["datetime"] = pd.to_datetime(df["datetime"], utc=True)

#     df = df.sort_values("datetime").reset_index(drop=True)

#     return df


# def load_multi_timeframe_data(
#     symbol: str,
#     period: str = "5d",
#     include_extended_hours: bool = True,
# ) -> dict[str, pd.DataFrame]:
#     return {
#         "3m": load_yfinance_data(
#             symbol,
#             period=period,
#             interval="5m",  # placeholder until broker data
#             include_extended_hours=include_extended_hours,
#         ),
#         "5m": load_yfinance_data(
#             symbol,
#             period=period,
#             interval="5m",
#             include_extended_hours=include_extended_hours,
#         ),
#         "15m": load_yfinance_data(
#             symbol,
#             period=period,
#             interval="15m",
#             include_extended_hours=include_extended_hours,
#         ),
#         "30m": load_yfinance_data(
#             symbol,
#             period=period,
#             interval="30m",
#             include_extended_hours=include_extended_hours,
#         ),
#     }
