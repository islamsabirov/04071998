from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings
from .models import Base

engine = create_async_engine(settings.db_url, echo=False, pool_pre_ping=True)

AsyncSessionMaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """Barcha jadvallarni yaratadi (agar mavjud bo'lmasa)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
