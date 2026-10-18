import asyncio
import logging
from itertools import groupby
from weakref import WeakValueDictionary

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramRetryAfter
from aiogram.types import Message

from app.bot.chats import relay
from app.bot.chats.topic import get_or_create_topic
from app.bot.exceptions import TopicException
from app.config import Config
from app.storage import UserData, UserStorage

logger = logging.getLogger(__name__)

RETRY_INTERVAL = 60
# The group takes about 20 messages a minute (Bot API FAQ), the queues of several users share it
RETRY_PAUSE = 3
CHUNK = 100

# The handler and the background retry must not send one queue twice or create two topics
_locks: WeakValueDictionary[int, asyncio.Lock] = WeakValueDictionary()


def _lock(user_id: int) -> asyncio.Lock:
    lock = _locks.get(user_id)
    if lock is None:
        lock = _locks[user_id] = asyncio.Lock()
    return lock


# A queued message has only its ID left, so its kind goes with it: a forwarded one is forwarded again
def queue_entry(message: Message) -> str:
    return f"{message.message_id}:f" if message.forward_origin else str(message.message_id)


def _entry_message_id(entry: str) -> int:
    return int(entry.partition(":")[0])


async def queued_message_ids(users: UserStorage, user_id: int) -> set[int]:
    return {_entry_message_id(entry) for entry in await users.queue_get(user_id)}


async def deliver(bot: Bot, users: UserStorage, config: Config, user_data: UserData, messages: list[Message]) -> None:
    async with _lock(user_data.id):
        user_data = await get_or_create_topic(bot, users, config, user_data)
        try:
            await _send(bot, users, config, user_data, messages)
        except TelegramBadRequest as ex:
            # The topic was deleted in the group
            if "message thread not found" not in ex.message:
                raise
            logger.info("User %s: topic %s not found, creating a new one", user_data.id, user_data.message_thread_id)
            user_data = await get_or_create_topic(
                bot, users, config, user_data, broken_thread_id=user_data.message_thread_id
            )
            await _send(bot, users, config, user_data, messages)


# Creates the topic and sends the queue
async def flush(bot: Bot, users: UserStorage, config: Config, user_data: UserData) -> None:
    await deliver(bot, users, config, user_data, [])


async def _send(bot: Bot, users: UserStorage, config: Config, user_data: UserData, messages: list[Message]) -> None:
    group_id, thread_id = config.bot.GROUP_ID, user_data.message_thread_id
    queue = sorted(await users.queue_get(user_data.id), key=_entry_message_id)
    for forwarded, run in groupby(queue, key=lambda entry: entry.endswith(":f")):
        entries = list(run)
        for i in range(0, len(entries), CHUNK):
            chunk = entries[i : i + CHUNK]
            message_ids = [_entry_message_id(entry) for entry in chunk]
            try:
                await relay.copy_ids(bot, users, user_data.id, message_ids, group_id, thread_id, forwarded=forwarded)
            except TelegramBadRequest as ex:
                # All deleted by the user (checked live, copy and forward): dropped, or the chunk would block the queue
                if "there are no messages to forward" not in ex.message:
                    raise
                logger.warning("User %s: %s queued message(s) were deleted", user_data.id, len(chunk))
            # Removed chunk by chunk: a failure later does not send this chunk again
            await users.queue_remove(user_data.id, chunk)
    if queue:
        logger.info("User %s: %s queued message(s) delivered", user_data.id, len(queue))
    if messages:
        await relay.send(bot, users, messages, group_id, thread_id)


async def retry_queues(bot: Bot, users: UserStorage, config: Config) -> None:
    while True:
        await asyncio.sleep(RETRY_INTERVAL)
        try:
            user_ids = await users.queued_users()
        except Exception:
            logger.exception("Queues not read")
            continue
        for user_id in user_ids:
            await retry_queue(bot, users, config, user_id)
            await asyncio.sleep(RETRY_PAUSE)


async def retry_queue(bot: Bot, users: UserStorage, config: Config, user_id: int) -> None:
    try:
        user_data = await users.get_user(user_id)
        if user_data is None or user_data.is_banned:
            await users.queue_clear(user_id)
            return
        await flush(bot, users, config, user_data)
    except TelegramRetryAfter as ex:
        logger.warning("User %s: queue waits, retry after %s s", user_id, ex.retry_after)
        await asyncio.sleep(ex.retry_after)
    except (TopicException, TelegramAPIError) as ex:
        # The developer was told when the message was queued; the next round tries again
        logger.warning("User %s: queue not delivered: %r", user_id, ex)
    except Exception:
        # The loop must outlive a bug or a Redis hiccup: one user's queue does not stop the others
        logger.exception("User %s: queue retry failed", user_id)
