from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ───────────────────────── USER MENU ─────────────────────────

def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎬 Kino kodi kiritish", callback_data="menu:enter_code")
    )
    builder.row(
        InlineKeyboardButton(text="💰 VIP bo'lish", callback_data="menu:vip")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Statistika", callback_data="menu:stats")
    )
    return builder.as_markup()


def vip_tariffs_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 20 kun — 20 000 so'm", callback_data="vip:plan:20"),
    )
    builder.row(
        InlineKeyboardButton(text="📅 30 kun — 30 000 so'm", callback_data="vip:plan:30"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu:back")
    )
    return builder.as_markup()


def subscribe_keyboard(channels: list[str]) -> InlineKeyboardMarkup:
    """Obuna bo'lmagan kanallar ro'yxati."""
    builder = InlineKeyboardBuilder()
    for i, link in enumerate(channels, start=1):
        # Link https:// bilan boshlansa, URL sifatida ishlatamiz
        if link.startswith("https://") or link.startswith("http://"):
            builder.row(
                InlineKeyboardButton(text=f"📢 {i}-kanal", url=link)
            )
        else:
            # @username → t.me/username
            username = link.lstrip("@")
            builder.row(
                InlineKeyboardButton(text=f"📢 {i}-kanal", url=f"https://t.me/{username}")
            )
    builder.row(
        InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_sub")
    )
    return builder.as_markup()


# ───────────────────────── ADMIN MENU ─────────────────────────

def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📈 Statistika", callback_data="admin:stats")
    )
    builder.row(
        InlineKeyboardButton(text="🎬 Kino qo'shish", callback_data="admin:add_movie"),
        InlineKeyboardButton(text="🗑 Kino o'chirish", callback_data="admin:delete_movie"),
    )
    builder.row(
        InlineKeyboardButton(text="🎞 Kinolar ro'yxati", callback_data="admin:list_movies"),
    )
    builder.row(
        InlineKeyboardButton(text="📢 Kanallar", callback_data="admin:channels"),
        InlineKeyboardButton(text="👑 VIP foydalanuvchilar", callback_data="admin:vip_users"),
    )
    builder.row(
        InlineKeyboardButton(text="👥 Adminlar", callback_data="admin:admins"),
        InlineKeyboardButton(text="📣 Broadcast", callback_data="admin:broadcast"),
    )
    return builder.as_markup()


def vip_payment_method_keyboard(days: int) -> InlineKeyboardMarkup:
    """To'lov usulini tanlash."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Payme", callback_data=f"pay:payme:{days}"),
        InlineKeyboardButton(text="💳 Click", callback_data=f"pay:click:{days}"),
    )
    builder.row(
        InlineKeyboardButton(text="📸 Qo'lda (skrinshot)", callback_data=f"pay:manual:{days}"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu:vip")
    )
    return builder.as_markup()


def admin_channels_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="admin:add_channel")
    )
    builder.row(
        InlineKeyboardButton(text="🗑 Kanal o'chirish", callback_data="admin:del_channel")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Kanallar ro'yxati", callback_data="admin:list_channels")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Admin menyu", callback_data="admin:back")
    )
    return builder.as_markup()


def payment_approve_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Tasdiqlash", callback_data=f"payment:approve:{payment_id}"
        ),
        InlineKeyboardButton(
            text="❌ Rad etish", callback_data=f"payment:reject:{payment_id}"
        ),
    )
    return builder.as_markup()
