from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot import keyboards
from bot.db import AsyncSessionMaker
from bot.services.codes import get_movie_by_code, get_or_create_user, register_code_usage
from bot.services.limits import can_use_code
from bot.services.subscription import check_subscription
from bot.services.vip import is_vip

router = Router()

# Oddiy foydalanuvchi uchun kunlik kod limiti
DAILY_LIMIT = 3


@router.message(F.text & ~F.text.startswith("/"))
async def handle_code(message: Message) -> None:
    code = message.text.strip()
    if not code:
        return

    bot = message.bot

    async with AsyncSessionMaker() as session:  # type: AsyncSession
        # Kanal obunasini tekshirish
        is_member, not_subscribed = await check_subscription(bot, message.from_user.id, session)
        if not is_member:
            text = (
                "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz kerak.\n\n"
                "Obuna bo'lgach, <b>✅ Obuna bo'ldim</b> tugmasini bosing."
            )
            await message.answer(
                text,
                reply_markup=keyboards.subscribe_keyboard(not_subscribed),
            )
            return

        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        # Limit tekshiruvi
        if not await can_use_code(session, user, DAILY_LIMIT):
            vip_status = await is_vip(session, user)
            if not vip_status:
                await message.answer(
                    f"⏳ Bugungi {DAILY_LIMIT} ta kunlik limitdan foydalandingiz.\n"
                    "Ertaga yana urinib ko'ring yoki <b>VIP</b> bo'ling — "
                    "VIP foydalanuvchilar uchun limit yo'q! 👑\n\n"
                    "VIP bo'lish uchun: /start → 💰 VIP bo'lish"
                )
                return

        movie = await get_movie_by_code(session, code)
        if movie is None:
            await message.answer("❌ Bunday kod topilmadi yoki kino o'chirib tashlangan.")
            return

        # Premium kino tekshiruvi
        if movie.is_premium and not await is_vip(session, user):
            await message.answer(
                "🔒 Bu kino faqat <b>VIP</b> foydalanuvchilar uchun.\n\n"
                "VIP bo'lish uchun: /start → 💰 VIP bo'lish"
            )
            return

        await register_code_usage(session, user, movie)
        await session.commit()

    await message.answer(
        f"✅ Kod tasdiqlandi!\n\n"
        f"🎬 <b>{movie.title}</b>\n\n"
        f"🔗 Kino ssilkasi:\n{movie.channel_post_link}"
    )
