from dataclasses import dataclass
import os


@dataclass(frozen=True)
class IBConfig:
    host: str = os.getenv("IB_HOST", "127.0.0.1")
    port: int = int(os.getenv("IB_PORT", "7497"))
    client_id: int = int(os.getenv("IB_CLIENT_ID", "7"))
    account_mode: str = os.getenv("IB_ACCOUNT_MODE", "paper")
    