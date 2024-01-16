import asyncio
import logging
import traceback

from aiogram import Router, F
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent, BufferedInputFile
from aiogram.utils.markdown import hcode, hbold

from app.bot.manager import Manager
from app.bot.utils.exceptions import CreateForumTopicException, NotEnoughRightsException

router = Router()


@router.errors(F.exception.message.contains("query is too old"))
async def query_too_old(_: ErrorEvent) -> None:
    """
    Handles errors related to outdated queries ("query is too old").

    :param _: ErrorEvent object.
    :return: None
    """


@router.errors(ExceptionTypeFilter(NotEnoughRightsException))
async def not_enough_rights_error(event: ErrorEvent, manager: Manager) -> None:
    """
    Handles errors related to not having enough rights to perform a specific action.

    :param event: ErrorEvent object.
    :param manager: Manager object.
    :return: None
    """
    logging.exception(f'Update: {event.update}\nException: {event.exception}')
    print(event.exception.args)
    await manager.bot.send_message(
        manager.config.bot.DEV_ID,
        NotEnoughRightsException.message,
    )


@router.errors(ExceptionTypeFilter(CreateForumTopicException))
async def create_forum_topic_error(event: ErrorEvent, manager: Manager) -> None:
    """
    Handles errors related to creating a forum topic.

    :param event: ErrorEvent object.
    :param manager: Manager object.
    :return: None
    """
    logging.exception(f'Update: {event.update}\nException: {event.exception}')

    await manager.bot.send_message(
        manager.config.bot.DEV_ID,
        CreateForumTopicException.message,
    )


@router.errors()
async def telegram_api_error(event: ErrorEvent, manager: Manager) -> None:
    """
    Handles generic errors related to the Telegram API.

    :param event: ErrorEvent object.
    :param manager: Manager object.
    :return: None
    """
    logging.exception(f'Update: {event.update}\nException: {event.exception}')

    # Prepare data for document
    update_json = event.update.model_dump_json(indent=2, exclude_none=True)
    exc_text, exc_name = str(event.exception), type(event.exception).__name__

    # Send document with error details
    document_data = traceback.format_exc().encode()
    document_name = f'error_{event.update.update_id}.txt'

    document = BufferedInputFile(document_data, filename=document_name)
    caption = f'{hbold(exc_name)}:\n{hcode(exc_text[:1024 - len(exc_name) - 2])}'
    message = await manager.bot.send_document(manager.config.bot.DEV_ID, document, caption=caption)

    # Send update_json in chunks
    for text in [update_json[i:i + 4096] for i in range(0, len(update_json), 4096)]:
        await asyncio.sleep(.1)
        await message.reply(hcode(text))
