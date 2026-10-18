import logging
import traceback

from aiogram import Bot, F, Router
from aiogram.types import BufferedInputFile, ErrorEvent
from aiogram.utils.markdown import hbold, hcode
from cachetools import TTLCache

from app.bot.exceptions import TopicException
from app.config import Config

logger = logging.getLogger(__name__)
router = Router()

# The same error reaches the developer at most once per 10 minutes: a broken group fails every incoming message
_reported: TTLCache[tuple[str, str], None] = TTLCache(maxsize=1_000, ttl=600)


# The button was pressed long ago, there is nothing to answer
@router.errors(F.exception.message.contains("query is too old"))
async def query_too_old(_: ErrorEvent) -> None:
    pass


# Takes bot and config, not manager: the error may come from the middleware that creates it
@router.errors()
async def handler(event: ErrorEvent, bot: Bot, config: Config) -> None:
    exception, update_id = event.exception, event.update.update_id
    # A topic error is a setup problem, its text says what to fix: no traceback
    is_topic = isinstance(exception, TopicException)
    logger.error("Update %s failed: %r", update_id, exception, exc_info=None if is_topic else exception)

    key = (type(exception).__name__, str(exception))
    if key in _reported:
        return
    _reported[key] = None

    if is_topic:
        cause = f"\n{hcode(str(exception.__cause__))}" if exception.__cause__ else ""
        await bot.send_message(config.bot.DEV_ID, f"{exception}{cause}")
        return

    log = "".join(traceback.format_exception(exception))
    log += "\n" + event.update.model_dump_json(indent=2, exclude_none=True)
    document = BufferedInputFile(log.encode(), filename=f"error_{update_id}.txt")
    # A caption is limited to 1024 characters
    caption = f"{hbold(type(exception).__name__)}: {hcode(str(exception)[:900])}"
    await bot.send_document(config.bot.DEV_ID, document, caption=caption)
