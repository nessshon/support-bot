from dataclasses import dataclass

from environs import Env

from app.texts import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


@dataclass
class BotConfig:
    TOKEN: str
    DEV_ID: int
    GROUP_ID: int
    BOT_EMOJI_ID: str
    GROUP_LANGUAGE: str


@dataclass
class RedisConfig:
    HOST: str
    PORT: int
    DB: int
    USERNAME: str | None = None
    PASSWORD: str | None = None


@dataclass
class Config:
    bot: BotConfig
    redis: RedisConfig


def load_config() -> Config:
    env = Env()
    env.read_env()

    group_language = env.str("BOT_GROUP_LANGUAGE", None)
    if group_language and group_language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"BOT_GROUP_LANGUAGE must be one of {', '.join(SUPPORTED_LANGUAGES)}, got {group_language!r}")

    return Config(
        bot=BotConfig(
            TOKEN=env.str("BOT_TOKEN"),
            DEV_ID=env.int("BOT_DEV_ID"),
            GROUP_ID=env.int("BOT_GROUP_ID"),
            BOT_EMOJI_ID=env.str("BOT_EMOJI_ID"),
            GROUP_LANGUAGE=group_language or DEFAULT_LANGUAGE,
        ),
        redis=RedisConfig(
            HOST=env.str("REDIS_HOST"),
            PORT=env.int("REDIS_PORT"),
            DB=env.int("REDIS_DB"),
            # An empty value in .env means no authentication
            USERNAME=env.str("REDIS_USERNAME", None) or None,
            PASSWORD=env.str("REDIS_PASSWORD", None) or None,
        ),
    )
