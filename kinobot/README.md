# 🎬 Telegram Kino Bot

Python + aiogram 3 asosida yozilgan Telegram bot.  
Kino kodlari, majburiy obuna tekshiruvi, VIP premium rejim va to'liq admin panel bilan.

---

## 📁 Loyiha tuzilmasi

```
kinobot/
├── bot/
│   ├── __init__.py
│   ├── config.py
│   ├── keyboards.py
│   ├── main.py
│   ├── db/
│   │   ├── __init__.py        ← engine, session, init_db
│   │   └── models.py          ← User, Movie, CodeUsage, Payment, RequiredChannel
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── admin.py           ← admin panel, broadcast, kanallar
│   │   ├── codes.py           ← kino kodi yuborish
│   │   ├── user_menu.py       ← /start, menyu
│   │   └── vip.py             ← VIP to'lov oqimi
│   └── services/
│       ├── __init__.py
│       ├── codes.py           ← DB so'rovlar (movie, user)
│       ├── limits.py          ← kunlik limit tekshiruvi
│       ├── stats.py           ← statistika
│       ├── subscription.py    ← obuna tekshiruvi (DB kaналлар)
│       └── vip.py             ← VIP boshqaruv
├── .env.example
├── .gitignore
├── render.yaml
└── requirements.txt
```

---

## ⚙️ Boshlash (lokal)

### 1. Talablar
- Python 3.10+
- pip

### 2. Virtual muhit
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 3. Kutubxonalar
```bash
pip install -r requirements.txt
```

### 4. `.env` fayl
`.env.example` nusxasini `.env` nomi bilan saqlang va to'ldiring:
```
BOT_TOKEN=7xxxxxxxxx:AAH...       ← @BotFather dan oling
ADMIN_IDS=123456789               ← Telegram ID (vergul bilan bir nechtasi: 111,222)
REQUIRED_CHANNEL=@kanalingiz      ← Ixtiyoriy; DB orqali ham qo'shish mumkin
DB_URL=sqlite+aiosqlite:///./bot.db
```

### 5. Ishga tushirish
```bash
python -m bot.main
```

---

## 🚀 GitHub + Render deploy

### GitHub

```bash
git init
git add .
git commit -m "init: kino bot"
git branch -M main
git remote add origin https://github.com/SIZNING_USERNAME/kinobot.git
git push -u origin main
```

### Render.com

1. [render.com](https://render.com) ga kiring → **New → Background Worker**
2. GitHub repongizni tanlang
3. Quyidagilarni to'ldiring:

| Maydon | Qiymat |
|---|---|
| Environment | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python -m bot.main` |

4. **Environment Variables** bo'limida quyidagilarni qo'shing:

| Kalit | Qiymat |
|---|---|
| `BOT_TOKEN` | BotFather dan olgan token |
| `ADMIN_IDS` | Telegram ID (masalan: `123456789`) |
| `REQUIRED_CHANNEL` | `@kanalingiz` yoki bo'sh qoldiring |
| `DB_URL` | `sqlite+aiosqlite:///./bot.db` (yoki PostgreSQL URL) |

> ⚠️ **Render bepul plani** — disk saqlanmaydi. SQLite ma'lumotlari qayta deploy da o'chadi.  
> Doimiy saqlash uchun **Render PostgreSQL** yoki **Railway** bepul DB dan foydalaning:  
> `DB_URL=postgresql+asyncpg://user:pass@host/dbname`

5. **Create Worker** tugmasini bosing — deploy avtomatik boshlanadi.

---

## 🛠 Admin buyruqlari

| Buyruq | Tavsif |
|---|---|
| `/admin` | Admin paneliga kirish |
| `/addmovie KOD \| Nom \| Link` | Kino qo'shish |
| `/addmovie KOD \| Nom \| Link \| premium` | Premium kino qo'shish |
| `/delmovie KOD` | Kinoni o'chirish (faolsizlantirish) |
| `/givevip TELEGRAM_ID KUNLAR` | Foydalanuvchiga VIP berish |
| `/cancel` | Joriy amalni bekor qilish |

---

## ✨ Imkoniyatlar

- ✅ Inline tugmalar bilan menyu
- ✅ Majburiy obuna (bir nechta kanal, DB da saqlanadi)
- ✅ Kino kodi orqali ssilka olish
- ✅ Kunlik kod limiti (oddiy: 3 ta/kun, VIP: cheksiz)
- ✅ Premium kinolar (faqat VIP ko'radi)
- ✅ VIP: skrinshot → admin tasdiqlash → avtomatik faollashtirish
- ✅ Admin: statistika, kinolar, kanallar, VIP, broadcast
- ✅ Broadcast (barcha foydalanuvchilarga xabar)
- ✅ GitHub + Render deploy tayyor
