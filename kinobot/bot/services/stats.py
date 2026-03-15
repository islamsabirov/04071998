from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import CodeUsage, Movie, User


async def get_basic_stats(session: AsyncSession) -> dict:
    stats: dict = {}
    now = datetime.now(timezone.utc)

    q_users: Select = select(func.count()).select_from(User)
    stats["total_users"] = int((await session.execute(q_users)).scalar_one() or 0)

    for label, days in [("24h", 1), ("7d", 7), ("30d", 30)]:
        since = now - timedelta(days=days)
        q = select(func.count()).select_from(User).where(User.joined_at >= since)
        stats[f"joined_{label}"] = int((await session.execute(q)).scalar_one() or 0)

    active_since = now - timedelta(hours=24)
    q_active: Select = select(func.count()).select_from(User).where(
        User.last_active >= active_since
    )
    stats["active_24h"] = int((await session.execute(q_active)).scalar_one() or 0)

    q_codes: Select = select(func.count()).select_from(CodeUsage)
    stats["total_code_usages"] = int((await session.execute(q_codes)).scalar_one() or 0)

    q_vip: Select = select(func.count()).select_from(User).where(
        User.is_vip.is_(True), User.vip_until.isnot(None), User.vip_until > now
    )
    stats["active_vip_users"] = int((await session.execute(q_vip)).scalar_one() or 0)

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)
    q_today: Select = (
        select(func.count())
        .select_from(CodeUsage)
        .where(CodeUsage.used_at >= today_start, CodeUsage.used_at < tomorrow_start)
    )
    stats["today_code_usages"] = int((await session.execute(q_today)).scalar_one() or 0)

    q_movies: Select = select(func.count()).select_from(Movie).where(Movie.is_active.is_(True))
    stats["active_movies"] = int((await session.execute(q_movies)).scalar_one() or 0)

    q_premium: Select = select(func.count()).select_from(Movie).where(
        Movie.is_active.is_(True), Movie.is_premium.is_(True)
    )
    stats["premium_movies"] = int((await session.execute(q_premium)).scalar_one() or 0)

    return stats


async def get_movie_stats(session: AsyncSession, limit: int = 20) -> list[dict]:
    """Har bir kino uchun yuklanishlar sonini qaytaradi (top N)."""
    stmt = (
        select(
            Movie.code,
            Movie.title,
            Movie.is_premium,
            func.count(CodeUsage.id).label("total"),
        )
        .join(CodeUsage, CodeUsage.movie_id == Movie.id, isouter=True)
        .where(Movie.is_active.is_(True))
        .group_by(Movie.id, Movie.code, Movie.title, Movie.is_premium)
        .order_by(func.count(CodeUsage.id).desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [
        {"code": r.code, "title": r.title, "is_premium": r.is_premium, "total": r.total}
        for r in result.all()
    ]


async def get_latest_vip_users(session: AsyncSession, limit: int = 20) -> list[User]:
    stmt: Select = (
        select(User)
        .where(User.is_vip.is_(True))
        .order_by(User.vip_until.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_all_user_ids(session: AsyncSession) -> list[int]:
    result = await session.execute(select(User.telegram_id))
    return [row[0] for row in result.all()]
