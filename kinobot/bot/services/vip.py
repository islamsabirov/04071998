from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Payment, User


async def refresh_vip_flag(session: AsyncSession, user: User) -> User:
    """vip_until tugagan bo'lsa, is_vip ni False ga o'zgartiradi."""
    now = datetime.now(timezone.utc)
    if user.vip_until and user.vip_until.tzinfo is None:
        # timezone-naive vaqtni UTC ga o'zgartir
        from datetime import timezone as tz
        user.vip_until = user.vip_until.replace(tzinfo=tz.utc)
    if user.vip_until and user.vip_until < now:
        user.is_vip = False
        user.vip_until = None
        await session.flush()
    return user


async def set_vip(session: AsyncSession, user: User, days: int) -> User:
    """Foydalanuvchini VIP qiladi yoki VIP muddatini uzaytiradi."""
    now = datetime.now(timezone.utc)
    if user.vip_until:
        if user.vip_until.tzinfo is None:
            user.vip_until = user.vip_until.replace(tzinfo=timezone.utc)
        base_time = user.vip_until if user.vip_until > now else now
    else:
        base_time = now
    user.is_vip = True
    user.vip_until = base_time + timedelta(days=days)
    await session.flush()
    return user


async def is_vip(session: AsyncSession, user: User) -> bool:
    user = await refresh_vip_flag(session, user)
    return bool(user.is_vip and user.vip_until)


async def get_payment_by_id(session: AsyncSession, payment_id: int) -> Payment | None:
    stmt = select(Payment).where(Payment.id == payment_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
