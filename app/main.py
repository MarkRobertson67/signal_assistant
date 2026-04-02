from pathlib import Path

from app.config import IBConfig
from app.contracts import stock_contract
from ibkr.market_data import MarketDataClient


def main() -> None:
    cfg = IBConfig()
    client = MarketDataClient()

    print(f"Connecting to IBKR at {cfg.host}:{cfg.port} (client_id={cfg.client_id})...")
    client.connect(cfg.host, cfg.port, cfg.client_id)
    client.start_background_loop()

    if not client.connected_event.wait(timeout=10):
        raise TimeoutError("Could not establish IBKR connection. Check TWS/Gateway API settings.")

    print("Connected to IBKR.")

    qqq = stock_contract("QQQ")
    tqqq = stock_contract("TQQQ")

    qqq_3m = client.get_historical_bars(req_id=1001, contract=qqq, duration_str="2 D", bar_size="3 mins")
    qqq_5m = client.get_historical_bars(req_id=1002, contract=qqq, duration_str="5 D", bar_size="5 mins")
    tqqq_3m = client.get_historical_bars(req_id=1003, contract=tqqq, duration_str="2 D", bar_size="3 mins")

    outdir = Path("data/raw")
    outdir.mkdir(parents=True, exist_ok=True)

    qqq_3m.to_csv(outdir / "qqq_3m.csv", index=False)
    qqq_5m.to_csv(outdir / "qqq_5m.csv", index=False)
    tqqq_3m.to_csv(outdir / "tqqq_3m.csv", index=False)

    print("Saved:")
    print(f"  {outdir / 'qqq_3m.csv'}")
    print(f"  {outdir / 'qqq_5m.csv'}")
    print(f"  {outdir / 'tqqq_3m.csv'}")

    client.disconnect()
    print("Disconnected.")


if __name__ == "__main__":
    main()
    