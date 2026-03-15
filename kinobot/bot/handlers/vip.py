from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot import keyboards
from bot.config import settings
from bot.db import AsyncSessionMaker
from bot.db.models import Payment, User
from bot.services.codes import get_or_create_user

router = Router()

class VipStates(StatesGroup):
    waiting_screenshot = State()

TARIFFS: dict[int, int] = {
    20: 20_000 * 100,   # tiyin (20 000 so'm)
    30: 30_000 * 100,   # tiyin (30 000 so'm)
}
TARIFF_LABELS: dict[int, str] = {
    20: "20 000 so'm",
    30: "30 000 so'm",
}

PAYMENT_CARD = "8600 XXXX XXXX XXXX"    # O'ZINGIZNING KARTANGIZ
PAYMENT_NAME = "Ism Familiya"           # TO'LIQ ISMINGIZ


@router.callback_query(F.data.startswith("vip:plan:"))
async def cb_vip_plan(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    try:
        days = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer("Noto'g'ri tarif.", show_alert=True)
        return
    if days not in TARIFFS:
        await callback.answer("Bu tarif mavjud emas.", show_alert=True)
        return

    text = (
        f"💰 <b>VIP — {days} kun</b>\n"
        f"To'lov summasi: <b>{TARIFF_LABELS[days]}</b>\n\n"
        "To'lov usulini tanlang:"
    )
    await callback.message.answer(text, reply_markup=keyboards.vip_payment_method_keyboard(days))
    await callback.answer()


# ─────── PAYME ───────
@router.callback_query(F.data.startswith("pay:payme:"))
async def cb_pay_payme(callback: CallbackQuery) -> None:
    days = int(callback.data.split(":")[2])
    amount_tiyin = TARIFFS[days]
    amount_som = amount_tiyin // 100

    async with AsyncSessionMaker() as session:
        user: User = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )
        payment = Payment(
            user_id=user.id,
            amount=amount_tiyin,
            days=days,
            method="payme",
            status="pending",
        )
        session.add(payment)
        await session.flush()
        payment_id = payment.id
        await session.commit()

    merchant_id = settings.payme_merchant_id
    if not merchant_id:
        await callback.message.answer("⚠️ Payme hali sozlanmagan. Qo'lda to'lov usulidan foydalaning.")
        await callback.answer()
        return

    import base64, json
    params = {
        "m": merchant_id,
        "ac.order_id": str(payment_id),
        "a": amount_tiyin,
        "l": "uz",
    }
    encoded = base64.b64encode(json.dumps(params).encode()).decode()
    pay_url = f"https://checkout.paycom.uz/{encoded}"

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="💳 Payme orqali to'lash", url=pay_url))

    await callback.message.answer(
        f"💳 <b>Payme to'lov</b>\n\n"
        f"Summa: <b>{amount_som:,} so'm</b>\n"
        f"Buyurtma: #{payment_id}\n\n"
        "Quyidagi tugmani bosib to'lovni amalga oshiring.\n"
        "To'lovdan so'ng avtomatik faollashadi.",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


# ─────── CLICK ───────
@router.callback_query(F.data.startswith("pay:click:"))
async def cb_pay_click(callback: CallbackQuery) -> None:
    days = int(callback.data.split(":")[2])
    amount_tiyin = TARIFFS[days]
    amount_som = amount_tiyin // 100

    async with AsyncSessionMaker() as session:
        user: User = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )
        payment = Payment(
            user_id=user.id,
            amount=amount_tiyin,
            days=days,
            method="click",
            status="pending",
        )
        session.add(payment)
        await session.flush()
        payment_id = payment.id
        await session.commit()

    service_id = settings.click_service_id
    merchant_id = settings.click_merchant_id
    if not service_id or not merchant_id:
        await callback.message.answer("⚠️ Click hali sozlanmagan. Qo'lda to'lov usulidan foydalaning.")
        await callback.answer()
        return

    pay_url = (
        f"https://my.click.uz/services/pay"
        f"?service_id={service_id}"
        f"&merchant_id={merchant_id}"
        f"&amount={amount_som}"
        f"&transaction_param={payment_id}"
        f"&return_url=https://t.me/{(await callback.bot.get_me()).username}"
    )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="💳 Click orqali to'lash", url=pay_url))

    await callback.message.answer(
        f"💳 <b>Click to'lov</b>\n\n"
        f"Summa: <b>{amount_som:,} so'm</b>\n"
        f"Buyurtma: #{payment_id}\n\n"
        "Quyidagi tugmani bosib to'lovni amalga oshiring.\n"
        "To'lovdan so'ng avtomatik faollashadi.",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


# ─────── QO'LDA (SKRINSHOT) ───────
@router.callback_query(F.data.startswith("pay:manual:"))
async def cb_pay_manual(callback: CallbackQuery, state: FSMContext) -> None:
    days = int(callback.data.split(":")[2])
    amount_tiyin = TARIFFS[days]
    amount_som = amount_tiyin // 100

    await state.set_state(VipStates.waiting_screenshot)
    await state.update_data(days=days, amount=amount_tiyin)

    await callback.message.answer(
        f"📸 <b>Qo'lda to'lov — {days} kun</b>\n\n"
        f"To'lov summasi: <b>{amount_som:,} so'm</b>\n\n"
        f"Karta raqami:\n<code>{PAYMENT_CARD}</code>\n"
        f"Egasi: {PAYMENT_NAME}\n\n"
        "To'lovni amalga oshirgandan so'ng <b>chek skrinshotini rasm sifatida</b> yuboring.\n\n"
        "⏱ Admin tekshirib, VIP ni faollashtiradi."
    )
    await callback.answer()


@router.message(VipStates.waiting_screenshot, F.photo)
async def handle_vip_screenshot(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    days: int = data.get("days", 0)
    amount: int = data.get("amount", 0)

    if not days or not amount:
        await message.answer("❌ Tarif topilmadi. /start → 💰 VIP bo'lish")
        await state.clear()
        return

    async with AsyncSessionMaker() as session:
        user: User = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        payment = Payment(user_id=user.id, amount=amount, days=days, method="manual", status="pending")
        session.add(payment)
        await session.flush()
        payment_id = payment.id
        await session.commit()

    caption = (
        f"💳 <b>Yangi VIP to'lov #{payment_id}</b>\n\n"
        f"👤 @{message.from_user.username or '—'}\n"
        f"🆔 <code>{message.from_user.id}</code>\n"
        f"📅 Tarif: {days} kun\n"
        f"💰 Summa: {amount // 100:,} so'm"
    )
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"payment:approve:{payment_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"payment:reject:{payment_id}"),
    )

    sent = 0
    for admin_id in settings.admin_ids:
        try:
            await message.bot.send_photo(
                chat_id=admin_id,
                photo=message.photo[-1].file_id,
                caption=caption,
                reply_markup=kb.as_markup(),
            )
            sent += 1
        except Exception:
            continue

    if sent > 0:
        await message.answer("✅ Chek adminlarga yuborildi. Tasdiqlashni kuting (1–24 soat).")
    else:
        await message.answer("⚠️ Admin topilmadi. Bot egasi bilan bog'laning.")
    await state.clear()


@router.message(VipStates.waiting_screenshot)
async def handle_vip_wrong_input(message: Message) -> None:
    await message.answer("📸 Iltimos, to'lov chekini <b>rasm (foto)</b> sifatida yuboring.")
