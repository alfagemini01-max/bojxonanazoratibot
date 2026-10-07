from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.config import Settings, get_settings
from app.admin_panel import setup_admin_routes
from app.handlers import build_router
from app.storage import UserStorage, create_user_storage
from app.webapp import setup_webapp_routes, webapp_page

logger = logging.getLogger(__name__)
APP_VERSION = "2026-10-07-permit-compat-v7"


def create_bot(settings: Settings) -> Bot:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN topilmadi. .env yoki Render Environment Variables ichiga BOT_TOKEN kiriting.")
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(settings: Settings) -> tuple[Dispatcher, UserStorage]:
    user_database_url = getattr(settings, "user_database_url", "")
    user_storage = create_user_storage(settings.database_path, settings.timezone, user_database_url)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(build_router(user_storage, settings))
    return dispatcher, user_storage


async def configure_telegram_webapp(bot: Bot, settings: Settings) -> None:
    if not settings.webhook_url.startswith("https://"):
        logger.warning("Telegram Web App menu skipped: public HTTPS WEBHOOK_URL is not configured.")
        return
    app_url = settings.webhook_url.rstrip("/") + "/app"
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Web App",
                web_app=WebAppInfo(url=app_url),
            )
        )
        logger.info("Telegram Web App menu configured: %s", app_url)
    except Exception:
        logger.exception("Telegram Web App menu could not be configured.")


async def start_health_server(settings: Settings) -> None:
    from aiohttp import web

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"ok": True, "service": "nazoratbot-telegram", "version": APP_VERSION})

    app = web.Application(client_max_size=12 * 1024 * 1024)
    app.router.add_get("/", webapp_page)
    app.router.add_get("/health", health)
    setup_admin_routes(app, settings)
    setup_webapp_routes(app, settings)

    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, settings.web_host, settings.web_port)
    await site.start()
    logger.info("Health server started on http://%s:%s version=%s", settings.web_host, settings.web_port, APP_VERSION)


async def run_polling() -> None:
    settings = get_settings()
    bot = create_bot(settings)
    dispatcher, user_storage = create_dispatcher(settings)

    await user_storage.init()
    await start_health_server(settings)
    await configure_telegram_webapp(bot, settings)
    logger.info("Starting Telegram polling mode. Existing webhook will be deleted.")
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await user_storage.close()
        await bot.session.close()


def run_webhook() -> None:
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    settings = get_settings()
    if not settings.webhook_url:
        raise RuntimeError("BOT_MODE=webhook uchun WEBHOOK_URL kiritilishi kerak.")

    bot = create_bot(settings)
    dispatcher, user_storage = create_dispatcher(settings)
    webhook_url = settings.webhook_url.rstrip("/") + settings.webhook_path

    async def health(_: web.Request) -> web.Response:
        return web.json_response(
            {"ok": True, "service": "nazoratbot-telegram", "mode": "webhook", "version": APP_VERSION}
        )

    async def on_startup(bot: Bot) -> None:
        await user_storage.init()
        logger.info("Setting Telegram webhook: %s", webhook_url)
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        await configure_telegram_webapp(bot, settings)

    async def on_shutdown(bot: Bot) -> None:
        await user_storage.close()
        await bot.session.close()

    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)

    app = web.Application(client_max_size=12 * 1024 * 1024)
    app.router.add_get("/", webapp_page)
    app.router.add_get("/health", health)
    setup_admin_routes(app, settings)
    setup_webapp_routes(app, settings)
    SimpleRequestHandler(dispatcher=dispatcher, bot=bot).register(app, path=settings.webhook_path)
    setup_application(app, dispatcher, bot=bot)
    web.run_app(app, host=settings.web_host, port=settings.web_port, access_log=None)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    settings = get_settings()
    if settings.bot_mode == "webhook":
        run_webhook()
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
