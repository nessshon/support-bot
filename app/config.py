from dataclasses import dataclass
from environs import Env

@dataclass
class BotConfig:
    """
    Класс данных, представляющий конфигурацию для бота.

    Атрибуты:
    - TOKEN (str): Токен бота.
    - DEV_ID (int): ID пользователя-разработчика.
    - GROUP_ID (int): ID группового чата.
    - BOT_EMOJI_ID (str): ID пользовательского эмодзи для темы группы.
    """
    TOKEN: str
    DEV_ID: int
    GROUP_ID: int
    BOT_EMOJI_ID: str

@dataclass
class RedisConfig:
    """
    Класс данных, представляющий конфигурацию для Redis.

    Атрибуты:
    - HOST (str): Хост Redis.
    - PORT (int): Порт Redis.
    - DB (int): Номер базы данных Redis.
    """
    HOST: str
    PORT: int
    DB: int

    def dsn(self) -> str:
        """
        Генерирует DSN (Data Source Name) для подключения к Redis, используя предоставленные хост, порт и базу данных.

        :return: Сгенерированный DSN.
        """
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"

@dataclass
class Config:
    """
    Класс данных, представляющий общую конфигурацию для приложения.

    Атрибуты:
    - bot (BotConfig): Конфигурация бота.
    - redis (RedisConfig): Конфигурация Redis.
    """
    bot: BotConfig
    redis: RedisConfig

def load_config() -> Config:
    """
    Загрузить конфигурацию из переменных окружения и вернуть объект Config.

    :return: Объект Config с загруженной конфигурацией.
    """
    env = Env()
    env.read_env()

    return Config(
        bot=BotConfig(
            TOKEN=env.str("BOT_TOKEN"),
            DEV_ID=env.int("BOT_DEV_ID"),
            GROUP_ID=env.int("BOT_GROUP_ID"),
            BOT_EMOJI_ID=env.str("BOT_EMOJI_ID"),
        ),
        redis=RedisConfig(
            HOST=env.str("REDIS_HOST"),
            PORT=env.int("REDIS_PORT"),
            DB=env.int("REDIS_DB"),
        ),
    )