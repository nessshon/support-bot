import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .bot import commands
from .bot.handlers import include_routers
from .bot.middlewares import register_middlewares
from .config import load_config, Config
from .logger import setup_logger

async def on_shutdown(
    apscheduler: AsyncIOScheduler,
    dispatcher: Dispatcher,
    config: Config,
    bot: Bot,
) -> None:
    """
    Обработчик события завершения работы. Выполняется при завершении работы бота.

    :param apscheduler: AsyncIOScheduler: Экземпляр планировщика задач.
    :param dispatcher: Dispatcher: Диспетчер бота.
    :param config: Config: Экземпляр конфигурации.
    :param bot: Bot: Экземпляр бота.
    """
    # Остановить планировщик задач
    apscheduler.shutdown()
    # Удалить команды и закрыть хранилище при завершении работы
    await commands.delete(bot, config)
    await dispatcher.storage.close()
    await bot.delete_webhook()
    await bot.session.close()

async def on_startup(
    apscheduler: AsyncIOScheduler,
    config: Config,
    bot: Bot,
) -> None:
    """
    Обработчик события запуска. Выполняется при запуске бота.

    :param apscheduler: AsyncIOScheduler: Экземпляр планировщика задач.
    :param config: Config: Экземпляр конфигурации.
    :param bot: Bot: Экземпляр бота.
    """
    # Запустить планировщик задач
    apscheduler.start()
    # Настроить команды при запуске
    await commands.setup(bot, config)

async def main() -> None:
    """
    Основная функция, которая инициализирует бота и запускает цикл событий.
    """
    # Загрузить конфигурацию
    config = load_config()

    # Инициализировать планировщик задач
    job_store = RedisJobStore(
        host=config.redis.HOST,
        port=config.redis.PORT,
        db=config.redis.DB,
    )
    apscheduler = AsyncIOScheduler(
        jobstores={"default": job_store},
    )

    # Инициализировать хранилище Redis
    storage = RedisStorage.from_url(
        url=config.redis.dsn(),
    )

    # Создать экземпляры Bot и Dispatcher
    bot = Bot(
        token=config.bot.TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )
    dp = Dispatcher(
        apscheduler=apscheduler,
        storage=storage,
        config=config,
        bot=bot,
    )

    # Зарегистрировать обработчик запуска
    dp.startup.register(on_startup)
    # Зарегистрировать обработчик завершения работы
    dp.shutdown.register(on_shutdown)

    # Включить маршруты
    include_routers(dp)
    # Зарегистрировать промежуточные слои (middlewares)
    register_middlewares(
        dp, config=config, redis=storage.redis, apscheduler=apscheduler
    )

    # Запустить бота
    await bot.delete_webhook()
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if name == "main":
    # Настроить логирование
    setup_logger()
    # Запустить бота
    asyncio.run(main())