from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)

async def init_db():
    # импорт моделей нужен, чтобы SQLAlchemy увидел таблицы
    from app.data.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)