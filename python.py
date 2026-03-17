# setup_bot.py - Bot loyihasini avtomatik yaratish
import os
from pathlib import Path

# Fayl tuzilmasi
STRUCTURE = {
    'premium_bot': {
        'main.py': '''# main.py
import logging
import asyncio
from bot import PremiumBot
from config import config
from database import db

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Botni ishga tushirish"""
    try:
        if not config.validate():
            logger.error("❌ Config validatsiya muvaffaqiyatsiz!")
            return
        
        logger.info("🗄️ Database connection testing...")
        db.get_statistics()
        logger.info("✅ Database connected successfully")
        
        logger.info("🚀 Starting Premium Bot...")
        config.print_summary()
        
        bot = PremiumBot()
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot to'xtatildi (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}", exc_info=True)
    finally:
        db.close()
        logger.info("🔌 Database connections closed")


if __name__ == "__main__":
    main()
''',
        
        'config.py': '''# config.py
import os
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Config:
    BOT_TOKEN = "8759637966:AAGZCbdLQaU9ihA0RXWuGmt7vtF1JmXqkRc"
    ADMIN_IDS = 5907118746
    _channel_id_raw = os.getenv('CHANNEL_ID', '')
    CHANNEL_ID = int(_channel_id_raw) if _channel_id_raw.strip().isdigit() else None
    BOT_USERNAME = os.getenv('BOT_USERNAME', '').strip()
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'uz').lower()
    SUPPORTED_LANGUAGES = ['uz', 'ru', 'en']
    
    DB_TYPE = os.getenv('DB_TYPE', 'postgresql').lower()
    DB_NAME = os.getenv('DB_NAME', 'premium_bot')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    SQLITE_PATH = os.getenv('SQLITE_PATH', 'bot.db')
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 10))
    
    @property
    def DATABASE_URL(self):
        if self.DB_TYPE == 'sqlite':
            return f"sqlite:///{self.SQLITE_PATH}"
        password_encoded = quote_plus(self.DB_PASSWORD)
        return f"postgresql://{self.DB_USER}:{password_encoded}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    CLICK_SERVICE_ID = os.getenv('CLICK_SERVICE_ID', '')
    CLICK_MERCHANT_ID = os.getenv('CLICK_MERCHANT_ID', '')
    CLICK_SECRET_KEY = os.getenv('CLICK_SECRET_KEY', '')
    
    @property
    def CLICK_ENABLED(self):
        return all([self.CLICK_SERVICE_ID, self.CLICK_MERCHANT_ID, self.CLICK_SECRET_KEY])
    
    PAYME_MERCHANT_ID = os.getenv('PAYME_MERCHANT_ID', '')
    PAYME_KEY = os.getenv('PAYME_KEY', '')
    
    @property
    def PAYME_ENABLED(self):
        return all([self.PAYME_MERCHANT_ID, self.PAYME_KEY])
    
    USE_WEBHOOK = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').rstrip('/')
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    TARIFFS = {
        "basic": {"id": 1, "slug": "basic", "name_uz": "🔰 Basic", "name_ru": "🔰 Базовый", "name_en": "🔰 Basic", "price": 5000, "days": 7, "popular": False, "features": {"uz": ["✅ Premium kirish", "📢 VIP kanal"], "ru": ["✅ Премиум доступ", "📢 VIP канал"], "en": ["✅ Premium access", "📢 VIP channel"]}},
        "standart": {"id": 2, "slug": "standart", "name_uz": "⚡ Standart", "name_ru": "⚡ Стандарт", "name_en": "⚡ Standart", "price": 15000, "days": 30, "popular": True, "features": {"uz": ["✅ Premium kirish", "📢 VIP kanal", "👥 Referral + bonus"], "ru": ["✅ Премиум доступ", "📢 VIP канал", "👥 Рефералы + бонус"], "en": ["✅ Premium access", "📢 VIP channel", "👥 Referral + bonus"]}},
        "premium": {"id": 3, "slug": "premium", "name_uz": "💎 Premium", "name_ru": "💎 Премиум", "name_en": "💎 Premium", "price": 30000, "days": 90, "popular": False, "features": {"uz": ["✅ Premium kirish", "📢 VIP kanal", "👥 Referral + bonus", "📊 Statistika"], "ru": ["✅ Премиум доступ", "📢 VIP канал", "👥 Рефералы + бонус", "📊 Статистика"], "en": ["✅ Premium access", "📢 VIP channel", "👥 Referral + bonus", "📊 Statistics"]}},
        "vip": {"id": 4, "slug": "vip", "name_uz": "👑 VIP", "name_ru": "👑 VIP", "name_en": "👑 VIP", "price": 50000, "days": 365, "popular": False, "features": {"uz": ["✅ Premium kirish", "📢 VIP kanal", "👥 Referral + bonus", "📊 Statistika", "⚡ Tez support"], "ru": ["✅ Премиум доступ", "📢 VIP канал", "👥 Рефералы + бонус", "📊 Статистика", "⚡ Быстрая поддержка"], "en": ["✅ Premium access", "📢 VIP channel", "👥 Referral + bonus", "📊 Statistics", "⚡ Fast support"]}}
    }
    
    REFERRAL_BONUSES = {5: 3, 10: 7, 25: 15, 50: 30, 100: 90}
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true'
    
    def get_tariff(self, slug):
        return self.TARIFFS.get(slug.lower())
    
    def get_tariff_by_id(self, tariff_id):
        for tariff in self.TARIFFS.values():
            if tariff['id'] == tariff_id:
                return tariff
        return None
    
    def get_referral_bonus_days(self, count):
        bonus = 0
        for threshold, days in sorted(self.REFERRAL_BONUSES.items(), reverse=True):
            if count >= threshold:
                bonus = days
                break
        return bonus
    
    @classmethod
    def validate(cls):
        required = ['BOT_TOKEN']
        missing = [key for key in required if not getattr(cls, key, None)]
        if missing:
            logger.error(f"❌ Missing: {missing}")
            return False
        return True
    
    @classmethod
    def print_summary(cls):
        print("\\n" + "="*50)
        print("🤖 PREMIUM BOT - CONFIG")
        print("="*50)
        print(f"✅ Bot Token: {'***' + cls.BOT_TOKEN[-5:] if cls.BOT_TOKEN else '❌'}")
        print(f"✅ Admin IDs: {cls.ADMIN_IDS or 'None'}")
        print(f"✅ Database: {cls.DB_TYPE.upper()}")
        print(f"✅ Webhook: {'Enabled' if cls.USE_WEBHOOK else 'Disabled'}")
        print("="*50 + "\\n")


config = Config()
''',
        
        'database.py': '''# database.py
import logging
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from config import config

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    pass


class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._pool = None
        self._connect()
        self.create_tables()
    
    def _connect(self):
        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=config.DB_POOL_SIZE,
                dbname=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                host=config.DB_HOST,
                port=config.DB_PORT,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            logger.info(f"✅ Database connected: {config.DB_HOST}:{config.DB_PORT}")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise DatabaseError(f"Cannot connect: {e}")
    
    @contextmanager
    def get_cursor(self, commit=False):
        conn = None
        cursor = None
        try:
            conn = self._pool.getconn()
            cursor = conn.cursor()
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseError(f"Query failed: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._pool.putconn(conn)
    
    def create_tables(self):
        tables = [
            """CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                full_name VARCHAR(255),
                language VARCHAR(10) DEFAULT 'uz',
                is_premium BOOLEAN DEFAULT FALSE,
                premium_until TIMESTAMP,
                referral_count INTEGER DEFAULT 0,
                referred_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
                is_banned BOOLEAN DEFAULT FALSE,
                ban_reason TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                amount DECIMAL(10, 2) NOT NULL,
                tariff_id INTEGER NOT NULL,
                tariff_slug VARCHAR(50),
                payment_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                screenshot_file_id VARCHAR(255),
                transaction_id VARCHAR(255) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_by BIGINT REFERENCES users(user_id),
                approved_at TIMESTAMP,
                rejected_reason TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS referrals (
                id SERIAL PRIMARY KEY,
                referrer_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                referred_id BIGINT UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
                bonus_days_given INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(referrer_id, referred_id)
            )""",
            """CREATE TABLE IF NOT EXISTS user_activities (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                action VARCHAR(100) NOT NULL,
                details JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS admin_logs (
                id SERIAL PRIMARY KEY,
                admin_id BIGINT REFERENCES users(user_id),
                action VARCHAR(100) NOT NULL,
                target_user_id BIGINT,
                details JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        with self.get_cursor(commit=True) as cursor:
            for table_sql in tables:
                cursor.execute(table_sql)
    
    def add_user(self, user_id, username, full_name, referred_by=None, language='uz'):
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO users (user_id, username, full_name, language, referred_by)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        full_name = EXCLUDED.full_name,
                        last_activity = CURRENT_TIMESTAMP
                """, (user_id, username, full_name, language, referred_by))
                if referred_by:
                    cursor.execute("""
                        INSERT INTO referrals (referrer_id, referred_id)
                        VALUES (%s, %s)
                        ON CONFLICT (referrer_id, referred_id) DO NOTHING
                    """, (referred_by, user_id))
                    cursor.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id = %s", (referred_by,))
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def user_exists(self, user_id):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE user_id = %s LIMIT 1", (user_id,))
            return cursor.fetchone() is not None
    
    def get_all_users(self, active_only=True, premium_only=False):
        query = "SELECT user_id FROM users WHERE 1=1"
        if active_only:
            query += " AND is_banned = FALSE"
        if premium_only:
            query += " AND is_premium = TRUE AND premium_until > CURRENT_TIMESTAMP"
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return [row['user_id'] for row in cursor.fetchall()]
    
    def update_user_activity(self, user_id):
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = %s", (user_id,))
    
    def log_user_action(self, user_id, action, details=None):
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("INSERT INTO user_activities (user_id, action, details) VALUES (%s, %s, %s)", (user_id, action, details))
    
    def update_user_language(self, user_id, language):
        if language not in ['uz', 'ru', 'en']:
            return False
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("UPDATE users SET language = %s WHERE user_id = %s", (language, user_id))
            return cursor.rowcount > 0
    
    def get_user_language(self, user_id):
        user = self.get_user(user_id)
        if user and user['language'] in ['uz', 'ru', 'en']:
            return user['language']
        return config.DEFAULT_LANGUAGE
    
    def is_premium(self, user_id):
        user = self.get_user(user_id)
        if not user or not user['is_premium']:
            return False
        if user['premium_until'] and user['premium_until'] < datetime.now():
            self._expire_premium(user_id)
            return False
        return True
    
    def get_premium_expiry(self, user_id):
        user = self.get_user(user_id)
        if user and user['is_premium'] and user['premium_until']:
            return user['premium_until']
        return None
    
    def give_premium(self, user_id, days, admin_id=None, reason="payment"):
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            if user['is_premium'] and user['premium_until'] and user['premium_until'] > datetime.now():
                new_until = user['premium_until'] + timedelta(days=days)
            else:
                new_until = datetime.now() + timedelta(days=days)
            with self.get_cursor(commit=True) as cursor:
                cursor.execute("UPDATE users SET is_premium = TRUE, premium_until = %s WHERE user_id = %s", (new_until, user_id))
                if admin_id:
                    cursor.execute("INSERT INTO admin_logs (admin_id, action, target_user_id, details) VALUES (%s, %s, %s, %s)",
                                   (admin_id, f'give_premium_{reason}', user_id, {'days': days}))
            logger.info(f"💎 Premium given: user={user_id}, days={days}")
            return True
        except Exception as e:
            logger.error(f"Error giving premium: {e}")
            return False
    
    def _expire_premium(self, user_id):
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("UPDATE users SET is_premium = FALSE, premium_until = NULL WHERE user_id = %s", (user_id,))
    
    def add_payment(self, user_id, amount, tariff_id, payment_type, tariff_slug=None, screenshot_id=None, transaction_id=None):
        try:
            with self.get_cursor(commit=True) as cursor:
                cursor.execute("""
                    INSERT INTO payments (user_id, amount, tariff_id, tariff_slug, payment_type, screenshot_file_id, transaction_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, amount, tariff_id, tariff_slug, payment_type, screenshot_id, transaction_id))
                return cursor.fetchone()['id']
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return None
    
    def get_payment(self, payment_id):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT p.*, u.username, u.full_name, u.language FROM payments p JOIN users u ON p.user_id = u.user_id WHERE p.id = %s", (payment_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_pending_payments(self, limit=50):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT p.*, u.username, u.full_name, u.language FROM payments p JOIN users u ON p.user_id = u.user_id WHERE p.status = 'pending' ORDER BY p.created_at ASC LIMIT %s", (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_payments(self, user_id, status=None, limit=20):
        query = "SELECT * FROM payments WHERE user_id = %s"
        params = [user_id]
        if status:
            query += " AND status = %s"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def approve_payment(self, payment_id, admin_id):
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE payments SET status = 'approved', approved_by = %s, approved_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING user_id, tariff_id, tariff_slug, amount
            """, (admin_id, payment_id))
            result = cursor.fetchone()
            if result:
                result = dict(result)
                tariff = config.get_tariff_by_id(result['tariff_id'])
                if tariff:
                    self.give_premium(result['user_id'], tariff['days'], admin_id, "payment")
                return result
            return None
    
    def reject_payment(self, payment_id, admin_id, reason):
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("UPDATE payments SET status = 'rejected', approved_by = %s, approved_at = CURRENT_TIMESTAMP, rejected_reason = %s WHERE id = %s", (admin_id, reason, payment_id))
            logger.info(f"❌ Payment rejected: {payment_id}")
            return True
    
    def get_referral_link(self, user_id):
        bot_username = config.BOT_USERNAME or "premium_bot"
        if bot_username.startswith('@'):
            bot_username = bot_username[1:]
        return f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    def get_referral_stats(self, user_id):
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as total, COUNT(CASE WHEN u.is_premium THEN 1 END) as premium_count
                FROM referrals r JOIN users u ON r.referred_id = u.user_id
                WHERE r.referrer_id = %s
            """, (user_id,))
            stats = dict(cursor.fetchone())
            cursor.execute("SELECT COALESCE(SUM(bonus_days_given), 0) as total_bonus_days FROM referrals WHERE referrer_id = %s", (user_id,))
            stats['bonus_days'] = cursor.fetchone()['total_bonus_days']
            cursor.execute("""
                SELECT r.created_at, u.user_id, u.username, u.full_name, u.is_premium
                FROM referrals r JOIN users u ON r.referred_id = u.user_id
                WHERE r.referrer_id = %s ORDER BY r.created_at DESC LIMIT 5
            """, (user_id,))
            stats['recent_referrals'] = [dict(row) for row in cursor.fetchall()]
            return stats
    
    def ban_user(self, user_id, admin_id, reason):
        if user_id in config.ADMIN_IDS:
            return False
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("UPDATE users SET is_banned = TRUE, ban_reason = %s WHERE user_id = %s", (reason, user_id))
            cursor.execute("INSERT INTO admin_logs (admin_id, action, target_user_id, details) VALUES (%s, %s, %s, %s)", (admin_id, 'ban_user', user_id, {'reason': reason}))
        return True
    
    def is_banned(self, user_id):
        user = self.get_user(user_id)
        return bool(user and user['is_banned'])
    
    def get_statistics(self):
        stats = {}
        with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_banned = FALSE")
            stats['active_users'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = TRUE AND premium_until > CURRENT_TIMESTAMP")
            stats['premium_users'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(joined_at) = CURRENT_DATE AND is_banned = FALSE")
            stats['new_today'] = cursor.fetchone()[0]
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'approved'")
            stats['total_income'] = float(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
            stats['pending_payments'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM referrals")
            stats['total_referrals'] = cursor.fetchone()[0]
        return stats
    
    def close(self):
        if self._pool:
            self._pool.closeall()
            logger.info("🔌 Database connections closed")
    
    def __del__(self):
        self.close()


db = Database()
''',
        
        'bot.py': '''# bot.py
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config import config
from database import db
from handlers.start import start_handler
from handlers.payment import handle_screenshot
from handlers.admin import admin_panel, broadcast_handler, give_premium_handler
from handlers.callback import callback_handler
from utils.decorators import check_banned, check_maintenance
from utils.keyboards import get_main_keyboard
from utils.messages import get_message

logger = logging.getLogger(__name__)


class PremiumBot:
    def __init__(self):
        self.app = Application.builder().token(config.BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", start_handler))
        self.app.add_handler(CommandHandler("menu", self.menu_command))
        self.app.add_handler(CommandHandler("premium", self.premium_command))
        self.app.add_handler(CommandHandler("admin", admin_panel))
        self.app.add_handler(CommandHandler("broadcast", broadcast_handler))
        self.app.add_handler(CommandHandler("give", give_premium_handler))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.app.add_handler(MessageHandler(filters.PHOTO, handle_screenshot))
        self.app.add_handler(CallbackQueryHandler(callback_handler, pattern="^"))
        self.app.add_error_handler(self.error_handler)
    
    @check_maintenance
    @check_banned
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        lang = db.get_user_language(user.id)
        await update.message.reply_text(get_message('menu', lang=lang), reply_markup=get_main_keyboard(lang))
        db.update_user_activity(user.id)
    
    @check_maintenance
    @check_banned
    async def premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from handlers.callback import show_premium_info
        await show_premium_info(update, context)
    
    @check_maintenance
    @check_banned
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        text = update.message.text.strip()
        db.update_user_activity(user.id)
        if text in ["💎 Premium", "💳 Sotib olish", "👥 Referral", "📢 Kanal", "⚙️ Sozlamalar"]:
            await self.menu_command(update, context)
        else:
            lang = db.get_user_language(user.id)
            await update.message.reply_text("❌ Noto'g'ri buyruq. /menu ni bosing.", reply_markup=get_main_keyboard(lang))
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.error(f"Update {update} caused error: {context.error}", exc_info=context.error)
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(get_message('error', lang='uz'))
        except:
            pass
    
    def run(self):
        logger.info("🚀 Bot polling rejimida ishga tushdi...")
        print("✅ Bot is running (POLLING mode)...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
''',
        
        '.env': '''# Bot
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
BOT_USERNAME=@your_bot
ADMIN_IDS=your_admin_id
CHANNEL_ID=-100xxxxxxxxxx
DEFAULT_LANGUAGE=uz

# Database
DB_TYPE=postgresql
DB_NAME=premium_bot
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_POOL_SIZE=10

# Payment
CLICK_SERVICE_ID=
CLICK_MERCHANT_ID=
CLICK_SECRET_KEY=
PAYME_MERCHANT_ID=
PAYME_KEY=

# Webhook
USE_WEBHOOK=false
WEBHOOK_URL=
PORT=5000

# Features
DEBUG=false
MAINTENANCE_MODE=false
''',
        
        '.gitignore': '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Environment
.env
*.log

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
''',
        
        'requirements.txt': '''python-telegram-bot>=20.6
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
aiohttp>=3.9.0
''',
        
        'handlers/__init__.py': '',
        
        'handlers/start.py': '''# handlers/start.py
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from utils.messages import get_message
from utils.keyboards import get_main_keyboard


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = db.get_user_language(user.id) if db.user_exists(user.id) else 'uz'
    
    referred_by = None
    if context.args:
        arg = context.args[0]
        if arg.startswith('ref_'):
            try:
                referred_by = int(arg.split('_')[1])
                if referred_by == user.id:
                    referred_by = None
            except (ValueError, IndexError):
                referred_by = None
    
    full_name = user.full_name or user.username or f"User {user.id}"
    db.add_user(user_id=user.id, username=user.username, full_name=full_name, referred_by=referred_by, language=lang)
    
    welcome_msg = get_message('welcome', lang=lang, name=user.first_name or '')
    await update.message.reply_text(welcome_msg, reply_markup=get_main_keyboard(lang))
    db.log_user_action(user.id, 'start', {'referred_by': referred_by})
''',
        
        'handlers/menu.py': '''# handlers/menu.py
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from utils.messages import get_message
from utils.keyboards import get_main_keyboard


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = db.get_user_language(user.id)
    await update.message.reply_text(get_message('menu', lang=lang), reply_markup=get_main_keyboard(lang))
    db.update_user_activity(user.id)
''',
        
        'handlers/premium.py': '''# handlers/premium.py
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import config
from utils.messages import get_message


async def premium_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.callback import show_premium_info
    await show_premium_info(update, context)
''',
        
        'handlers/payment.py': '''# handlers/payment.py
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import config
from utils.messages import get_message
from utils.keyboards import get_payment_keyboard
from utils.decorators import check_banned, check_subscription


@check_banned
@check_subscription
async def show_tariffs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = db.get_user_language(user.id)
    from utils.keyboards import get_tariffs_keyboard
    await update.message.reply_text("💎 *Tariflarni tanlang:*", parse_mode='Markdown', reply_markup=get_tariffs_keyboard(lang))


@check_banned
@check_subscription
async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = db.get_user_language(user.id)
    
    pending_payments = db.get_user_payments(user.id, status='pending')
    if pending_payments:
        await update.message.reply_text("⚠️ Sizda allaqachon kutilayotgan to'lov bor.")
        return
    
    photo = update.message.photo[-1]
    screenshot_id = photo.file_id
    
    payment_id = db.add_payment(user_id=user.id, amount=0, tariff_id=0, payment_type='manual', screenshot_id=screenshot_id)
    
    await update.message.reply_text(get_message('payment_sent', lang=lang))
    
    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_photo(chat_id=admin_id, photo=screenshot_id,
                caption=f"💳 *Yangi to'lov*\\n\\n👤 User: {user.full_name}\\n🆔 ID: {user.id}\\n📸 Payment ID: {payment_id}",
                parse_mode='Markdown', reply_markup=get_payment_keyboard(payment_id))
        except:
            pass
''',
        
        'handlers/referral.py': '''# handlers/referral.py
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from utils.messages import get_message


async def referral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from handlers.callback import show_referral_info
    await show_referral_info(update, context)
''',
        
        'handlers/channel.py': '''# handlers/channel.py
from telegram import Update
from telegram.ext import ContextTypes
from config import config


async def channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📢 *Bizning Kanal*\\n\\nYangiliklar uchun obuna bo'ling!\\n\\n🔗 https://t.me/{config.BOT_USERNAME or 'premium_channel'}", parse_mode='Markdown')
''',
        
        'handlers/admin.py': '''# handlers/admin.py
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import config
from utils.messages import get_message
from utils.keyboards import get_admin_keyboard
from utils.decorators import check_admin


@check_admin
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = db.get_statistics()
    await update.message.reply_text(get_message('admin_panel', lang='uz', **stats), reply_markup=get_admin_keyboard())


@check_admin
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Foydalanish: /broadcast <xabar>")
        return
    
    message_text = ' '.join(context.args)
    users = db.get_all_users(active_only=True)
    sent_count = 0
    
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message_text, parse_mode='Markdown')
            sent_count += 1
        except:
            pass
    
    await update.message.reply_text(get_message('broadcast_sent', lang='uz', count=sent_count))
    db.log_user_action(update.effective_user.id, 'broadcast', {'sent': sent_count})


@check_admin
async def give_premium_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Foydalanish: /give <user_id> <days>")
        return
    
    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ user_id va days raqam bo'lishi kerak!")
        return
    
    if db.give_premium(user_id, days, admin_id=update.effective_user.id):
        await update.message.reply_text(f"✅ {user_id} ga {days} kun premium berildi!")
        try:
            user = db.get_user(user_id)
            lang = user.get('language', 'uz') if user else 'uz'
            until = db.get_premium_expiry(user_id)
            await context.bot.send_message(chat_id=user_id,
                text=get_message('payment_approved', lang=lang, days=days, until=until.strftime('%Y-%m-%d %H:%M') if until else 'N/A'))
        except:
            pass
    else:
        await update.message.reply_text("❌ Xatolik! User topilmadi.")
''',
        
        'handlers/callback.py': '''# handlers/callback.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from config import config
from utils.messages import get_message
from utils.keyboards import get_main_keyboard, get_tariffs_keyboard, get_settings_keyboard, get_referral_keyboard


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    
    if data == "back_to_menu":
        await query.edit_message_text(get_message('menu', lang=lang), reply_markup=get_main_keyboard(lang))
    elif data == "menu_premium":
        await show_premium_info(update, context)
    elif data == "menu_buy":
        await query.edit_message_text("💎 *Tariflarni tanlang:*", parse_mode='Markdown', reply_markup=get_tariffs_keyboard(lang))
    elif data == "menu_referral":
        await show_referral_info(update, context)
    elif data == "menu_channel":
        await query.edit_message_text(f"📢 *Bizning Kanal*\\n\\nYangiliklar uchun obuna bo'ling!", parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Obuna bo'lish", url=f"https://t.me/{config.BOT_USERNAME or 'premium_channel'}")]]))
    elif data == "menu_settings":
        await query.edit_message_text("⚙️ *Sozlamalar*\\n\\nTilni tanlang:", parse_mode='Markdown', reply_markup=get_settings_keyboard(lang))
    elif data.startswith("lang_"):
        new_lang = data.split('_')[1]
        db.update_user_language(user_id, new_lang)
        await query.edit_message_text(f"✅ Til o'zgartirildi: {new_lang.upper()}", reply_markup=get_main_keyboard(new_lang))
    elif data.startswith("tariff_"):
        tariff_slug = data.split('_')[1]
        tariff = config.get_tariff(tariff_slug)
        if tariff:
            name = tariff.get(f'name_{lang}', tariff['name_uz'])
            features = '\\n'.join(tariff['features'].get(lang, tariff['features']['uz']))
            await query.edit_message_text(f"💎 *{name}*\\n\\n📅 {tariff['days']} kun\\n💰 {tariff['price']:,} so'm\\n\\n📋 *Features:*\\n{features}\\n\\n💳 To'lov uchun screenshot yuboring:", parse_mode='Markdown')
    elif data == "check_channel":
        if config.CHANNEL_ID:
            try:
                member = await context.bot.get_chat_member(config.CHANNEL_ID, user_id)
                if member.status in ['member', 'administrator', 'creator']:
                    db.update_user_activity(user_id)
                    await query.edit_message_text(get_message('channel_subscribed', lang=lang), reply_markup=get_main_keyboard(lang))
                    return
            except:
                pass
        await query.answer("⚠️ Hali obuna bo'lmagansiz!", show_alert=True)
    elif data.startswith("approve_"):
        if user_id not in config.ADMIN_IDS:
            await query.answer("❌ Faqat adminlar!", show_alert=True)
            return
        payment_id = int(data.split('_')[1])
        result = db.approve_payment(payment_id, user_id)
        if result:
            await query.edit_message_caption(caption=f"✅ TASDIQLANDI\\n\\nPayment ID: {payment_id}")
            try:
                tariff = config.get_tariff_by_id(result['tariff_id'])
                days = tariff['days'] if tariff else 30
                until = db.get_premium_expiry(result['user_id'])
                await context.bot.send_message(chat_id=result['user_id'],
                    text=get_message('payment_approved', lang='uz', days=days, until=until.strftime('%Y-%m-%d %H:%M') if until else 'N/A'))
            except:
                pass
        else:
            await query.answer("❌ Xatolik!", show_alert=True)
    elif data.startswith("reject_"):
        if user_id not in config.ADMIN_IDS:
            await query.answer("❌ Faqat adminlar!", show_alert=True)
            return
        payment_id = int(data.split('_')[1])
        db.reject_payment(payment_id, user_id, "Admin rad etdi")
        await query.edit_message_caption(caption=f"❌ RAD ETILDI\\n\\nPayment ID: {payment_id}")


async def show_premium_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    
    is_premium = db.is_premium(user_id)
    expiry = db.get_premium_expiry(user_id)
    
    if is_premium and expiry:
        text = f"✅ *Premium aktiv!*\\n\\n⏰ Tugash vaqti: {expiry.strftime('%Y-%m-%d %H:%M')}"
    else:
        cheapest = min(config.TARIFFS.values(), key=lambda x: x['price'])
        text = get_message('premium_info', lang=lang, days=cheapest['days'], price=cheapest['price'])
    
    if query:
        await query.edit_message_text(text, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, parse_mode='Markdown')


async def show_referral_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user_id = update.effective_user.id
    lang = db.get_user_language(user_id)
    
    stats = db.get_referral_stats(user_id)
    link = db.get_referral_link(user_id)
    bonus_days = config.get_referral_bonus_days(stats.get('total', 0))
    
    text = get_message('referral_info', lang=lang, link=link, count=stats.get('total', 0), bonus_days=bonus_days)
    
    if query:
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_referral_keyboard(lang))
    else:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_referral_keyboard(lang))
''',
        
        'utils/__init__.py': '',
        
        'utils/decorators.py': '''# utils/decorators.py
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config import config
from database import db
from utils.messages import get_message


def check_banned(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if db.is_banned(user_id):
            user = db.get_user(user_id)
            reason = user.get('ban_reason', 'No reason') if user else 'Unknown'
            await update.message.reply_text(get_message('banned', lang='uz', reason=reason))
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def check_premium(required=True):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            user = db.get_user(user_id)
            lang = user.get('language', 'uz') if user else 'uz'
            is_premium = db.is_premium(user_id)
            if required and not is_premium:
                await update.message.reply_text(get_message('not_premium', lang=lang))
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


def check_admin(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in config.ADMIN_IDS:
            await update.message.reply_text("❌ Bu faqat administratorlar uchun!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def check_subscription(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not config.CHANNEL_ID:
            return await func(update, context, *args, **kwargs)
        user_id = update.effective_user.id
        try:
            member = await context.bot.get_chat_member(config.CHANNEL_ID, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                from utils.keyboards import get_channel_keyboard
                await update.message.reply_text(get_message('channel_required', lang='uz', channel=config.BOT_USERNAME or 'premium_channel'),
                    reply_markup=get_channel_keyboard('uz'))
                return
        except:
            pass
        return await func(update, context, *args, **kwargs)
    return wrapper


def check_maintenance(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if config.MAINTENANCE_MODE and update.effective_user.id not in config.ADMIN_IDS:
            await update.message.reply_text(get_message('maintenance', lang='uz'))
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
''',
        
        'utils/messages.py': '''# utils/messages.py
from typing import Dict

MESSAGES: Dict[str, Dict[str, str]] = {
    'uz': {
        'welcome': "👋 Assalomu alaykum, {name}!\\n\\n🤖 Premium Botga xush kelibsiz!",
        'menu': "📱 *Asosiy Menyu*\\n\\nTanlang:",
        'premium_info': "💎 *Premium Haqida*\\n\\nPremium obuna bilan siz:\\n✅ VIP kanalga kirish\\n✅ Maxsus funksiyalar\\n\\nMuddati: {days} kun\\nNarxi: {price:,} so'm",
        'not_premium': "❌ Sizda premium obuna yo'q.\\n\\n💳 Sotib olish uchun /premium buyrug'ini bosing.",
        'channel_required': "⚠️ *Kanalga obuna bo'ling!*\\n\\nBotdan foydalanish uchun kanalimizga obuna bo'lishingiz kerak.\\n\\n📢 Kanal: @{channel}\\n\\nObuna bo'lgandan keyin ✅ *Tekshirish* tugmasini bosing.",
        'channel_subscribed': "✅ Kanalga obuna bo'ldingiz! Rahmat!",
        'payment_sent': "📸 To'lov qabul qilindi!\\n\\nAdmin tasdiqlashini kuting (5-30 daqiqa).",
        'payment_approved': "✅ *To'lov tasdiqlandi!*\\n\\n💎 Premium aktivlashtirildi!\\n📅 Muddati: {days} kun\\n⏰ Tugash vaqti: {until}",
        'payment_rejected': "❌ *To'lov rad etildi*\\n\\nSabab: {reason}",
        'referral_info': "👥 *Referral Tizimi*\\n\\n🔗 Sizning link: {link}\\n\\n👥 Jalb qilinganlar: {count}\\n🎁 Bonus kunlar: {bonus_days}",
        'broadcast_sent': "📢 Xabar yuborildi: {count} ta userga",
        'admin_panel': "👑 *Admin Panel*\\n\\n📊 Statistika:\\n• Jami userlar: {total_users}\\n• Premium: {premium_users}\\n• Bugun: {new_today}\\n• Daromad: {total_income:,.0f} so'm\\n• Pending to'lovlar: {pending_payments}",
        'banned': "❌ Siz bloklangansiz!\\n\\nSabab: {reason}",
        'maintenance': "🔧 Bot texnik xizmatda.\\n\\nIltimos, keyinroq urinib ko'ring.",
        'error': "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
    },
    'ru': {
        'welcome': "👋 Здравствуйте, {name}!\\n\\n🤖 Добро пожаловать!",
        'menu': "📱 *Главное Меню*\\n\\nВыберите:",
        'premium_info': "💎 *О Премиуме*\\n\\nСрок: {days} дней\\nЦена: {price:,} сум",
        'not_premium': "❌ У вас нет премиум подписки.",
        'channel_required': "⚠️ *Подпишитесь на канал!*\\n\\n📢 Канал: @{channel}",
        'channel_subscribed': "✅ Вы подписались!",
        'payment_sent': "📸 Оплата принята!",
        'payment_approved': "✅ *Оплата подтверждена!*\\n📅 Срок: {days} дней\\n⏰ Истекает: {until}",
        'payment_rejected': "❌ *Оплата отклонена*\\nПричина: {reason}",
        'referral_info': "👥 *Реферальная Система*\\n\\n🔗 Ваша ссылка: {link}\\n👥 Приглашено: {count}\\n🎁 Бонус: {bonus_days}",
        'broadcast_sent': "📢 Сообщение отправлено: {count}",
        'admin_panel': "👑 *Панель Админа*\\n\\n📊 Статистика:\\n• Всего: {total_users}\\n• Премиум: {premium_users}\\n• Сегодня: {new_today}\\n• Доход: {total_income:,.0f}\\n• Ожидающие: {pending_payments}",
        'banned': "❌ Вы заблокированы!\\nПричина: {reason}",
        'maintenance': "🔧 Бот на обслуживании.",
        'error': "❌ Произошла ошибка.",
    },
    'en': {
        'welcome': "👋 Hello, {name}!\\n\\n🤖 Welcome!",
        'menu': "📱 *Main Menu*\\n\\nChoose:",
        'premium_info': "💎 *About Premium*\\n\\nDuration: {days} days\\nPrice: {price:,} UZS",
        'not_premium': "❌ You don't have premium.",
        'channel_required': "⚠️ *Subscribe to Channel!*\\n\\n📢 Channel: @{channel}",
        'channel_subscribed': "✅ You subscribed!",
        'payment_sent': "📸 Payment received!",
        'payment_approved': "✅ *Payment Approved!*\\n📅 Duration: {days} days\\n⏰ Expires: {until}",
        'payment_rejected': "❌ *Payment Rejected*\\nReason: {reason}",
        'referral_info': "👥 *Referral System*\\n\\n🔗 Your link: {link}\\n👥 Referred: {count}\\n🎁 Bonus: {bonus_days}",
        'broadcast_sent': "📢 Message sent: {count}",
        'admin_panel': "👑 *Admin Panel*\\n\\n📊 Statistics:\\n• Total: {total_users}\\n• Premium: {premium_users}\\n• Today: {new_today}\\n• Income: {total_income:,.0f}\\n• Pending: {pending_payments}",
        'banned': "❌ You are banned!\\nReason: {reason}",
        'maintenance': "🔧 Bot under maintenance.",
        'error': "❌ An error occurred.",
    }
}


def get_message(key: str, lang: str = 'uz', **kwargs) -> str:
    lang = lang if lang in MESSAGES else 'uz'
    message = MESSAGES.get(lang, MESSAGES['uz']).get(key, MESSAGES['uz']['error'])
    return message.format(**kwargs) if kwargs else message
''',
        
        'utils/keyboards.py': '''# utils/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import config


def get_main_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("💎 Premium", callback_data="menu_premium"), InlineKeyboardButton("💳 Sotib olish", callback_data="menu_buy")],
        [InlineKeyboardButton("👥 Referral", callback_data="menu_referral"), InlineKeyboardButton("📢 Kanal", callback_data="menu_channel")],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data="menu_settings")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_tariffs_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    keyboard = []
    for slug, tariff in config.TARIFFS.items():
        name = tariff.get(f'name_{lang}', tariff['name_uz'])
        price = f"{tariff['price']:,}"
        days = tariff['days']
        popular = " 🔥" if tariff.get('popular') else ""
        keyboard.append([InlineKeyboardButton(f"{name} - {price} so'm ({days} kun){popular}", callback_data=f"tariff_{slug}")])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_channel_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📢 Kanalga obuna", url=f"https://t.me/{config.BOT_USERNAME or 'premium_channel'}")],
        [InlineKeyboardButton("✅ Tekshirish", callback_data="check_channel")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_payment_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{payment_id}"), InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{payment_id}")],
        [InlineKeyboardButton("📸 Screenshot", callback_data=f"view_screenshot_{payment_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_referral_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔗 Linkni nusxalash", callback_data="copy_referral_link")],
        [InlineKeyboardButton("📊 Statistika", callback_data="referral_stats")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"), InlineKeyboardButton("💰 To'lovlar", callback_data="admin_payments")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"), InlineKeyboardButton("👥 Userlar", callback_data="admin_users")],
        [InlineKeyboardButton("⚙️ Sozlamalar", callback_data="admin_settings")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard(lang: str = 'uz') -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz"), InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"), InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
''',
        
        'utils/helpers.py': '',
        
        'services/__init__.py': '',
        
        'services/click.py': '''# services/click.py
# Click API integration (kelajakda)
pass
''',
        
        'services/payme.py': '''# services/payme.py
# Payme API integration (kelajakda)
pass
''',
        
        'services/ai.py': '''# services/ai.py
# AI integration (kelajakda)
pass
''',
        
        'middlewares/__init__.py': '',
        
        'middlewares/auth.py': '''# middlewares/auth.py
# Auth middleware (kelajakda)
pass
''',
        
        'middlewares/ban.py': '''# middlewares/ban.py
# Ban middleware (kelajakda)
pass
''',
        
        'middlewares/channel.py': '''# middlewares/channel.py
# Channel middleware (kelajakda)
pass
''',
        
        'logs/.gitkeep': '',
    }
}


def create_structure(base_path='.'):
    """Barcha fayllarni avtomatik yaratish"""
    for folder, files in STRUCTURE.items():
        if isinstance(files, dict):
            folder_path = Path(base_path) / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Yaratildi: {folder_path}")
            
            for filename, content in files.items():
                if '/' in filename:
                    # Nested folder
                    file_path = folder_path / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                else:
                    file_path = folder_path / filename
                
                file_path.write_text(content, encoding='utf-8')
                print(f"  📄 {filename}")
    
    print("\\n✅ Barcha fayllar yaratildi!")
    print("\\n📝 Endi .env faylini to'ldiring va botni ishga tushiring:")
    print("   python main.py")


if __name__ == '__main__':
    create_structure()