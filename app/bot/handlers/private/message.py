import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.filters import MagicData
from aiogram.types import Message

from app.bot.chats import relay
from app.bot.chats.delivery import deliver, queue_entry, queued_message_ids
from app.bot.exceptions import TopicException
from app.bot.manager import Manager, delete_later
from app.config import Config
from app.storage import UserData, UserStorage

logger = logging.getLogger(__name__)
# Messages before the captcha are handled by the captcha router
router = Router()
router.message.filter(MagicData(~F.user_data.is_banned))
router.edited_message.filter(MagicData(~F.user_data.is_banned), MagicData(F.user_data.is_verified))


# The copy in the topic follows the edit; without a pair (older than the link, deleted by admins) the user is told
@router.edited_message()
async def handle_edited_message(
    message: Message,
    bot: Bot,
    users: UserStorage,
    user_data: UserData,
    manager: Manager,
    album: list[Message] | None = None,
) -> None:
    messages = album or [message]
    not_edited = [m.message_id for m in messages if not await relay.edit(bot, users, m)]
    # A queued message is sent later as it is then, the edit included
    if set(not_edited) - await queued_message_ids(users, user_data.id):
        delete_later(await message.reply(manager.text_message.get("message_edited")))


@router.message()
async def handle_incoming_message(
    message: Message,
    bot: Bot,
    config: Config,
    users: UserStorage,
    user_data: UserData,
    manager: Manager,
    album: list[Message] | None = None,
) -> None:
    await send_to_topic(message, album or [message], bot, config, users, user_data, manager)


# What can't be delivered now waits in the queue for the background retry or the user's next message
async def send_to_topic(
    message: Message,
    messages: list[Message],
    bot: Bot,
    config: Config,
    users: UserStorage,
    user_data: UserData,
    manager: Manager,
) -> None:
    try:
        await deliver(bot, users, config, user_data, messages)
    except (TopicException, TelegramAPIError) as ex:
        await users.queue_add(user_data.id, [queue_entry(m) for m in messages])
        await message.reply(manager.text_message.get("message_queued"))
        # Telegram allows ~20 messages per minute in a group: busy, not broken, the developer is not told
        if isinstance(ex, TelegramRetryAfter):
            logger.warning(
                "User %s: %s message(s) queued, retry after %s s", user_data.id, len(messages), ex.retry_after
            )
            return
        logger.warning("User %s: %s message(s) queued: %s", user_data.id, len(messages), type(ex).__name__)
        raise
