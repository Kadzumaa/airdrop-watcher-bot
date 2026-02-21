import os

def env_bool(name: str, default: bool=False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1","true","yes","y","on"}

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_URL = os.getenv("DB_URL", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))

ENABLE_DEFILLAMA = env_bool("ENABLE_DEFILLAMA", True)
ENABLE_COINGECKO = env_bool("ENABLE_COINGECKO", True)
ENABLE_DROPSEARN = env_bool("ENABLE_DROPSEARN", True)
ENABLE_GITHUB = env_bool("ENABLE_GITHUB", True)
ENABLE_DOCS_MONITOR = env_bool("ENABLE_DOCS_MONITOR", True)
