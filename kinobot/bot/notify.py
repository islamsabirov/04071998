"""
To'lov webhook lari bot instance ga ega bo'lmaydi.
Shu modul global bot instance ni saqlaydi va notify funksiyalarini taqdim etadi.
"""
from __future__ import annotations

from aiogram import Bot

_bot: Bot | None = None


def set_bot(bot: Bot) -> None:
    global _bot
    _bot = bot


async def notify_vip_activated(telegram_id: int, days: int) -> None:
    if _bot is None:
        return
    try:
        await _bot.send_message(
            chat_id=telegram_id,
            text=(
                f"🎉 <b>VIP rejimingiz avtomatik faollashtirildi!</b>\n"
                f"📅 Muddat: <b>{days} kun</b>\n\n"
                "Barcha VIP imtiyozlardan foydalaning! 👑"
            ),
        )
    except Exception:
        pass
