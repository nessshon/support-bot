import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from redis.asyncio import Redis

from app.bot import commands
from app.bot.chats import delivery
from app.bot.chats.topic import check_group
from app.bot.handlers import include_routers
from app.bot.middlewares import register_middlewares
from app.bot.middlewares.chat_order import ChatOrder
from app.bot.middlewares.retry_after import RetryMiddleware
from app.config import Config, load_config
from app.storage import UserStorage
from app.texts import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)
# Under docker's 10 s between the stop and the kill
SHUTDOWN_WAIT = 8


async def on_startup(dispatcher: Dispatcher, bot: Bot, config: Config, users: UserStorage) -> None:
    await commands.setup(bot, config)
    dispatcher["queue_retry"] = asyncio.create_task(delivery.retry_queues(bot, users, config))
    logger.info("Group %s, languages %s", config.bot.GROUP_ID, ", ".join(SUPPORTED_LANGUAGES))


async def on_shutdown(dispatcher: Dispatcher, bot: Bot, users: UserStorage, chat_order: ChatOrder) -> None:
    # Handlers still running are cancelled when the bot stops: a message in the middle of its delivery would be lost
    with suppress(TimeoutError):
        await asyncio.wait_for(chat_order.idle(), SHUTDOWN_WAIT)
    retry = dispatcher["queue_retry"]
    retry.cancel()
    with suppress(asyncio.CancelledError):
        await retry
    await commands.delete(bot)
    await users.redis.aclose()


async def main() -> None:
    config = load_config()

    # Credentials go as arguments, not in a URL: special characters in a password break URL parsing
    redis = Redis(
        host=config.redis.HOST,
        port=config.redis.PORT,
        db=config.redis.DB,
        username=config.redis.USERNAME,
        password=config.redis.PASSWORD,
    )
    await redis.ping()

    bot_default = DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True)
    bot = Bot(token=config.bot.TOKEN, default=bot_default)
    bot.session.middleware(RetryMiddleware())
    await check_group(bot, config)

    users = UserStorage(redis)
    await users.init_first_group_id(config.bot.GROUP_ID)

    # No FSM: the bot has no states, its window and captcha live in UserStorage
    dp = Dispatcher(disable_fsm=True, config=config, users=users)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    include_routers(dp)
    register_middlewares(dp)

    await bot.delete_webhook()
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # aiogram logs every handled update at INFO; failed updates are logged at ERROR
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    asyncio.run(main())
