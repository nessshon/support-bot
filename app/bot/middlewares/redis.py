import asyncio
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, User, Chat
from redis.asyncio import Redis

from app.bot.utils.create_forum_topic import create_forum_topic
from app.bot.utils.redis import RedisStorage
from app.bot.utils.redis.models import UserData
from app.bot.utils.texts import SUPPORTED_LANGUAGES

from app.config import Config


class RedisMiddleware(BaseMiddleware):
    """
    Middleware for integrating Redis storage with Aiogram.

    Args:
        redis (Redis): The Redis instance for data storage.
    """

    def __init__(self, redis: Redis) -> None:
        """
        Initializes the RedisMiddleware instance.

        :param redis: The Redis instance for data storage.
        """
        self.redis = redis

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        """
        Call the middleware.

        :param handler: The handler function.
        :param event: The Telegram event.
        :param data: Additional data.
        :return: The result of the handler function.
        """
        # Create an instance of RedisStorage using the provided Redis instance
        redis = RedisStorage(self.redis)
        # Retrieve the bot configuration from data
        config: Config = data.get("config")

        # Extract the chat and user objects from data
        chat: Chat = data.get("event_chat")
        user: User = data.get("event_from_user")

        # Check if the chat type is private and the user object is not None
        if chat.type == "private" and user is not None:
            # Retrieve user data from Redis based on user ID
            user_redis = await redis.get_user(user.id)
            user_data = user_redis or UserData(
                message_thread_id=None,
                message_silent_id=None,
                message_silent_mode=False,
                is_banned=False,
                id=user.id,
                full_name=user.full_name,
                username=f"@{user.username}" if user.username else "-",
            )

            if user_redis is None:
                _ = asyncio.create_task(create_forum_topic_and_set_message_thread_id(
                    event.bot, user, redis, config, user_data,
                ))
            else:
                user_data.full_name = user.full_name
                user_data.username = f"@{user.username}" if user.username else "-"

            if len(SUPPORTED_LANGUAGES.keys()) == 1:
                # If only one language is supported, set user language_code to the first language
                user_data.language_code = list(SUPPORTED_LANGUAGES.keys())[0]

            # Update user data in Redis
            await redis.update_user(user.id, user_data)
        else:
            # For group chats or if the user object is None, set user_data to None
            user_data = None

        # Add redis and user_data to data for use in subsequent handlers
        data["redis"] = redis
        data["user_data"] = user_data

        # Call the handler function with the event and data
        return await handler(event, data)


async def create_forum_topic_and_set_message_thread_id(
        bot: Bot, user: User, redis: RedisStorage, config: Config, user_data: UserData,
):
    try:
        # If user data is not found, create a forum topic and initialize user data
        message_thread_id = await create_forum_topic(
            bot, config, user.full_name,
        )
        # Wait for 1 seconds for the topic to be created
        await asyncio.sleep(1)
    except Exception as e:
        await bot.send_message(config.bot.DEV_ID, str(e))
        logging.exception(e)
        return None

    user_data.message_thread_id = message_thread_id,
    await redis.update_user(user.id, user_data)
