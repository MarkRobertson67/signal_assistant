import threading
from typing import Any

import pandas as pd
from ibapi.common import BarData

from ibkr.client import IBClient


class MarketDataClient(IBClient):
    def __init__(self) -> None:
        super().__init__()
        self.historical_data: dict[int, list[dict[str, Any]]] = {}
        self.historical_done: dict[int, threading.Event] = {}

    def historicalData(self, reqId: int, bar: BarData) -> None:
        self.historical_data.setdefault(reqId, []).append(
            {
                "datetime": bar.date,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
        )

    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:
        if reqId in self.historical_done:
            self.historical_done[reqId].set()

    def get_historical_bars(
        self,
        req_id: int,
        contract,
        duration_str: str = "2 D",
        bar_size: str = "3 mins",
        what_to_show: str = "TRADES",
        use_rth: int = 0,
    ) -> pd.DataFrame:
        done_event = threading.Event()
        self.historical_done[req_id] = done_event
        self.historical_data[req_id] = []

        self.reqHistoricalData(
            reqId=req_id,
            contract=contract,
            endDateTime="",
            durationStr=duration_str,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=use_rth,
            formatDate=1,
            keepUpToDate=False,
            chartOptions=[],
        )

        done_event.wait(timeout=20)

        rows = self.historical_data.get(req_id, [])
        df = pd.DataFrame(rows)
        if not df.empty:
            df["datetime"] = pd.to_datetime(df["datetime"])
        return df
    