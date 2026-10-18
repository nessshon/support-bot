from aiogram import Bot, F, Router
from aiogram.filters import MagicData
from aiogram.types import MessageReactionUpdated

from app.bot.chats import relay
from app.config import Config
from app.storage import UserData, UserStorage

router = Router()


@router.message_reaction(F.chat.type == "private", MagicData(~F.user_data.is_banned))
async def handler(
    event: MessageReactionUpdated, bot: Bot, config: Config, users: UserStorage, user_data: UserData
) -> None:
    pair = await users.get_link(event.chat.id, event.message_id)
    if pair is None or pair[0] != config.bot.GROUP_ID:
        return
    await relay.copy_reaction(bot, users, event, user_data.id, pair)


# Like their messages, reactions of anonymous admins (no user) are ignored
@router.message_reaction(MagicData(F.event_chat.id == F.config.bot.GROUP_ID), F.user)
async def handler(event: MessageReactionUpdated, bot: Bot, users: UserStorage) -> None:
    pair = await users.get_link(event.chat.id, event.message_id)
    if pair is None or event.user is None:
        return
    # The pair is in the user's private chat, whose ID is the user's
    user_data = await users.get_user(pair[0])
    if user_data is None or user_data.message_silent_mode:
        return
    await relay.copy_reaction(bot, users, event, event.user.id, pair)
