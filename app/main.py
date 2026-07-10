import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import ErrorEvent
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


async def global_error_handler(event: ErrorEvent) -> None:
    logger.error(
        "Unhandled update error: %s: %s",
        type(event.exception).__name__,
        event.exception,
        exc_info=(
            type(event.exception),
            event.exception,
            event.exception.__traceback__,
        ),
    )
    try:
        update = event.update
        if update and update.message:
            await update.message.answer(
                "Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring."
            )
        elif update and update.callback_query:
            await update.callback_query.message.answer(
                "Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring."
            )
    except Exception:
        logger.exception("Failed to send error notification to user")


async def wait_for_telegram(bot: Bot, max_attempts: int = 12) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            me = await bot.get_me(request_timeout=15)
            bot._me = me
            logger.info("Connected to Telegram as @%s", me.username)
            return
        except TelegramNetworkError as e:
            logger.warning(
                "Telegram connection failed (%s/%s): %s",
                attempt,
                max_attempts,
                e,
            )
            await asyncio.sleep(5)

    raise RuntimeError("Telegram API is unavailable after repeated attempts")


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

    dp.errors()(global_error_handler)

    try:
        await wait_for_telegram(bot)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
