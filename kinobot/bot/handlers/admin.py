import asyncio
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot import keyboards
from bot.config import settings
from bot.db import AsyncSessionMaker
from bot.db.models import Movie, Payment, RequiredChannel, User
from bot.services.admin_mgmt import (
    add_admin, is_admin, is_super_admin, list_admins, remove_admin,
)
from bot.services.stats import (
    get_all_user_ids, get_basic_stats, get_latest_vip_users, get_movie_stats,
)
from bot.services.vip import get_payment_by_id, set_vip

logger = logging.getLogger(__name__)
router = Router()


# ─────── FSM STATES ───────
class AdminMovieStates(StatesGroup):
    waiting_edit_field = State()
    waiting_edit_value = State()

class AdminChannelStates(StatesGroup):
    waiting_channel_id = State()
    waiting_channel_title = State()
    waiting_channel_link = State()
    waiting_del_id = State()

class BroadcastStates(StatesGroup):
    waiting_message = State()
    confirm = State()

class AdminMgmtStates(StatesGroup):
    waiting_add_id = State()
    waiting_del_id = State()


# ─────── ENTRY ───────
@router.message(F.text == "/admin")
async def cmd_admin(message: Message) -> None:
    async with AsyncSessionMaker() as session:
        ok = await is_admin(session, message.from_user.id)
    if not ok:
        await message.answer("⛔ Bu bo'lim faqat adminlar uchun.")
        return
    await message.answer(
        "🛠 <b>Admin paneli</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=keyboards.admin_menu_keyboard(),
    )

@router.callback_query(F.data == "admin:back")
async def cb_admin_back(callback: CallbackQuery) -> None:
    async with AsyncSessionMaker() as session:
        ok = await is_admin(session, callback.from_user.id)
    if not ok:
        await callback.answer("Siz admin emassiz.", show_alert=True)
        return
    await callback.message.edit_text(
        "🛠 <b>Admin paneli</b>", reply_markup=keyboards.admin_menu_keyboard()
    )
    await callback.answer()


# ─────── STATISTICS ───────
@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
        stats = await get_basic_stats(session)
    text = (
        "📈 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b>\n"
        f"   ├ Bugun: +{stats['joined_24h']}\n"
        f"   ├ 7 kun: +{stats['joined_7d']}\n"
        f"   └ 30 kun: +{stats['joined_30d']}\n\n"
        f"🟢 So'nggi 24 soatda faol: <b>{stats['active_24h']}</b>\n\n"
        f"🎬 Aktiv kinolar: <b>{stats['active_movies']}</b> (premium: {stats['premium_movies']})\n\n"
        f"🔢 Jami kod ishlatilishi: <b>{stats['total_code_usages']}</b>\n"
        f"   └ Bugun: {stats['today_code_usages']}\n\n"
        f"👑 Aktiv VIP: <b>{stats['active_vip_users']}</b>"
    )
    await callback.message.answer(text)
    await callback.answer()


# ─────── MOVIE STATS ───────
@router.message(F.text == "/moviestats")
async def cmd_movie_stats(message: Message) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, message.from_user.id):
            return
        rows = await get_movie_stats(session, limit=20)
    if not rows:
        await message.answer("📊 Hali kino yuklanishlari yo'q.")
        return
    lines = ["📊 <b>Kino yuklanish statistikasi (top 20):</b>\n"]
    for i, r in enumerate(rows, 1):
        ptype = "🔒" if r["is_premium"] else "🆓"
        lines.append(f"{i}. {ptype} <code>{r['code']}</code> — {r['title']}\n   👁 {r['total']} marta")
    await message.answer("\n".join(lines))


# ─────── MOVIES ───────
@router.callback_query(F.data == "admin:add_movie")
async def cb_admin_add_movie_info(callback: CallbackQuery) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
    await callback.message.answer(
        "➕ <b>Kino qo'shish</b>\n\n"
        "<code>/addmovie KOD | Nomi | https://t.me/...</code>\n\n"
        "Premium kino:\n<code>/addmovie KOD | Nomi | https://t.me/... | premium</code>"
    )
    await callback.answer()

@router.message(F.text.startswith("/addmovie"))
async def cmd_add_movie(message: Message) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, message.from_user.id):
            return
    try:
        _, rest = message.text.split(" ", 1)
        parts = [p.strip() for p in rest.split("|")]
        code, title, link = parts[0], parts[1], parts[2]
        is_premium = len(parts) > 3 and parts[3].lower() == "premium"
    except (ValueError, IndexError):
        await message.answer("❌ Format:\n<code>/addmovie KOD | Nomi | https://t.me/...</code>")
        return
    async with AsyncSessionMaker() as session:
        result = await session.execute(select(Movie).where(Movie.code == code))
        movie = result.scalar_one_or_none()
        if movie:
            movie.title = title
            movie.channel_post_link = link
            movie.is_active = True
            movie.is_premium = is_premium
        else:
            movie = Movie(code=code, title=title, channel_post_link=link, is_active=True, is_premium=is_premium)
            session.add(movie)
        await session.commit()
    ptype = "🔒 Premium" if is_premium else "🆓 Bepul"
    await message.answer(f"✅ Kino saqlandi!\nKod: <code>{code}</code> | {ptype}")

@router.callback_query(F.data == "admin:delete_movie")
async def cb_admin_delete_movie_info(callback: CallbackQuery) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
    await callback.message.answer("🗑 O'chirish:\n<code>/delmovie KOD</code>")
    await callback.answer()

@router.message(F.text.startswith("/delmovie"))
async def cmd_del_movie(message: Message) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, message.from_user.id):
            return
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Format: <code>/delmovie KOD</code>")
        return
    code = parts[1].strip()
    async with AsyncSessionMaker() as session:
        result = await session.execute(select(Movie).where(Movie.code == code))
        movie = result.scalar_one_or_none()
        if not movie:
            await message.answer("❌ Kino topilmadi.")
            return
        movie.is_active = False
        await session.commit()
    await message.answer(f"✅ <code>{code}</code> o'chirildi.")

@router.callback_query(F.data == "admin:list_movies")
async def cb_admin_list_movies(callback: CallbackQuery) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
        result = await session.execute(
            select(Movie).where(Movie.is_active.is_(True)).order_by(Movie.created_at.desc()).limit(30)
        )
        movies = result.scalars().all()
    if not movies:
        await callback.message.answer("🎬 Aktiv kinolar yo'q.")
        await callback.answer()
        return
    lines = ["🎬 <b>Aktiv kinolar (so'nggi 30):</b>\n"]
    for m in movies:
        ptype = "🔒" if m.is_premium else "🆓"
        lines.append(f"{ptype} <code>{m.code}</code> — {m.title}")
    await callback.message.answer("\n".join(lines))
    await callback.answer()


# ─────── KINO TAHRIRLASH ───────
@router.message(F.text.startswith("/editmovie"))
async def cmd_edit_movie(message: Message, state: FSMContext) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, message.from_user.id):
            return
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Format: <code>/editmovie KOD</code>")
        return
    code = parts[1].strip()
    async with AsyncSessionMaker() as session:
        result = await session.execute(select(Movie).where(Movie.code == code))
        movie = result.scalar_one_or_none()
    if not movie:
        await message.answer(f"❌ <code>{code}</code> topilmadi.")
        return
    await state.set_state(AdminMovieStates.waiting_edit_field)
    await state.update_data(movie_code=code)
    ptype = "🔒 Premium" if movie.is_premium else "🆓 Bepul"
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📝 Nomini o'zgartirish", callback_data="edit:title"))
    kb.row(InlineKeyboardButton(text="🔗 Ssilkani o'zgartirish", callback_data="edit:link"))
    kb.row(InlineKeyboardButton(text="🏷 Kodni o'zgartirish", callback_data="edit:code"))
    kb.row(InlineKeyboardButton(text="🔄 Premium/Bepul almashtirish", callback_data="edit:premium"))
    kb.row(InlineKeyboardButton(text="❌ Bekor", callback_data="edit:cancel"))
    await message.answer(
        f"🎬 <b>{movie.title}</b>\nKod: <code>{movie.code}</code> | {ptype}\n\nNimani o'zgartirmoqchisiz?",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data.startswith("edit:"), AdminMovieStates.waiting_edit_field)
async def cb_edit_field(callback: CallbackQuery, state: FSMContext) -> None:
    field = callback.data.split(":")[1]
    if field == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Tahrirlash bekor qilindi.")
        await callback.answer()
        return
    if field == "premium":
        data = await state.get_data()
        code = data["movie_code"]
        async with AsyncSessionMaker() as session:
            result = await session.execute(select(Movie).where(Movie.code == code))
            movie = result.scalar_one_or_none()
            if movie:
                movie.is_premium = not movie.is_premium
                new_type = "🔒 Premium" if movie.is_premium else "🆓 Bepul"
                await session.commit()
                await callback.message.edit_text(f"✅ Kino turi: {new_type}")
        await state.clear()
        await callback.answer()
        return
    field_labels = {"title": "yangi nomini", "link": "yangi ssilkani", "code": "yangi kodini"}
    await state.update_data(edit_field=field)
    await state.set_state(AdminMovieStates.waiting_edit_value)
    await callback.message.answer(f"✏️ Kinoning {field_labels.get(field, field)}ni yuboring:\n\n/cancel")
    await callback.answer()

@router.message(AdminMovieStates.waiting_edit_value)
async def fsm_edit_value(message: Message, state: FSMContext) -> None:
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.")
    data = await state.get_data()
    code = data["movie_code"]
    field = data["edit_field"]
    new_value = message.text.strip()
    async with AsyncSessionMaker() as session:
        result = await session.execute(select(Movie).where(Movie.code == code))
        movie = result.scalar_one_or_none()
        if not movie:
            await message.answer("❌ Kino topilmadi.")
            await state.clear()
            return
        if field == "title":
            movie.title = new_value
        elif field == "link":
            movie.channel_post_link = new_value
        elif field == "code":
            existing = await session.execute(select(Movie).where(Movie.code == new_value))
            if existing.scalar_one_or_none():
                await message.answer(f"❌ <code>{new_value}</code> kodi allaqachon mavjud.")
                await state.clear()
                return
            movie.code = new_value
        await session.commit()
    await message.answer("✅ Kino yangilandi!")
    await state.clear()


# ─────── CHANNELS ───────
@router.callback_query(F.data == "admin:channels")
async def cb_admin_channels(callback: CallbackQuery) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
    await callback.message.answer("📢 <b>Majburiy obuna kanallari</b>", reply_markup=keyboards.admin_channels_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin:add_channel")
async def cb_admin_add_channel(callback: CallbackQuery, state: FSMContext) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
    await state.set_state(AdminChannelStates.waiting_channel_id)
    await callback.message.answer("📢 Kanal ID:\n• <code>@kanalusername</code>\n• <code>-1001234567890</code>\n\n/cancel")
    await callback.answer()

@router.message(AdminChannelStates.waiting_channel_id)
async def fsm_channel_id(message: Message, state: FSMContext) -> None:
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.")
    await state.update_data(channel_id=message.text.strip())
    await state.set_state(AdminChannelStates.waiting_channel_title)
    await message.answer("Kanal nomini kiriting:")

@router.message(AdminChannelStates.waiting_channel_title)
async def fsm_channel_title(message: Message, state: FSMContext) -> None:
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.")
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminChannelStates.waiting_channel_link)
    await message.answer("Taklif havolasi (yo'q bo'lsa <code>-</code>):\n\n/cancel")

@router.message(AdminChannelStates.waiting_channel_link)
async def fsm_channel_link(message: Message, state: FSMContext) -> None:
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.")
    data = await state.get_data()
    invite_link = None if message.text.strip() == "-" else message.text.strip()
    async with AsyncSessionMaker() as session:
        existing = await session.execute(select(RequiredChannel).where(RequiredChannel.channel_id == data["channel_id"]))
        ch = existing.scalar_one_or_none()
        if ch:
            ch.title = data["title"]
            ch.invite_link = invite_link
            ch.is_active = True
        else:
            session.add(RequiredChannel(channel_id=data["channel_id"], title=data["title"], invite_link=invite_link, is_active=True))
        await session.commit()
    await state.clear()
    await message.answer(f"✅ Kanal qo'shildi: <b>{data['title']}</b>")

@router.callback_query(F.data == "admin:list_channels")
async def cb_admin_list_channels(callback: CallbackQuery) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
        result = await session.execute(select(RequiredChannel).where(RequiredChannel.is_active.is_(True)))
        channels = result.scalars().all()
    if not channels:
        await callback.message.answer("📢 Majburiy kanal yo'q.")
        await callback.answer()
        return
    lines = ["📢 <b>Majburiy kanallar:</b>\n"]
    for i, ch in enumerate(channels, 1):
        link = ch.invite_link or ch.channel_id
        lines.append(f"{i}. <b>{ch.title}</b>\n   ID: <code>{ch.channel_id}</code>\n   🔗 {link}")
    await callback.message.answer("\n".join(lines))
    await callback.answer()

@router.callback_query(F.data == "admin:del_channel")
async def cb_admin_del_channel(callback: CallbackQuery, state: FSMContext) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
    await state.set_state(AdminChannelStates.waiting_del_id)
    await callback.message.answer("🗑 Kanal ID (masalan: <code>@kanalim</code>):\n\n/cancel")
    await callback.answer()

@router.message(AdminChannelStates.waiting_del_id)
async def fsm_del_channel(message: Message, state: FSMContext) -> None:
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.")
    channel_id = message.text.strip()
    async with AsyncSessionMaker() as session:
        result = await session.execute(select(RequiredChannel).where(RequiredChannel.channel_id == channel_id))
        ch = result.scalar_one_or_none()
        if not ch:
            await message.answer(f"❌ <code>{channel_id}</code> topilmadi.")
        else:
            ch.is_active = False
            await session.commit()
            await message.answer(f"✅ <code>{channel_id}</code> o'chirildi.")
    await state.clear()


# ─────── ADMIN MANAGEMENT ───────
@router.callback_query(F.data == "admin:admins")
async def cb_admin_admins(callback: CallbackQuery) -> None:
    if not is_super_admin(callback.from_user.id):
        await callback.answer("Faqat super-admin.", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin:add_admin"))
    kb.row(InlineKeyboardButton(text="🗑 Admin o'chirish", callback_data="admin:del_admin"))
    kb.row(InlineKeyboardButton(text="📋 Adminlar ro'yxati", callback_data="admin:list_admins"))
    kb.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:back"))
    await callback.message.answer("👥 <b>Adminlar boshqaruvi</b>", reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(F.data == "admin:list_admins")
async def cb_list_admins(callback: CallbackQuery) -> None:
    if not is_super_admin(callback.from_user.id):
        await callback.answer("Faqat super-admin.", show_alert=True)
        return
    async with AsyncSessionMaker() as session:
        admins = await list_admins(session)
    lines = ["👥 <b>Adminlar ro'yxati:</b>\n", "🌟 <b>Super-adminlar (.env):</b>"]
    for uid in settings.admin_ids:
        lines.append(f"  • <code>{uid}</code>")
    if admins:
        lines.append("\n🤖 <b>Bot orqali qo'shilgan:</b>")
        for a in admins:
            line = f"  • <code>{a.telegram_id}</code>"
            if a.username:
                line += f" (@{a.username})"
            lines.append(line)
    else:
        lines.append("\nBot orqali admin yo'q.")
    await callback.message.answer("\n".join(lines))
    await callback.answer()

@router.callback_query(F.data == "admin:add_admin")
async def cb_add_admin(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_super_admin(callback.from_user.id):
        await callback.answer("Faqat super-admin.", show_alert=True)
        return
    await state.set_state(AdminMgmtStates.waiting_add_id)
    await callback.message.answer("➕ Yangi admin Telegram ID sini yuboring:\n\n/cancel")
    await callback.answer()

@router.message(AdminMgmtStates.waiting_add_id)
async def fsm_add_admin(message: Message, state: FSMContext) -> None:
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.")
    try:
        new_id = int(message.text.strip())
    except ValueError:
        return await message.answer("❌ ID raqam bo'lishi kerak.")
    async with AsyncSessionMaker() as session:
        success, msg = await add_admin(session, new_id, None, message.from_user.id)
    await message.answer(msg)
    await state.clear()

@router.callback_query(F.data == "admin:del_admin")
async def cb_del_admin(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_super_admin(callback.from_user.id):
        await callback.answer("Faqat super-admin.", show_alert=True)
        return
    await state.set_state(AdminMgmtStates.waiting_del_id)
    await callback.message.answer("🗑 O'chirish uchun admin ID:\n\n/cancel")
    await callback.answer()

@router.message(AdminMgmtStates.waiting_del_id)
async def fsm_del_admin(message: Message, state: FSMContext) -> None:
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.")
    try:
        del_id = int(message.text.strip())
    except ValueError:
        return await message.answer("❌ ID raqam bo'lishi kerak.")
    async with AsyncSessionMaker() as session:
        success, msg = await remove_admin(session, del_id)
    await message.answer(msg)
    await state.clear()


# ─────── VIP USERS ───────
@router.callback_query(F.data == "admin:vip_users")
async def cb_admin_vip_users(callback: CallbackQuery) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
        users = await get_latest_vip_users(session)
    if not users:
        await callback.message.answer("👑 Aktiv VIP foydalanuvchilar yo'q.")
        await callback.answer()
        return
    lines = ["👑 <b>VIP foydalanuvchilar:</b>\n"]
    for u in users:
        line = f"• <code>{u.telegram_id}</code>"
        if u.username:
            line += f" (@{u.username})"
        if u.vip_until:
            line += f" — {u.vip_until.strftime('%d.%m.%Y')}"
        lines.append(line)
    await callback.message.answer("\n".join(lines))
    await callback.answer()

@router.message(F.text.startswith("/givevip"))
async def cmd_give_vip(message: Message) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, message.from_user.id):
            return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Format: <code>/givevip TELEGRAM_ID KUNLAR</code>")
        return
    try:
        target_id, days = int(parts[1]), int(parts[2])
    except ValueError:
        return await message.answer("❌ ID va kunlar son bo'lishi kerak.")
    async with AsyncSessionMaker() as session:
        result = await session.execute(select(User).where(User.telegram_id == target_id))
        user = result.scalar_one_or_none()
        if not user:
            return await message.answer(f"❌ ID {target_id} topilmadi.")
        await set_vip(session, user, days)
        await session.commit()
    await message.answer(f"✅ {target_id} ga {days} kunlik VIP berildi.")
    try:
        await message.bot.send_message(target_id, f"🎉 Sizga <b>{days} kunlik VIP</b> berildi! 👑")
    except Exception:
        pass


# ─────── BROADCAST ───────
@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
    await state.set_state(BroadcastStates.waiting_message)
    await callback.message.answer("📣 <b>Broadcast</b>\n\nBarcha foydalanuvchilarga yubormoqchi bo'lgan xabarni yuboring.\n\n/cancel")
    await callback.answer()

@router.message(BroadcastStates.waiting_message)
async def fsm_broadcast_msg(message: Message, state: FSMContext) -> None:
    if message.text == "/cancel":
        await state.clear()
        return await message.answer("❌ Bekor qilindi.")
    await state.update_data(msg_id=message.message_id, chat_id=message.chat.id)
    await state.set_state(BroadcastStates.confirm)
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast:confirm"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="broadcast:cancel"),
    )
    await message.answer("Yuqoridagi xabar barcha foydalanuvchilarga yuborilsinmi?", reply_markup=kb.as_markup())

@router.callback_query(F.data == "broadcast:cancel")
async def cb_broadcast_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Broadcast bekor qilindi.")
    await callback.answer()

@router.callback_query(F.data == "broadcast:confirm")
async def cb_broadcast_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
    data = await state.get_data()
    await state.clear()
    source_chat_id = data.get("chat_id")
    source_msg_id = data.get("msg_id")
    async with AsyncSessionMaker() as session:
        user_ids = await get_all_user_ids(session)
    total = len(user_ids)
    success = 0
    failed = 0
    status_msg = await callback.message.answer(f"📣 Broadcast boshlandi...\n👥 Jami: {total}")
    for uid in user_ids:
        try:
            await callback.bot.forward_message(chat_id=uid, from_chat_id=source_chat_id, message_id=source_msg_id)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await status_msg.edit_text(
        f"✅ <b>Broadcast tugadi!</b>\n\n👥 Jami: {total}\n✅ Yuborildi: {success}\n❌ Blok: {failed}"
    )
    await callback.answer()


# ─────── PAYMENT APPROVAL ───────
@router.callback_query(F.data.startswith("payment:"))
async def cb_payment_action(callback: CallbackQuery) -> None:
    async with AsyncSessionMaker() as session:
        if not await is_admin(session, callback.from_user.id):
            await callback.answer("Siz admin emassiz.", show_alert=True)
            return
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Noto'g'ri format.", show_alert=True)
        return
    action = parts[1]
    try:
        payment_id = int(parts[2])
    except ValueError:
        await callback.answer("Noto'g'ri ID.", show_alert=True)
        return
    async with AsyncSessionMaker() as session:
        payment = await get_payment_by_id(session, payment_id)
        if not payment:
            await callback.answer("To'lov topilmadi.", show_alert=True)
            return
        if payment.status != "pending":
            await callback.answer(f"Bu to'lov allaqachon: {payment.status}", show_alert=True)
            return
        result = await session.execute(select(User).where(User.id == payment.user_id))
        user = result.scalar_one_or_none()
        if not user:
            await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
            return
        if action == "approve":
            payment.status = "approved"
            await set_vip(session, user, payment.days)
            await session.commit()
            try:
                await callback.bot.send_message(user.telegram_id, f"🎉 <b>VIP faollashtirildi!</b>\n📅 {payment.days} kun 👑")
            except Exception:
                pass
            try:
                await callback.message.edit_caption((callback.message.caption or "") + "\n\n✅ Tasdiqlandi.")
            except Exception:
                pass
            await callback.answer("✅ Tasdiqlandi.")
        elif action == "reject":
            payment.status = "rejected"
            await session.commit()
            try:
                await callback.bot.send_message(user.telegram_id, "❌ VIP to'lovingiz rad etildi.")
            except Exception:
                pass
            try:
                await callback.message.edit_caption((callback.message.caption or "") + "\n\n❌ Rad etildi.")
            except Exception:
                pass
            await callback.answer("❌ Rad etildi.")
        else:
            await callback.answer("Noto'g'ri amal.", show_alert=True)


# ─────── CANCEL ───────
@router.message(F.text == "/cancel")
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state():
        await state.clear()
        await message.answer("❌ Amal bekor qilindi.")
