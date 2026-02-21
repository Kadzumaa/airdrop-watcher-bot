
import asyncio, os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from app.bot.handlers import router
from app.core.scheduler import start_scheduler
from app.data.db import init_db

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await start_scheduler(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
