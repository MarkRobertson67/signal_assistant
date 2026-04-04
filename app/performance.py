import pandas as pd


def calculate_trade_pnl(trades_df: pd.DataFrame) -> pd.DataFrame:
    df = trades_df.copy()

    closed = df[df["result"] != "OPEN"].copy()

    if closed.empty:
        return closed

    def calc_row(row):
        if row["direction"] == "CALL":
            pnl = row["exit_price"] - row["entry"]
            risk = row["entry"] - row["stop"]
        else:
            pnl = row["entry"] - row["exit_price"]
            risk = row["stop"] - row["entry"]

        r_multiple = pnl / risk if risk != 0 else 0

        return pd.Series(
            {
                "pnl": round(pnl, 2),
                "r_multiple": round(r_multiple, 2),
                "win": pnl > 0,
            }
        )

    metrics = closed.apply(calc_row, axis=1)
    closed = pd.concat([closed, metrics], axis=1)

    return closed


def summarize_performance(closed_df: pd.DataFrame) -> dict:
    if closed_df.empty:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "avg_pnl": 0,
            "avg_r": 0,
            "total_pnl": 0,
            "profit_factor": 0,
        }

    total_trades = len(closed_df)
    wins = closed_df[closed_df["pnl"] > 0]
    losses = closed_df[closed_df["pnl"] <= 0]

    gross_profit = wins["pnl"].sum()
    gross_loss = abs(losses["pnl"].sum())

    profit_factor = (
        gross_profit / gross_loss if gross_loss != 0 else float("inf")
    )

    return {
        "total_trades": total_trades,
        "win_rate": round((len(wins) / total_trades) * 100, 2),
        "avg_pnl": round(closed_df["pnl"].mean(), 2),
        "avg_r": round(closed_df["r_multiple"].mean(), 2),
        "total_pnl": round(closed_df["pnl"].sum(), 2),
        "profit_factor": round(profit_factor, 2),
    }
