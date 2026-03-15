from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db.models import BotAdmin


async def is_admin(session: AsyncSession, telegram_id: int) -> bool:
    """Super-admin (.env) yoki bot-admin (DB) ekanligini tekshiradi."""
    if telegram_id in settings.admin_ids:
        return True
    result = await session.execute(
        select(BotAdmin).where(BotAdmin.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none() is not None


def is_super_admin(telegram_id: int) -> bool:
    """Faqat .env dagi ADMIN_IDS ni tekshiradi."""
    return telegram_id in settings.admin_ids


async def add_admin(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    added_by: int,
) -> tuple[bool, str]:
    """
    Yangi admin qo'shadi.
    :return: (success, message)
    """
    if telegram_id in settings.admin_ids:
        return False, "Bu foydalanuvchi allaqachon super-admin (.env)."

    result = await session.execute(
        select(BotAdmin).where(BotAdmin.telegram_id == telegram_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return False, f"ID {telegram_id} allaqachon admin."

    admin = BotAdmin(
        telegram_id=telegram_id,
        username=username,
        added_by=added_by,
    )
    session.add(admin)
    await session.commit()
    return True, f"✅ {telegram_id} admin qilib qo'shildi."


async def remove_admin(
    session: AsyncSession, telegram_id: int
) -> tuple[bool, str]:
    """
    Adminni o'chiradi (faqat DB adminlarini; super-adminlarni o'chirib bo'lmaydi).
    :return: (success, message)
    """
    if telegram_id in settings.admin_ids:
        return False, "Super-adminni bot orqali o'chirib bo'lmaydi (.env dan o'chiring)."

    result = await session.execute(
        select(BotAdmin).where(BotAdmin.telegram_id == telegram_id)
    )
    admin = result.scalar_one_or_none()
    if not admin:
        return False, f"ID {telegram_id} adminlar ro'yxatida topilmadi."

    await session.delete(admin)
    await session.commit()
    return True, f"✅ {telegram_id} admin ro'yxatidan o'chirildi."


async def list_admins(session: AsyncSession) -> list[BotAdmin]:
    result = await session.execute(select(BotAdmin).order_by(BotAdmin.added_at.desc()))
    return list(result.scalars().all())
