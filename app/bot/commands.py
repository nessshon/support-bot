from aiogram import Bot
from aiogram.types import BotCommandScopeAllPrivateChats, BotCommand, BotCommandScopeAllGroupChats


async def setup(bot: Bot) -> None:
    """
    Set up bot commands for various scopes and languages.

    :param bot: The Bot object.
    """
    # Define bot commands for different languages
    commands = {
        "en": [
            BotCommand(command="start", description="Restart bot"),
            BotCommand(command="source", description="Source code"),
            BotCommand(command="language", description="Change language"),
        ],
        "ru": [
            BotCommand(command="start", description="Перезапустить бота"),
            BotCommand(command="source", description="Исходники бота"),
            BotCommand(command="language", description="Изменить язык"),
        ]
    }
    group_commands = {
        "en": [
            BotCommand(command="ban", description="Block/Unblock a user"),
            BotCommand(command="silent", description="Activate/Deactivate silent Mode"),
            BotCommand(command="information", description="User information"),
        ],
        "ru": [
            BotCommand(command="ban", description="Заблокировать/Разблокировать пользователя"),
            BotCommand(command="silent", description="Активировать/Деактивировать тихий режим"),
            BotCommand(command="information", description="Информация о пользователе"),
        ]
    }

    # Set commands for all private chats in English language
    await bot.set_my_commands(
        commands=commands["en"],
        scope=BotCommandScopeAllPrivateChats(),
    )
    # Set commands for all private chats in Russian language
    await bot.set_my_commands(
        commands=commands["ru"],
        scope=BotCommandScopeAllPrivateChats(),
        language_code="ru",
    )
    # Set commands for all group chats in English language
    await bot.set_my_commands(
        commands=group_commands["en"],
        scope=BotCommandScopeAllGroupChats(),
    )
    # Set commands for all group chats in Russian language
    await bot.set_my_commands(
        commands=group_commands["ru"],
        scope=BotCommandScopeAllGroupChats(),
        language_code="ru"
    )


async def delete(bot: Bot) -> None:
    """
    Delete bot commands for various scopes and languages.

    :param bot: The Bot object.
    """

    # Delete commands for all private chats in any language
    await bot.delete_my_commands(
        scope=BotCommandScopeAllPrivateChats(),
    )
    # Delete commands for all private chats in Russian language
    await bot.delete_my_commands(
        scope=BotCommandScopeAllPrivateChats(),
        language_code="ru",
    )
    # Delete commands for all group chats in any language
    await bot.delete_my_commands(
        scope=BotCommandScopeAllGroupChats(),
    )
    # Delete commands for all group chats in Russian language
    await bot.delete_my_commands(
        scope=BotCommandScopeAllGroupChats(),
        language_code="ru",
    )
