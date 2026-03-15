from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot import keyboards
from bot.config import settings
from bot.db import AsyncSessionMaker
from bot.services.subscription import check_subscription

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message) -> None:
    text = (
        "🎬 <b>Kino Botga xush kelibsiz!</b>\n\n"
        "Bu bot orqali kino kodini kiritib, kino ssilkasini olishingiz mumkin.\n"
        "VIP rejimda esa cheksiz kinolardan bahramand bo'ling! 👑\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=keyboards.main_menu_keyboard())


@router.callback_query(F.data == "menu:back")
async def cb_back_to_menu(callback: CallbackQuery) -> None:
    text = (
        "🎬 <b>Asosiy menyu</b>\n\n"
        "Kerakli bo'limni tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=keyboards.main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:enter_code")
async def cb_enter_code(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "🎬 Kino kodini kiriting (masalan: <code>151</code>).\n\n"
        "Kod bot bilan suhbatga yuboring."
    )
    await callback.answer()


@router.callback_query(F.data == "menu:vip")
async def cb_vip(callback: CallbackQuery) -> None:
    text = (
        "👑 <b>VIP rejim</b>\n\n"
        "VIP foydalanuvchilar uchun:\n"
        "✅ Cheksiz kino kodi ishlatish\n"
        "✅ Premium kinolarga kirish\n"
        "✅ Ustunlik xizmat\n\n"
        "Quyidagi tariflardan birini tanlang:"
    )
    await callback.message.answer(text, reply_markup=keyboards.vip_tariffs_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu:stats")
async def cb_stats_placeholder(callback: CallbackQuery) -> None:
    if callback.from_user.id not in settings.admin_ids:
        await callback.answer("Bu bo'lim faqat adminlar uchun.", show_alert=True)
        return

    await callback.message.answer(
        "Admin paneliga kirish uchun /admin komandasini yuboring."
    )
    await callback.answer()


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(callback: CallbackQuery) -> None:
    """Foydalanuvchi 'Obuna bo'ldim' tugmasini bosganida tekshirish."""
    async with AsyncSessionMaker() as session:
        is_member, not_subscribed = await check_subscription(
            callback.bot, callback.from_user.id, session
        )

    if is_member:
        await callback.message.edit_text(
            "✅ Obuna tasdiqlandi! Endi kino kodini yuboring."
        )
    else:
        await callback.answer(
            "❌ Siz hali barcha kanallarga obuna bo'lmadingiz!",
            show_alert=True,
        )
    await callback.answer()
