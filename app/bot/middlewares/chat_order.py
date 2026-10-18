import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY, EventContext
from aiogram.types import TelegramObject, Update

Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]
Key = tuple[int, int | None]
# Reactions and buttons don't wait: one in a long flood wait must not hold up the chat's messages
ORDERED = {"message", "edited_message"}


# Updates of a chat (a topic in the group) run concurrently. `note` sees them before any await, so in Telegram's order;
# `wait` holds a handler back until the earlier messages and edits of its chat are handled.
class ChatOrder:
    def __init__(self) -> None:
        self.in_progress: defaultdict[Key, set[int]] = defaultdict(set)
        self.changed = asyncio.Condition()

    async def note(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        key = self.key(data)
        if not isinstance(event, Update) or event.event_type not in ORDERED or key is None:
            return await handler(event, data)
        self.in_progress[key].add(event.update_id)
        try:
            return await handler(event, data)
        finally:
            self.in_progress[key].discard(event.update_id)
            if not self.in_progress[key]:
                del self.in_progress[key]
            async with self.changed:
                self.changed.notify_all()

    # Inner: after filters and the album aggregator, whose other parts never get here and hold nothing up
    async def wait(self, handler: Handler, event: TelegramObject, data: dict[str, Any]) -> Any:
        key, update_id = self.key(data), data["event_update"].update_id
        if key is None:
            return await handler(event, data)
        async with self.changed:
            await self.changed.wait_for(lambda: min(self.in_progress.get(key, {update_id})) >= update_id)
        return await handler(event, data)

    async def idle(self) -> None:
        async with self.changed:
            await self.changed.wait_for(lambda: not self.in_progress)

    @staticmethod
    def key(data: dict[str, Any]) -> Key | None:
        context: EventContext = data[EVENT_CONTEXT_KEY]
        return None if context.chat_id is None else (context.chat_id, context.thread_id)
