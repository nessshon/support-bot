from aiogram import F, Router
from aiogram.filters import MagicData

from . import command, message

id_router = command.id_router

router = Router()
for observer in (router.message, router.edited_message):
    observer.filter(MagicData(F.event_chat.id == F.config.bot.GROUP_ID), F.message_thread_id.is_not(None))
router.include_routers(command.router, message.router)
