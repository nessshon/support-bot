from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatMemberUpdated
from aiogram.utils.markdown import hlink

from app.bot.manager import Manager
from app.bot.utils import create_forum_topic
from app.bot.utils.redis import RedisStorage
from app.bot.utils.redis.models import UserData

router = Router()
router.my_chat_member.filter(F.chat.type == "private")


@router.my_chat_member()
async def handle_chat_member_update(
        update: ChatMemberUpdated,
        manager: Manager,
        redis: RedisStorage,
        user_data: UserData
) -> None:
    """
    Handle updates of the bot chat member status.

    :param update: ChatMemberUpdated object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :return: None
    """
    # Update the user's state based on the new chat member status
    user_data.state = update.new_chat_member.status

    # Generate a URL for the user's profile
    url = f"https://t.me/{user_data.username}" if user_data.username else f"tg://user?id={user_data.id}"

    # Get the appropriate text based on the user's state
    text = manager.text_message.get("user_started_bot" if user_data.state == "member" else "user_stopped_bot")

    async def send_message():
        # Send a message to the group chat with information about the user's status
        await update.bot.send_message(
            chat_id=manager.config.bot.GROUP_ID,
            text=text.format(name=hlink(user_data.full_name, url)),
            message_thread_id=user_data.message_thread_id,
        )

    try:
        await send_message()
    except TelegramBadRequest as ex:
        if "message thread not found" in ex.message:
            # If the message thread is not found, create a new forum topic
            user_data.message_thread_id = await create_forum_topic(
                update.bot, manager.config, user_data.full_name,
            )
            await send_message()
        else:
            raise
    finally:
        # Update user data in Redis
        await redis.update_user(user_data.id, user_data)
