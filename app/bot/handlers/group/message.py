import asyncio
from typing import Optional

from aiogram import Router, F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import MagicData
from aiogram.types import Message
from aiogram.utils.markdown import hlink

from app.bot.manager import Manager
from app.bot.types.album import Album
from app.bot.utils.redis import RedisStorage

router = Router()
router.message.filter(
    MagicData(F.event_chat.id == F.config.bot.GROUP_ID),  # type: ignore
    F.chat.type.in_(["group", "supergroup"]),
    F.message_thread_id.is_not(None),
)


@router.message(F.forum_topic_created)
async def handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    await asyncio.sleep(3)
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data: return None  # noqa

    # Generate a URL for the user's profile
    url = f"https://t.me/{user_data.username[1:]}" if user_data.username != "-" else f"tg://user?id={user_data.id}"

    # Get the appropriate text based on the user's state
    text = manager.text_message.get("user_started_bot")

    message = await message.bot.send_message(
        chat_id=manager.config.bot.GROUP_ID,
        text=text.format(name=hlink(user_data.full_name, url)),
        message_thread_id=user_data.message_thread_id
    )

    # Pin the message
    await message.pin()


@router.message(F.pinned_message | F.forum_topic_edited | F.forum_topic_closed | F.forum_topic_reopened)
async def handler(message: Message) -> None:
    """
    Delete service messages such as pinned, edited, closed, or reopened forum topics.

    :param message: Message object.
    :return: None
    """
    await message.delete()


@router.message(F.media_group_id, F.from_user[F.is_bot.is_(False)])
@router.message(F.media_group_id.is_(None), F.from_user[F.is_bot.is_(False)])
async def handler(message: Message, manager: Manager, redis: RedisStorage, album: Optional[Album] = None) -> None:
    """
    Handles user messages and sends them to the respective user.
    If silent mode is enabled for the user, the messages are ignored.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param album: Album object or None.
    :return: None
    """
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data: return None  # noqa

    if user_data.message_silent_mode:
        # If silent mode is enabled, ignore all messages.
        return

    text = manager.text_message.get("message_sent_to_user")

    try:
        if not album:
            await message.copy_to(chat_id=user_data.id)
        else:
            await album.copy_to(chat_id=user_data.id)

    except TelegramAPIError as ex:
        if "blocked" in ex.message:
            text = manager.text_message.get("blocked_by_user")

    except (Exception,):
        text = manager.text_message.get("message_not_sent")

    # Reply to the edited message with the specified text
    msg = await message.reply(text)
    # Wait for 5 seconds before deleting the reply
    await asyncio.sleep(5)
    # Delete the reply to the edited message
    await msg.delete()
