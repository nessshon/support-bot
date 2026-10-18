from aiogram import F, Router, flags
from aiogram.filters import MagicData
from aiogram.types import CallbackQuery

from app.bot.handlers.private.windows import Window
from app.bot.manager import Manager
from app.storage import UserData, UserStorage
from app.texts import SUPPORTED_LANGUAGES

router = Router()
router.callback_query.filter(MagicData(~F.user_data.is_banned))


@router.callback_query()
@flags.rate_limit(1)
async def handler(call: CallbackQuery, manager: Manager, users: UserStorage, user_data: UserData) -> None:
    if call.data in SUPPORTED_LANGUAGES:
        await users.patch_user(user_data.id, language_code=call.data)
        manager.text_message.language_code = call.data
        if user_data.is_verified:
            await Window.main_menu(manager)
        else:
            await Window.captcha(manager)

    await call.answer()
