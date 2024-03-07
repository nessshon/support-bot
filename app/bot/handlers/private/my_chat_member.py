from aiogram import Router, F
from aiogram.types import ChatMemberUpdated

from app.bot.utils.redis import RedisStorage
from app.bot.utils.redis.models import UserData

router = Router()
router.my_chat_member.filter(F.chat.type == "private")


@router.my_chat_member()
async def handle_chat_member_update(
        update: ChatMemberUpdated,
        redis: RedisStorage,
        user_data: UserData
) -> None:
    """
    Handle updates of the bot chat member status.

    :param update: ChatMemberUpdated object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    # Update the user's state based on the new chat member status
    user_data.state = update.new_chat_member.status
    await redis.update_user(user_data.id, user_data)
