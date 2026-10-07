from __future__ import annotations

import asyncio
from collections import defaultdict, deque
import logging
from time import monotonic

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.config import Settings, get_settings
from app.admin_panel import setup_admin_routes
from app.handlers import build_router
from app.storage import UserStorage, create_user_storage
from app.portal_store import PortalStore
from app.webapp import setup_webapp_routes, webapp_page

logger = logging.getLogger(__name__)
APP_VERSION = "2026-10-07-full-permission-reference-v15"


def create_http_middlewares(settings: Settings):
    from aiohttp import web

    requests: dict[str, deque[float]] = defaultdict(deque)

    @web.middleware
    async def security(request: web.Request, handler):
        if request.path == settings.webhook_path and settings.webhook_secret:
            supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if supplied != settings.webhook_secret:
                raise web.HTTPForbidden(text="Webhook token noto'g'ri.")
        if request.path.startswith("/api/webapp/"):
            key = request.remote or "unknown"
            now = monotonic()
            history = requests[key]
            while history and history[0] < now - 60:
                history.popleft()
            if len(history) >= 90:
                raise web.HTTPTooManyRequests(text="So'rovlar juda ko'p. Bir daqiqadan keyin urinib ko'ring.")
            history.append(now)
            if len(requests) > 5000:
                requests.clear()
        response = await handler(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

    return [security]


def setup_portal_lifecycle(app, settings: Settings, store: PortalStore) -> None:
    async def initialize(_: object) -> None:
        await store.initialize()
        app["portal_ready"] = True

        async def notification_worker() -> None:
            from aiohttp import ClientSession

            messages = {
                "uz": "Saqlangan yo'nalishingiz bo'yicha qoidalar yangilandi. Web App orqali qayta tekshiring.",
                "ru": "Правила по сохраненному маршруту обновлены. Повторите проверку в Web App.",
                "en": "Rules for your saved route were updated. Please check the route again in the Web App.",
            }
            async with ClientSession() as session:
                while True:
                    try:
                        rows = await store.pending_notifications()
                        for row in rows:
                            language = str(row.get("language") or "uz")
                            payload = {
                                "chat_id": int(row["telegram_user_id"]),
                                "text": messages.get(language, messages["uz"]),
                                "disable_web_page_preview": True,
                            }
                            async with session.post(
                                f"https://api.telegram.org/bot{settings.bot_token}/sendMessage",
                                json=payload,
                                timeout=10,
                            ) as response:
                                await store.finish_notification(int(row["id"]), response.status == 200)
                        await asyncio.sleep(15 if rows else 45)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        logger.exception("Rule notification worker failed")
                        await asyncio.sleep(30)

        app["notification_task"] = asyncio.create_task(notification_worker())

    async def close(_: object) -> None:
        task = app.get("notification_task")
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await store.close()

    app.on_startup.append(initialize)
    app.on_cleanup.append(close)


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


async def start_health_server(settings: Settings):
    from aiohttp import web

    async def health(request: web.Request) -> web.Response:
        ready = bool(request.app.get("portal_ready"))
        return web.json_response({"ok": ready, "ready": ready, "service": "nazoratbot-telegram", "version": APP_VERSION}, status=200 if ready else 503)

    app = web.Application(client_max_size=12 * 1024 * 1024, middlewares=create_http_middlewares(settings))
    portal_store = PortalStore(
        settings.user_database_url,
        settings.database_path,
        settings.database_quota_mb,
    )
    setup_portal_lifecycle(app, settings, portal_store)
    app.router.add_get("/", webapp_page)
    app.router.add_get("/health", health)
    setup_admin_routes(app, settings, portal_store)
    setup_webapp_routes(app, settings, portal_store)

    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, settings.web_host, settings.web_port)
    await site.start()
    logger.info("Health server started on http://%s:%s version=%s", settings.web_host, settings.web_port, APP_VERSION)
    return runner


async def run_polling() -> None:
    settings = get_settings()
    bot = create_bot(settings)
    dispatcher, user_storage = create_dispatcher(settings)

    await user_storage.init()
    runner = await start_health_server(settings)
    await configure_telegram_webapp(bot, settings)
    runner.app["telegram_ready"] = True
    logger.info("Starting Telegram polling mode. Existing webhook will be deleted.")
    await bot.delete_webhook(drop_pending_updates=False)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await user_storage.close()
        await runner.cleanup()
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

    async def health(request: web.Request) -> web.Response:
        ready = bool(request.app.get("portal_ready"))
        return web.json_response(
            {"ok": ready, "ready": ready, "service": "nazoratbot-telegram", "mode": "webhook", "version": APP_VERSION},
            status=200 if ready else 503,
        )

    async def on_startup(bot: Bot) -> None:
        await user_storage.init()
        logger.info("Setting Telegram webhook: %s", webhook_url)
        await bot.set_webhook(
            webhook_url,
            drop_pending_updates=False,
            secret_token=settings.webhook_secret or None,
        )
        await configure_telegram_webapp(bot, settings)
        app["telegram_ready"] = True

    async def on_shutdown(bot: Bot) -> None:
        await user_storage.close()
        await bot.session.close()

    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)

    app = web.Application(client_max_size=12 * 1024 * 1024, middlewares=create_http_middlewares(settings))
    portal_store = PortalStore(
        settings.user_database_url,
        settings.database_path,
        settings.database_quota_mb,
    )
    setup_portal_lifecycle(app, settings, portal_store)
    app.router.add_get("/", webapp_page)
    app.router.add_get("/health", health)
    setup_admin_routes(app, settings, portal_store)
    setup_webapp_routes(app, settings, portal_store)
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
