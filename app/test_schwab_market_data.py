import os
from dotenv import load_dotenv
from schwab.auth import easy_client


def main() -> None:
    load_dotenv()

    client = easy_client(
        api_key=os.getenv("SCHWAB_APP_KEY"),
        app_secret=os.getenv("SCHWAB_APP_SECRET"),
        callback_url=os.getenv("SCHWAB_CALLBACK_URL"),
        token_path=os.getenv("SCHWAB_TOKEN_PATH"),
    )

    # Quote test
    quote_response = client.get_quote("QQQ")
    print("QUOTE STATUS:", quote_response.status_code)
    print("QUOTE JSON:")
    print(quote_response.json())

    # Price history test
    history_response = client.get_price_history_every_five_minutes(
        "QQQ",
        need_extended_hours_data=True,
        need_previous_close=True,
    )
    print("\nHISTORY STATUS:", history_response.status_code)
    history_json = history_response.json()
    print("HISTORY KEYS:", history_json.keys())
    print("CANDLE COUNT:", len(history_json.get("candles", [])))


if __name__ == "__main__":
    main()
