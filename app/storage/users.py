import asyncio
import json
import time
from dataclasses import asdict
from typing import Any

from redis.asyncio import Redis

from .models import UserData

USERS = "users"

# Replies, edits and reactions follow the pair for 30 days; /delete is limited to 48 hours by Telegram itself
LINK_TTL = 30 * 24 * 60 * 60
# An unanswered captcha is kept a day; it expires after captcha.TTL anyway
CAPTCHA_KEY_TTL = 24 * 60 * 60

# Records without group_id have their topics in the group the bot first started with
FIRST_GROUP_ID = "config:first_group_id"
QUEUED_USERS = "users_pending"


def topic_key(message_thread_id: int) -> str:
    return f"users_index_{message_thread_id}"


def queue_key(user_id: int) -> str:
    return f"users_pending_{user_id}"


def link_key(chat_id: int, message_id: int) -> str:
    return f"message:{chat_id}:{message_id}"


def reactions_key(chat_id: int, message_id: int) -> str:
    return f"reactions:{chat_id}:{message_id}"


def window_key(user_id: int) -> str:
    return f"window:{user_id}"


def captcha_key(user_id: int) -> str:
    return f"captcha:{user_id}"


class UserStorage:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.first_group_id: int | None = None
        # One write at a time: a /ban and a name update must not undo each other (one process)
        # ponytail: one lock for all users, a Lua script per write if writes become a bottleneck
        self.lock = asyncio.Lock()

    async def init_first_group_id(self, group_id: int) -> None:
        await self.redis.set(FIRST_GROUP_ID, group_id, nx=True)
        self.first_group_id = int(await self.redis.get(FIRST_GROUP_ID))

    async def get_user(self, user_id: int) -> UserData | None:
        raw = await self.redis.hget(USERS, str(user_id))
        if raw is None:
            return None
        user_data = UserData(**json.loads(raw))
        if user_data.group_id is None and user_data.message_thread_id is not None:
            user_data.group_id = self.first_group_id
        return user_data

    # Topic numbers repeat across groups and old index entries are not removed, so the record is checked
    async def get_user_by_topic(self, message_thread_id: int, group_id: int) -> UserData | None:
        for user_id in await self.redis.hkeys(topic_key(message_thread_id)):
            user_data = await self.get_user(int(user_id))
            if user_data and user_data.message_thread_id == message_thread_id and user_data.group_id == group_id:
                return user_data
        return None

    # A record that already exists is kept: two first updates of a new user may come together
    async def create_user(self, user_data: UserData) -> UserData:
        async with self.lock:
            await self.redis.hsetnx(USERS, str(user_data.id), json.dumps(asdict(user_data)))
        return await self.get_user(user_data.id) or user_data

    async def patch_user(self, user_id: int, **fields: Any) -> UserData | None:
        async with self.lock:
            raw = await self.redis.hget(USERS, str(user_id))
            if raw is None:
                return None
            record = {**json.loads(raw), **fields}
            await self.redis.hset(USERS, str(user_id), json.dumps(record))
            if record["message_thread_id"] is not None:
                await self.redis.hset(topic_key(record["message_thread_id"]), str(user_id), "1")
        return await self.get_user(user_id)

    # Undelivered messages: "{id}", or "{id}:f" for a forwarded one; QUEUED_USERS lists who has a queue
    async def queue_add(self, user_id: int, entries: list[str]) -> None:
        async with self.lock:
            await self.redis.rpush(queue_key(user_id), *entries)
            await self.redis.sadd(QUEUED_USERS, user_id)

    async def queue_get(self, user_id: int) -> list[str]:
        return [entry.decode() for entry in await self.redis.lrange(queue_key(user_id), 0, -1)]

    async def queue_remove(self, user_id: int, entries: list[str]) -> None:
        async with self.lock:
            for entry in entries:
                await self.redis.lrem(queue_key(user_id), 1, entry)
            if not await self.redis.exists(queue_key(user_id)):
                await self.redis.srem(QUEUED_USERS, user_id)

    async def queue_clear(self, user_id: int) -> None:
        async with self.lock:
            await self.redis.delete(queue_key(user_id))
            await self.redis.srem(QUEUED_USERS, user_id)

    async def queued_users(self) -> list[int]:
        return [int(user_id) for user_id in await self.redis.smembers(QUEUED_USERS)]

    # A message in the user's chat and its pair in the topic, both ways
    async def add_links(self, from_chat_id: int, from_ids: list[int], to_chat_id: int, to_ids: list[int]) -> None:
        # forwardMessages and copyMessages skip messages they can't send: the pairs are unknown then
        if len(from_ids) != len(to_ids):
            return
        async with self.redis.pipeline(transaction=False) as pipe:
            for from_id, to_id in zip(from_ids, to_ids, strict=True):
                pipe.set(link_key(from_chat_id, from_id), f"{to_chat_id}:{to_id}", ex=LINK_TTL)
                pipe.set(link_key(to_chat_id, to_id), f"{from_chat_id}:{from_id}", ex=LINK_TTL)
            await pipe.execute()

    async def get_link(self, chat_id: int, message_id: int) -> tuple[int, int] | None:
        raw = await self.redis.get(link_key(chat_id, message_id))
        if raw is None:
            return None
        link_chat_id, link_message_id = raw.decode().split(":")
        return int(link_chat_id), int(link_message_id)

    # The private chat is one window: returns the previous screen, which the new one replaces
    async def swap_window(self, user_id: int, message_id: int) -> int | None:
        previous = await self.redis.set(window_key(user_id), message_id, get=True)
        return int(previous) if previous else None

    async def set_captcha(self, user_id: int, solution: str, issued_at: float) -> None:
        key = captcha_key(user_id)
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.hset(key, mapping={"solution": solution, "issued_at": issued_at})
            pipe.expire(key, CAPTCHA_KEY_TTL)
            await pipe.execute()

    async def get_captcha(self, user_id: int) -> tuple[str, float] | None:
        stored = await self.redis.hgetall(captcha_key(user_id))
        if not stored:
            return None
        return stored[b"solution"].decode(), float(stored[b"issued_at"])

    async def clear_captcha(self, user_id: int) -> None:
        await self.redis.delete(captcha_key(user_id))

    # Each person's reaction on a paired message, so that the pair shows the latest one still set
    async def update_reaction(
        self, chat_id: int, message_id: int, user_id: int, reaction: dict[str, str] | None
    ) -> dict[str, str] | None:
        key = reactions_key(chat_id, message_id)
        async with self.redis.pipeline(transaction=True) as pipe:
            if reaction is None:
                pipe.hdel(key, str(user_id))
            else:
                pipe.hset(key, str(user_id), json.dumps([time.time(), reaction]))
                pipe.expire(key, LINK_TTL)
            pipe.hvals(key)
            values = (await pipe.execute())[-1]
        if not values:
            return None
        return max((json.loads(value) for value in values), key=lambda item: item[0])[1]
