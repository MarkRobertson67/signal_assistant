from dotenv import load_dotenv
import os

load_dotenv()

print("TradeStation credentials loaded:")
print("CLIENT ID:", os.getenv("TS_CLIENT_ID"))
print("REDIRECT URI:", os.getenv("TS_REDIRECT_URI"))
