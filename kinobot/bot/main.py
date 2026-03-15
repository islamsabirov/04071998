import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import settings
from .db import init_db
from .handlers import admin_router, codes_router, user_menu_router, vip_router
from .notify import set_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _build_web_app() -> web.Application:
    """Payme va Click webhook uchun aiohttp ilovasi."""
    from .services.payment_payme import payme_handler
    from .services.payment_click import click_handler

    app = web.Application()
    app.router.add_post("/payme/", payme_handler)
    app.router.add_post("/click/", click_handler)

    async def healthcheck(request: web.Request) -> web.Response:
        return web.Response(text="OK")

    app.router.add_get("/", healthcheck)
    app.router.add_get("/health", healthcheck)
    return app


async def main() -> None:
    logger.info("Bot ishga tushmoqda...")

    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    set_bot(bot)   # payment webhook notify uchun

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(user_menu_router)
    dp.include_router(vip_router)
    dp.include_router(admin_router)
    dp.include_router(codes_router)   # eng oxirida

    logger.info("Database ishga tushmoqda...")
    await init_db()

    # Web server (Payme/Click webhook)
    app = _build_web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=settings.web_port)
    await site.start()
    logger.info("Web server port %d da ishga tushdi.", settings.web_port)

    logger.info("Bot polling boshladi...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
