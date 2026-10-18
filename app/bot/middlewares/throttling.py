import math
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import CallbackQuery, Chat, Message, TelegramObject, User
from cachetools import TTLCache

from app.bot.manager import Manager, delete_later, safe_delete

LIMIT = 5
PERIOD = 10


# Private chat only, an album counts as one; `@flags.rate_limit(seconds)`: one call per `seconds`
class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.messages: TTLCache[int, list[float]] = TTLCache(maxsize=10_000, ttl=PERIOD)
        self.warned: TTLCache[int, None] = TTLCache(maxsize=10_000, ttl=PERIOD)
        self.flagged: dict[float, TTLCache[tuple[int, int], None]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any | None:
        chat: Chat | None = data.get("event_chat")
        user: User | None = data.get("event_from_user")
        if chat is None or chat.type != "private" or user is None:
            return await handler(event, data)

        rate_limit = get_flag(data, "rate_limit")
        if rate_limit is not None:
            cache = self.flagged.setdefault(rate_limit, TTLCache(maxsize=10_000, ttl=rate_limit))
            key = (user.id, id(data["handler"].callback))
            if key in cache:
                await self.drop(event)
                return None
            cache[key] = None
            return await handler(event, data)

        if isinstance(event, Message):
            now = time.monotonic()
            times = [t for t in self.messages.get(user.id, []) if now - t < PERIOD]
            if len(times) >= LIMIT:
                seconds = math.ceil(times[0] + PERIOD - now)
                await self.warn(event, data["manager"], user.id, seconds)
                return None
            self.messages[user.id] = [*times, now]

        return await handler(event, data)

    @staticmethod
    async def drop(event: TelegramObject) -> None:
        if isinstance(event, CallbackQuery):
            await event.answer()
        elif isinstance(event, Message):
            await safe_delete(event)

    async def warn(self, message: Message, manager: Manager, user_id: int, seconds: int) -> None:
        # Once per period, so that a flood of messages does not turn into a flood of replies
        if user_id in self.warned:
            return
        self.warned[user_id] = None

        text = manager.text_message.get("too_many_messages").format(seconds=seconds)
        delete_later(await message.reply(text))
