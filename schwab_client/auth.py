from pathlib import Path


TOKEN_PATH = Path("tokens/token.json")
TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)

print("Schwab auth module ready.")
print("Waiting for API approval and app key creation.")
