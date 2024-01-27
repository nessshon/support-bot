from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.handlers.private.windows import Window
from app.bot.manager import Manager
from app.bot.utils.redis.models import UserData

router = Router()
router.message.filter(F.chat.type == "private")


@router.message(Command("start"))
async def handler(message: Message, manager: Manager, user_data: UserData) -> None:
    """
    Handles the /start command.

    If the user has already selected a language, displays the main menu window.
    Otherwise, prompts the user to select a language.

    :param message: Message object.
    :param manager: Manager object.
    :param user_data: UserData object.
    :return: None
    """
    if user_data.language_code:
        await Window.main_menu(manager)
    else:
        await Window.select_language(manager)
    await manager.delete_message(message)


@router.message(Command("language"))
async def handler(message: Message, manager: Manager, user_data: UserData) -> None:
    """
    Handles the /language command.

    If the user has already selected a language, prompts the user to select a new language.
    Otherwise, prompts the user to select a language.

    :param message: Message object.
    :param manager: Manager object.
    :param user_data: UserData object.
    :return: None
    """
    if user_data.language_code:
        await Window.change_language(manager)
    else:
        await Window.select_language(manager)
    await manager.delete_message(message)


@router.message(Command("source"))
async def handler(message: Message, manager: Manager) -> None:
    """
    Handles the /source command.

    :param message: Message object.
    :param manager: Manager object.
    :return: None
    """
    text = manager.text_message.get("source")
    await manager.send_message(text)
    await manager.delete_message(message)
