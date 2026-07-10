import asyncio
import json
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import ErrorEvent
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update

from app.config import config
from app.database import init_db
from app.handlers import start, admin, client
from app.services.sheets_service import sheets_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BOT_TOKEN_MASKED = config.bot_token[:6] + "..." if len(config.bot_token) > 6 else "***"


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response(
        {"ok": True, "service": "ombor_bot", "mode": config.bot_mode}
    )


async def webhook_handler(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]
    dp: Dispatcher = request.app["dp"]

    if request.match_info.get("secret") != config.webhook_secret_path:
        return web.Response(status=404)

    try:
        update = Update.model_validate(
            await request.json(), context={"bot": bot}
        )
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.warning("Webhook update processing error: %s", type(e).__name__)

    return web.Response(status=200)


async def on_startup(app: web.Application) -> None:
    bot = app["bot"]
    webhook_url = config.webhook_base_url + "/webhook/" + config.webhook_secret_path
    await bot.set_webhook(webhook_url)
    logger.info("Webhook set: %s", webhook_url[:40] + "...")
    logger.info(
        "Webhook server listening on %s:%d", config.webapp_host, config.webapp_port
    )


async def on_cleanup(app: web.Application) -> None:
    bot = app["bot"]
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Webhook removed, bot session closed")


async def run_webhook() -> None:
    logger.info("Run mode: webhook")

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

    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    app.router.add_get("/health", health_handler)
    app.router.add_post(
        "/webhook/{secret}", webhook_handler
    )

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config.webapp_host, config.webapp_port)
    await site.start()

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


async def run_polling() -> None:
    logger.info("Run mode: polling")

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
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def main():
    logger.info("Bot starting... (token: %s)", BOT_TOKEN_MASKED)

    if config.bot_mode == "webhook":
        await run_webhook()
    else:
        await run_polling()


if __name__ == "__main__":
    asyncio.run(main())
