import os
import sys
import asyncio
import logging

# ✅ FIX for PaaS запусков типа Bothost:
# Когда запускают /app/app/main.py как скрипт, Python не видит пакет "app".
BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # .../app/app
PROJECT_ROOT = os.path.dirname(BASE_DIR)                     # .../app
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from aiogram import Bot, Dispatcher
from app.core.config import BOT_TOKEN
from app.bot.handlers import router
from app.core.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await start_scheduler(bot)

    logging.info("Бот запущен и работает (polling).")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())