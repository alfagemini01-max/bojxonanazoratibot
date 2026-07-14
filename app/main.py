from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import Settings, get_settings
from app.handlers import build_router
from app.repositories.factory import create_vehicle_repository
from app.storage import UserStorage


def create_bot(settings: Settings) -> Bot:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN topilmadi. .env yoki Render Environment Variables ichiga BOT_TOKEN kiriting.")
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(settings: Settings) -> tuple[Dispatcher, UserStorage]:
    user_storage = UserStorage(settings.database_path, settings.timezone)
    vehicle_repository = create_vehicle_repository(settings)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(build_router(user_storage, vehicle_repository, settings))
    return dispatcher, user_storage


async def run_polling() -> None:
    settings = get_settings()
    bot = create_bot(settings)
    dispatcher, user_storage = create_dispatcher(settings)

    await user_storage.init()
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


def run_webhook() -> None:
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    settings = get_settings()
    if not settings.webhook_url:
        raise RuntimeError("BOT_MODE=webhook uchun WEBHOOK_URL kiritilishi kerak.")

    bot = create_bot(settings)
    dispatcher, user_storage = create_dispatcher(settings)
    webhook_url = settings.webhook_url.rstrip("/") + settings.webhook_path

    async def on_startup(bot: Bot) -> None:
        await user_storage.init()
        await bot.set_webhook(webhook_url, drop_pending_updates=True)

    async def on_shutdown(bot: Bot) -> None:
        await bot.delete_webhook()
        await bot.session.close()

    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dispatcher, bot=bot).register(app, path=settings.webhook_path)
    setup_application(app, dispatcher, bot=bot)
    web.run_app(app, host=settings.web_host, port=settings.web_port)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    if settings.bot_mode == "webhook":
        run_webhook()
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
