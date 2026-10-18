import asyncio
import logging
from typing import Any

from aiogram import Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware, NextRequestMiddlewareType
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType

logger = logging.getLogger(__name__)

ATTEMPTS = 3
MAX_WAIT = 60


class RetryMiddleware(BaseRequestMiddleware):
    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Any:
        for attempt in range(1, ATTEMPTS):
            try:
                return await make_request(bot, method)
            except TelegramRetryAfter as ex:
                if ex.retry_after > MAX_WAIT:
                    raise
                logger.warning("%s: retry after %s s, attempt %s", type(method).__name__, ex.retry_after, attempt)
                await asyncio.sleep(ex.retry_after)
        return await make_request(bot, method)
