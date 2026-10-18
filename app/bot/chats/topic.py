import logging
import re
from contextlib import suppress

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ChatMemberAdministrator, Message
from aiogram.utils.markdown import hbold, hlink

from app.bot.exceptions import CreateForumTopicException, NotAForumException, NotEnoughRightsException
from app.config import Config
from app.storage import UserData, UserStorage
from app.texts import SUPPORTED_LANGUAGES, TextMessage

logger = logging.getLogger(__name__)


# Before any Redis write: a wrong BOT_GROUP_ID would bind the old topics to it for good (config:first_group_id)
async def check_group(bot: Bot, config: Config) -> None:
    group_id = config.bot.GROUP_ID
    try:
        chat = await bot.get_chat(group_id)
        member = await bot.get_chat_member(group_id, bot.id)
    except (TelegramBadRequest, TelegramForbiddenError) as ex:
        raise ValueError(f"BOT_GROUP_ID {group_id}: the bot is not in this group ({ex.message})") from ex
    if not chat.is_forum:
        raise ValueError(f"BOT_GROUP_ID {group_id} is not a group with topics: turn topics on in the group settings")
    if not isinstance(member, ChatMemberAdministrator) or not member.can_manage_topics:
        raise ValueError(f"BOT_GROUP_ID {group_id}: the bot needs to be an admin that can manage topics")
    if not member.can_delete_messages or not member.can_pin_messages:
        logger.warning("Group %s: without the rights to delete and pin messages /delete and pins don't work", group_id)


# Only under delivery's user lock; re-read: the delivery just before may have created the topic
async def get_or_create_topic(
    bot: Bot, users: UserStorage, config: Config, user_data: UserData, broken_thread_id: int | None = None
) -> UserData:
    stored = await users.get_user(user_data.id) or user_data
    if stored.has_topic(config.bot.GROUP_ID) and stored.message_thread_id != broken_thread_id:
        return stored

    message_thread_id = await create_topic(bot, config, stored)
    created = await users.patch_user(
        stored.id,
        message_thread_id=message_thread_id,
        group_id=config.bot.GROUP_ID,
        message_silent_mode=False,
        message_silent_id=None,
    )
    logger.info("User %s: topic %s created", stored.id, message_thread_id)
    created = created or stored
    # The topic is stored already: a failed card must not hold the user's messages back
    try:
        message = await notify(bot, config, created, "user_started_bot")
        with suppress(TelegramBadRequest):
            await message.pin()
    except TelegramAPIError as ex:
        logger.warning("User %s: the card of topic %s not sent: %s", stored.id, message_thread_id, ex)
    return created


async def create_topic(bot: Bot, config: Config, user_data: UserData) -> int:
    # A topic name is 1-128 characters, a full name is up to 129: two names of 64 and a space
    name, fallback = user_data.full_name[:128], f"User {user_data.id}"
    while True:
        try:
            forum_topic = await bot.create_forum_topic(
                config.bot.GROUP_ID, name, icon_custom_emoji_id=config.bot.BOT_EMOJI_ID, request_timeout=30
            )
            return forum_topic.message_thread_id
        except TelegramBadRequest as ex:
            # A name of invisible characters only (Hangul filler, Braille blank, zero-width space) is empty for Telegram
            blank = "TOPIC_TITLE_EMPTY" in ex.message or "name must be non-empty" in ex.message
            if not blank or name == fallback:
                raise _topic_exception(ex) from ex
            logger.warning("User %s: name is blank for Telegram, topic named by ID", user_data.id)
            name = fallback


# Telegram tells the reasons apart only by the text
def _topic_exception(ex: TelegramBadRequest) -> Exception:
    if "not enough rights" in ex.message:
        return NotEnoughRightsException()
    if "not a forum" in ex.message:
        return NotAForumException()
    return CreateForumTopicException()


async def notify(bot: Bot, config: Config, user_data: UserData, text_code: str) -> Message:
    text_message = TextMessage(config.bot.GROUP_LANGUAGE)
    return await bot.send_message(
        chat_id=config.bot.GROUP_ID,
        text=text_message.get(text_code).format_map(user_details(user_data, text_message)),
        message_thread_id=user_data.message_thread_id,
    )


def user_details(user_data: UserData, text_message: TextMessage) -> dict[str, str]:
    none = text_message.get("value_none")
    return {
        "id": str(user_data.id),
        "name": hlink(user_data.full_name, user_data.url),
        "full_name": hbold(user_data.full_name),
        "username": user_data.username if user_data.username and user_data.username != "-" else none,
        "language": SUPPORTED_LANGUAGES.get(user_data.language_code or "", none),
        "state": text_message.get("bot_running" if user_data.state == "member" else "bot_stopped"),
        "is_banned": text_message.get("value_yes" if user_data.is_banned else "value_no"),
        "silent_mode": text_message.get("value_on" if user_data.message_silent_mode else "value_off"),
        # Seconds say nothing to an admin
        "created_at": re.sub(r"(\d\d:\d\d):\d\d", r"\1", user_data.created_at),
    }
