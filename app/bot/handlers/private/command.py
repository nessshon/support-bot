from aiogram import Bot, F, Router, flags
from aiogram.filters import Command, MagicData
from aiogram.types import Message

from app.bot.chats import relay
from app.bot.handlers.private.windows import Window
from app.bot.manager import Manager, delete_later, safe_delete
from app.storage import UserData, UserStorage

router = Router()
router.message.filter(MagicData(~F.user_data.is_banned))


@router.message(Command("start"))
@flags.rate_limit(2)
async def handler(message: Message, manager: Manager, user_data: UserData) -> None:
    if user_data.language_code:
        await Window.main_menu(manager)
    else:
        await Window.select_language(manager)
    await safe_delete(message)


@router.message(Command("language"))
@flags.rate_limit(2)
async def handler(message: Message, manager: Manager, user_data: UserData) -> None:
    if user_data.language_code:
        await Window.change_language(manager)
    else:
        await Window.select_language(manager)
    await safe_delete(message)


@router.message(Command("delete"))
@flags.rate_limit(2)
async def handler(message: Message, bot: Bot, users: UserStorage, manager: Manager) -> None:
    text_code = await relay.delete_pair(bot, users, message)
    delete_later(await message.reply(manager.text_message.get(text_code)), message)
