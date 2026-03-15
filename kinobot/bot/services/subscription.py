from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatMember

from bot.config import settings
from bot.db.models import RequiredChannel


async def get_active_channels(session: AsyncSession) -> list[RequiredChannel]:
    result = await session.execute(
        select(RequiredChannel).where(RequiredChannel.is_active.is_(True))
    )
    return list(result.scalars().all())


async def check_subscription(
    bot: Bot, user_id: int, session: AsyncSession
) -> tuple[bool, list[str]]:
    """
    Barcha faol kanallarga obunani tekshiradi.

    :return: (is_member, not_subscribed_links_list)
    """
    channels = await get_active_channels(session)

    # Agar DB da kanal yo'q bo'lsa, config dagi REQUIRED_CHANNEL ni tekshir
    if not channels:
        env_channel = settings.required_channel
        if not env_channel:
            return True, []
        channels_to_check: list[tuple[str, str]] = [(env_channel, env_channel)]
    else:
        channels_to_check = [
            (ch.channel_id, ch.invite_link or ch.channel_id) for ch in channels
        ]

    not_subscribed: list[str] = []
    for channel_id, display_link in channels_to_check:
        try:
            member: ChatMember = await bot.get_chat_member(
                chat_id=channel_id, user_id=user_id
            )
            status = getattr(member, "status", None)
            if status not in {"member", "administrator", "creator"}:
                not_subscribed.append(display_link)
        except TelegramBadRequest:
            not_subscribed.append(display_link)

    return len(not_subscribed) == 0, not_subscribed
