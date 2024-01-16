import asyncio

from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from .bot import commands
from .bot.handlers import include_routers
from .bot.middlewares import register_middlewares
from .config import load_config
from .logger import setup_logger


async def on_shutdown(dispatcher: Dispatcher, bot: Bot) -> None:
    """
    Shutdown event handler. This runs when the bot shuts down.

    :param dispatcher: Dispatcher: The bot dispatcher.
    :param bot: Bot: The bot instance.
    """
    # Delete commands and close storage when shutting down
    await commands.delete(bot)
    await dispatcher.storage.close()
    await bot.delete_webhook()
    await bot.session.close()


async def on_startup(bot: Bot) -> None:
    """
    Startup event handler. This runs when the bot starts up.

    :param bot: Bot: The bot instance.
    """
    # Setup commands when starting up
    await commands.setup(bot)


async def main() -> None:
    """
    Main function that initializes the bot and starts the event loop.
    """
    # Load config
    config = load_config()

    # Initialize Redis storage
    storage = RedisStorage.from_url(
        url=config.redis.dsn(),
    )

    # Create Bot and Dispatcher instances
    bot = Bot(
        token=config.bot.TOKEN,
        parse_mode=ParseMode.HTML,
    )
    dp = Dispatcher(
        storage=storage,
        config=config,
        bot=bot,
    )

    # Register startup handler
    dp.startup.register(on_startup)
    # Register shutdown handler
    dp.shutdown.register(on_shutdown)

    # Include routes
    include_routers(dp)
    # Register middlewares
    register_middlewares(dp, config=config, redis=storage.redis)

    # Start the bot
    await bot.delete_webhook()
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    # Set up logging
    setup_logger()
    # Run the bot
    asyncio.run(main())
