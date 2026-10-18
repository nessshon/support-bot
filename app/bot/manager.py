import asyncio
from contextlib import suppress
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, Message, User

from app.storage import UserStorage
from app.texts import TextMessage

# The text of an old screen that can't be deleted any more
BLANK_SCREEN = "💎"
MESSAGE_EDIT_ERRORS = [
    "message can't be edited",
    "message is not modified",
    "message to edit not found",
    "there is no text in the message to edit",
]
MESSAGE_DELETE_ERRORS = [
    "message can't be deleted",
    "message to delete not found",
]

_background: set[asyncio.Task[None]] = set()


async def safe_delete(message: Message) -> None:
    with suppress(TelegramBadRequest):
        await message.delete()


# In the background: a handler that waits holds up the next updates of its chat, they are handled in order
def delete_later(*messages: Message, delay: float = 5) -> None:
    async def delete() -> None:
        await asyncio.sleep(delay)
        for message in messages:
            await safe_delete(message)

    task = asyncio.create_task(delete())
    # The loop keeps only a weak reference to a task
    _background.add(task)
    task.add_done_callback(_background.discard)


class Manager:
    def __init__(self, data: dict[str, Any], language_code: str | None) -> None:
        self.bot: Bot = data["bot"]
        self.users: UserStorage = data["users"]
        self.user: User = data["event_from_user"]
        self.text_message = TextMessage(language_code)

    async def send_message(self, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
        message = await self.bot.send_message(chat_id=self.user.id, text=text, reply_markup=reply_markup)
        await self.replace_screen(message)

    async def send_photo(self, photo: bytes, caption: str) -> None:
        message = await self.bot.send_photo(
            chat_id=self.user.id,
            photo=BufferedInputFile(photo, filename="photo.png"),
            caption=caption,
        )
        await self.replace_screen(message)

    async def replace_screen(self, message: Message) -> None:
        message_id = await self.users.swap_window(self.user.id, message.message_id)
        if not message_id:
            return
        try:
            await self.bot.delete_message(chat_id=self.user.id, message_id=message_id)
        except TelegramBadRequest as ex:
            # Messages older than 48 hours can't be deleted, the old screen is blanked instead
            if not any(e in ex.message for e in MESSAGE_DELETE_ERRORS):
                return
            try:
                await self.bot.edit_message_text(chat_id=self.user.id, message_id=message_id, text=BLANK_SCREEN)
            except TelegramBadRequest as ex:
                if not any(e in ex.message for e in MESSAGE_EDIT_ERRORS):
                    raise
