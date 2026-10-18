from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY, EventContext
from aiogram.types import TelegramObject, User

from app.bot.manager import Manager
from app.config import Config
from app.storage import UserData, UserStorage
from app.texts import SUPPORTED_LANGUAGES


# `user_data`: the user of the private chat, or the user of a topic in BOT_GROUP_ID; None elsewhere.
# `manager`: the window and texts, for events with a user
class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        users: UserStorage = data["users"]
        config: Config = data["config"]
        context: EventContext = data[EVENT_CONTEXT_KEY]
        user_data = None
        if context.chat and context.chat.type == "private" and context.user:
            user_data = await self.private_user(users, context.user)
        elif context.chat_id == config.bot.GROUP_ID and context.thread_id is not None:
            user_data = await users.get_user_by_topic(context.thread_id, config.bot.GROUP_ID)
        data["user_data"] = user_data

        # Such as a reaction of an anonymous admin: there is no window and no language
        if context.user is None:
            return await handler(event, data)
        language_code: str | None
        if context.chat and context.chat.type != "private":
            language_code = config.bot.GROUP_LANGUAGE
        elif user_data and user_data.language_code:
            language_code = user_data.language_code
        else:
            # Until the user picks a language in the bot
            language_code = context.user.language_code
        data["manager"] = Manager(data, language_code)
        return await handler(event, data)

    @staticmethod
    async def private_user(users: UserStorage, user: User) -> UserData:
        username = f"@{user.username}" if user.username else "-"
        # With one language there is nothing to choose
        language_code = next(iter(SUPPORTED_LANGUAGES)) if len(SUPPORTED_LANGUAGES) == 1 else None

        user_data = await users.get_user(user.id)
        if user_data is None:
            return await users.create_user(
                UserData(
                    message_thread_id=None,
                    message_silent_id=None,
                    message_silent_mode=False,
                    id=user.id,
                    full_name=user.full_name,
                    username=username,
                    created_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S %Z"),
                    language_code=language_code,
                    is_verified=False,
                )
            )

        changed: dict[str, Any] = {}
        if user_data.full_name != user.full_name:
            changed["full_name"] = user.full_name
        if user_data.username != username:
            changed["username"] = username
        if language_code and user_data.language_code != language_code:
            changed["language_code"] = language_code
        if not changed:
            return user_data
        return await users.patch_user(user.id, **changed) or user_data
