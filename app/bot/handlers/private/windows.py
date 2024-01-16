from aiogram.utils.markdown import hbold

from app.bot.manager import Manager

from aiogram.types import InlineKeyboardMarkup as Markup
from aiogram.types import InlineKeyboardButton as Button


def select_language_markup() -> Markup:
    """
    Generate an inline keyboard markup for selecting the language.

    :return: InlineKeyboardMarkup
    """
    inline_keyboard = [
        [Button(text="🇷🇺 Русский", callback_data="ru"),
         Button(text="🇬🇧 English", callback_data="en")],
    ]
    return Markup(inline_keyboard=inline_keyboard)


class Window:

    @staticmethod
    async def select_language(manager: Manager) -> None:
        """
        Display the window for selecting the language.

        :param manager: Manager object.
        :return: None
        """
        text = manager.text_message.get("select_language")
        text = text.format(full_name=hbold(manager.user.full_name))
        reply_markup = select_language_markup()
        await manager.send_message(text, reply_markup=reply_markup)

    @staticmethod
    async def main_menu(manager: Manager) -> None:
        """
        Display the main menu window.

        :param manager: Manager object.
        :return: None
        """
        text = manager.text_message.get("main_menu")
        await manager.send_message(text)

    @staticmethod
    async def change_language(manager: Manager) -> None:
        """
        Display the window for changing the language.

        :param manager: Manager object.
        :return: None
        """
        text = manager.text_message.get("change_language")
        reply_markup = select_language_markup()
        await manager.send_message(text, reply_markup=reply_markup)

    @staticmethod
    async def command_source(manager: Manager) -> None:
        """
        Display the window with information about the command source.

        :param manager: Manager object.
        :return: None
        """
        text = manager.text_message.get("command_source")
        await manager.send_message(text)
