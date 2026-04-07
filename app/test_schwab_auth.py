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

    print("Connected successfully")
    print(client)


if __name__ == "__main__":
    main()
