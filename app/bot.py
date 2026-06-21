"""Wires the bot together: Bot, Dispatcher, dependency injection and routers."""

import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import settings
from app.database import Database
from app.handlers import admin, user
from app.logging_setup import setup_logging

logger = logging.getLogger(__name__)


def create_dispatcher(db: Database) -> Dispatcher:
    dp = Dispatcher()
    # Anything stored on the dispatcher is injected into handlers that declare a
    # parameter with the same name (here: `db`).
    dp["db"] = db
    dp.include_router(user.router)
    dp.include_router(admin.router)
    return dp


async def _run() -> None:
    setup_logging()
    db = Database(settings.db_path)
    await db.connect()
    bot = Bot(token=settings.bot_token)
    dp = create_dispatcher(db)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot started")
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()
        logger.info("Bot stopped")


def run() -> None:
    asyncio.run(_run())
