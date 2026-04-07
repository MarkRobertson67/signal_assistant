import pandas as pd


def get_empty_frame():
    return pd.DataFrame(
        columns=["datetime", "open", "high", "low", "close", "volume"]
    )


if __name__ == "__main__":
    print(get_empty_frame())
    