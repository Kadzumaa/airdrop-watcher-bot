import os

def _env(key: str, default: str = "") -> str:
    return (os.getenv(key, default) or "").strip()

BOT_TOKEN = _env("BOT_TOKEN")
ADMIN_CHAT_ID = _env("ADMIN_CHAT_ID")

CHECK_INTERVAL_MINUTES = int(_env("CHECK_INTERVAL_MINUTES", "5") or 5)

# Фичи источников (можно включать/выключать в Bothost env)
ENABLE_DROPSEARN = _env("ENABLE_DROPSEARN", "1") == "1"
ENABLE_DEFILLAMA = _env("ENABLE_DEFILLAMA", "1") == "1"
ENABLE_COINGECKO = _env("ENABLE_COINGECKO", "1") == "1"
ENABLE_DOCS_MONITOR = _env("ENABLE_DOCS_MONITOR", "1") == "1"

# ✅ Главное: БД
# Если DATABASE_URL не задан — используем SQLite файл на диске
DATABASE_URL = _env("DATABASE_URL")
if not DATABASE_URL:
    # Bothost Dockerfile создаёт /app/data, туда и кладём базу
    DATABASE_URL = "sqlite+aiosqlite:////app/data/bot.db"