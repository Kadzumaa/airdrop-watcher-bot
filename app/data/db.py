
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
DATABASE_URL=os.getenv("DB_URL")
engine=create_async_engine(DATABASE_URL, echo=False)
SessionLocal=async_sessionmaker(engine, expire_on_commit=False)
Base=declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
