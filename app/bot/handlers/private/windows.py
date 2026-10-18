import asyncio
import time

from aiogram.types import InlineKeyboardButton as Button
from aiogram.types import InlineKeyboardMarkup as Markup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold

from app import captcha
from app.bot.manager import Manager
from app.texts import SUPPORTED_LANGUAGES


def select_language_markup() -> Markup:
    builder = InlineKeyboardBuilder()
    builder.row(
        *[Button(text=text, callback_data=callback_data) for callback_data, text in SUPPORTED_LANGUAGES.items()],
        width=2,
    )
    return builder.as_markup()


class Window:
    @staticmethod
    async def select_language(manager: Manager) -> None:
        text = manager.text_message.get("select_language")
        text = text.format(full_name=hbold(manager.user.full_name))
        reply_markup = select_language_markup()
        await manager.send_message(text, reply_markup=reply_markup)

    @staticmethod
    async def main_menu(manager: Manager) -> None:
        text = manager.text_message.get("main_menu")
        text = text.format(full_name=hbold(manager.user.full_name))
        await manager.send_message(text)

    @staticmethod
    async def change_language(manager: Manager) -> None:
        text = manager.text_message.get("change_language")
        reply_markup = select_language_markup()
        await manager.send_message(text, reply_markup=reply_markup)

    @staticmethod
    async def captcha(manager: Manager, text_code: str = "captcha") -> None:
        solution, image = await asyncio.to_thread(captcha.generate)
        await manager.users.set_captcha(manager.user.id, solution, time.time())
        await manager.send_photo(image, manager.text_message.get(text_code))
