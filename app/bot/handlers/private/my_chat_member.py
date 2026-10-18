import logging
from contextlib import suppress

from aiogram import Bot, Router
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatMemberUpdated

from app.bot.chats.topic import notify
from app.config import Config
from app.storage import UserData, UserStorage

logger = logging.getLogger(__name__)
router = Router()


@router.my_chat_member()
async def handler(update: ChatMemberUpdated, bot: Bot, config: Config, users: UserStorage, user_data: UserData) -> None:
    state = update.new_chat_member.status
    member = state == ChatMemberStatus.MEMBER
    logger.info("User %s: %s the bot", user_data.id, "unblocked" if member else "blocked")
    user_data = await users.patch_user(user_data.id, state=state) or user_data

    # Without a topic in the current group there is nowhere to report, and the General topic is not the place for it
    if not user_data.has_topic(config.bot.GROUP_ID):
        return
    # Admins may have deleted the topic
    with suppress(TelegramBadRequest):
        await notify(bot, config, user_data, "user_restarted_bot" if member else "user_stopped_bot")
