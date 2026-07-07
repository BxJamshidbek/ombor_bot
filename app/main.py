import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import config
from app.database import init_db
from app.handlers import start, admin, client
from app.services.sheets_service import sheets_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Bot starting...")

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    await init_db()

    try:
        await sheets_service.initialize()
        logger.info("Google Sheets initialized")
    except Exception as e:
        logger.warning("Google Sheets not available: %s", e)

    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(client.router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
