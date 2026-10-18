from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
)

from app.config import Config
from app.texts import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, TextMessage


def menu(language_code: str, prefix: str, names: list[str]) -> list[BotCommand]:
    text_message = TextMessage(language_code)
    return [BotCommand(command=name, description=text_message.get(f"{prefix}_{name}")) for name in names]


# The default language's menu is shown to everyone without a menu of their own language
def menu_language(language_code: str) -> str | None:
    return None if language_code == DEFAULT_LANGUAGE else language_code


async def setup(bot: Bot, config: Config) -> None:
    commands = ["start", "delete"]
    if len(SUPPORTED_LANGUAGES) > 1:
        commands.append("language")
    group_commands = ["ban", "silent", "delete", "information"]

    try:
        for language_code in SUPPORTED_LANGUAGES:
            await bot.delete_my_commands(
                scope=BotCommandScopeChat(chat_id=config.bot.DEV_ID),
                language_code=menu_language(language_code),
            )
    except TelegramBadRequest as ex:
        raise ValueError(f"Chat with DEV_ID {config.bot.DEV_ID} not found.") from ex

    for language_code in SUPPORTED_LANGUAGES:
        await bot.set_my_commands(
            commands=menu(language_code, "command", commands),
            scope=BotCommandScopeAllPrivateChats(),
            language_code=menu_language(language_code),
        )
    await bot.set_my_commands(
        commands=menu(config.bot.GROUP_LANGUAGE, "group_command", group_commands),
        scope=BotCommandScopeAllGroupChats(),
    )
    # The group has one language: commands for a language_code would override it for admins with that language
    for language_code in SUPPORTED_LANGUAGES:
        if language_code != DEFAULT_LANGUAGE:
            await bot.delete_my_commands(scope=BotCommandScopeAllGroupChats(), language_code=language_code)


async def delete(bot: Bot) -> None:
    for language_code in SUPPORTED_LANGUAGES:
        await bot.delete_my_commands(
            scope=BotCommandScopeAllPrivateChats(),
            language_code=menu_language(language_code),
        )
        await bot.delete_my_commands(
            scope=BotCommandScopeAllGroupChats(),
            language_code=menu_language(language_code),
        )
