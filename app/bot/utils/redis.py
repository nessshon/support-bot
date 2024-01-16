import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta

from redis.asyncio import Redis


@dataclass
class UserData:
    """Data class representing user information."""
    message_thread_id: int
    message_silent_id: int | None
    message_silent_mode: bool

    id: int
    full_name: str
    username: str | None
    state: str = "member"
    is_banned: bool = False
    language_code: str | None = None
    created_at: str = datetime.now(timezone(timedelta(hours=3))).strftime("%Y-%m-%d %H:%M:%S %Z")

    def to_dict(self) -> dict:
        """
        Converts UserData object to a dictionary.

        :return: Dictionary representation of UserData.
        """
        return asdict(self)


class RedisStorage:
    """Class for managing user data storage using Redis."""

    NAME = "users"

    def __init__(self, redis: Redis) -> None:
        """
        Initializes the RedisStorage instance.

        :param redis: The Redis instance to be used for data storage.
        """
        self.redis = redis

    async def _get(self, name: str, key: str | int) -> bytes | None:
        """
        Retrieves data from Redis.

        :param name: The name of the Redis hash.
        :param key: The key to be retrieved.
        :return: The retrieved data or None if not found.
        """
        async with self.redis.client() as client:
            return await client.hget(name, key)

    async def _set(self, name: str, key: str | int, value: any) -> None:
        """
        Sets data in Redis.

        :param name: The name of the Redis hash.
        :param key: The key to be set.
        :param value: The value to be set.
        """
        async with self.redis.client() as client:
            await client.hset(name, key, value)

    async def _update_index(self, message_thread_id: int, user_id: int) -> None:
        """
        Updates the user index in Redis.

        :param message_thread_id: The ID of the message thread.
        :param user_id: The ID of the user to be updated in the index.
        """
        index_key = f"{self.NAME}_index_{message_thread_id}"
        await self._set(index_key, user_id, "1")

    async def get_by_message_thread_id(self, message_thread_id: int) -> UserData | None:
        """
        Retrieves user data based on message thread ID.

        :param message_thread_id: The ID of the message thread.
        :return: The user data or None if not found.
        """
        user_id = await self._get_user_id_by_message_thread_id(message_thread_id)
        return None if user_id is None else await self.get_user(user_id)

    async def _get_user_id_by_message_thread_id(self, message_thread_id: int) -> int | None:
        """
        Retrieves user ID based on message thread ID.

        :param message_thread_id: The ID of the message thread.
        :return: The user ID or None if not found.
        """
        index_key = f"{self.NAME}_index_{message_thread_id}"
        async with self.redis.client() as client:
            user_ids = await client.hkeys(index_key)
            return int(user_ids[0]) if user_ids else None

    async def get_user(self, id_: int) -> UserData | None:
        """
        Retrieves user data based on user ID.

        :param id_: The ID of the user.
        :return: The user data or None if not found.
        """
        data = await self._get(self.NAME, id_)
        if data is not None:
            decoded_data = json.loads(data)
            return UserData(**decoded_data)
        return None

    async def update_user(self, id_: int, data: UserData) -> None:
        """
        Updates user data in Redis.

        :param id_: The ID of the user to be updated.
        :param data: The updated user data.
        """
        json_data = json.dumps(data.to_dict())
        await self._set(self.NAME, id_, json_data)
        await self._update_index(data.message_thread_id, id_)
