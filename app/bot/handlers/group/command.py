import logging
from contextlib import suppress

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, MagicData
from aiogram.types import Message
from aiogram.utils.markdown import hcode

from app.bot.chats import relay
from app.bot.chats.topic import user_details
from app.bot.manager import Manager, delete_later
from app.storage import UserData, UserStorage

logger = logging.getLogger(__name__)

id_router = Router()
id_router.message.filter(F.chat.type.in_(["group", "supergroup"]))


@id_router.message(Command("id"))
async def handler(message: Message) -> None:
    await message.reply(hcode(message.chat.id))


router = Router()
known_user = MagicData(F.user_data)


@router.message(Command("silent"), known_user)
async def handler(message: Message, bot: Bot, users: UserStorage, user_data: UserData, manager: Manager) -> None:
    if user_data.message_silent_mode:
        await message.reply(manager.text_message.get("silent_mode_disabled"))
        # Without an ID Telegram unpins the chat's latest pinned message, which may be another user's card
        if user_data.message_silent_id:
            with suppress(TelegramBadRequest):
                await bot.unpin_chat_message(chat_id=message.chat.id, message_id=user_data.message_silent_id)
        await users.patch_user(user_data.id, message_silent_mode=False, message_silent_id=None)
        logger.info("User %s: silent mode off", user_data.id)
        return

    msg = await message.reply(manager.text_message.get("silent_mode_enabled"))
    # The pinned reply shows the mode at the top of the topic
    with suppress(TelegramBadRequest):
        await msg.pin(disable_notification=True)
    await users.patch_user(user_data.id, message_silent_mode=True, message_silent_id=msg.message_id)
    logger.info("User %s: silent mode on", user_data.id)


@router.message(Command("information"), known_user)
async def handler(message: Message, user_data: UserData, manager: Manager) -> None:
    text = manager.text_message.get("user_information")
    await message.reply(text.format_map(user_details(user_data, manager.text_message)))


@router.message(Command("ban"), known_user)
async def handler(message: Message, users: UserStorage, user_data: UserData, manager: Manager) -> None:
    banned = not user_data.is_banned
    await users.patch_user(user_data.id, is_banned=banned)
    logger.info("User %s: %s", user_data.id, "banned" if banned else "unbanned")
    await message.reply(manager.text_message.get("user_blocked" if banned else "user_unblocked"))


@router.message(Command("delete"))
async def handler(message: Message, bot: Bot, users: UserStorage, manager: Manager) -> None:
    text_code = await relay.delete_pair(bot, users, message)
    # An admin deletes any support message, not only their own
    if text_code == "message_not_found":
        text_code = "admin_message_not_found"
    delete_later(await message.reply(manager.text_message.get(text_code)), message)
