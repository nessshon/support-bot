from aiogram import F, Router

from . import callback_query, captcha, command, message, my_chat_member

# The filters of a parent router keep updates from its children (aiogram checks them before propagating)
router = Router()
router.message.filter(F.chat.type == "private")
router.edited_message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")
router.my_chat_member.filter(F.chat.type == "private")
router.include_routers(
    captcha.router,
    command.router,
    message.router,
    callback_query.router,
    my_chat_member.router,
)
