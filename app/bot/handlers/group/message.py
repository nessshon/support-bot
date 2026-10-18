import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
from aiogram.filters import MagicData
from aiogram.types import Message

from app.bot.chats import relay
from app.bot.manager import Manager, delete_later, safe_delete
from app.storage import UserData, UserStorage

logger = logging.getLogger(__name__)
router = Router()
to_user = (MagicData(F.user_data), MagicData(~F.user_data.message_silent_mode))


# Without the right to delete they stay: the start check warns about it
@router.message(F.pinned_message | F.forum_topic_edited | F.forum_topic_closed | F.forum_topic_reopened)
async def handler(message: Message) -> None:
    await safe_delete(message)


# Anonymous admins (a fake bot user) are ignored; an unknown command stays here: a typo must not reach the user
@router.message(F.from_user[F.is_bot.is_(False)], ~F.text.startswith("/"), *to_user)
async def handler(
    message: Message,
    bot: Bot,
    users: UserStorage,
    user_data: UserData,
    manager: Manager,
    album: list[Message] | None = None,
) -> None:
    try:
        await relay.send(bot, users, album or [message], user_data.id, None)
    except TelegramAPIError as ex:
        logger.warning("User %s: message not delivered: %s", user_data.id, ex.message)
        text_code = "blocked_by_user" if isinstance(ex, TelegramForbiddenError) else "message_not_sent"
        delete_later(await message.reply(manager.text_message.get(text_code)))


@router.edited_message(F.from_user[F.is_bot.is_(False)], *to_user)
async def handler(message: Message, bot: Bot, users: UserStorage, album: list[Message] | None = None) -> None:
    for m in album or [message]:
        await relay.edit(bot, users, m)
