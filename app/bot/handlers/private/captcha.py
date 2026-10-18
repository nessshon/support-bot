import time

from aiogram import Bot, F, Router
from aiogram.filters import MagicData
from aiogram.types import Message

from app import captcha
from app.bot.chats.delivery import flush
from app.bot.handlers.private.message import send_to_topic
from app.bot.handlers.private.windows import Window
from app.bot.manager import Manager, safe_delete
from app.config import Config
from app.storage import UserData, UserStorage

router = Router()
router.message.filter(MagicData(F.user_data.is_verified.is_(False)))


# No rate_limit: it would delete the message sent right after the right answer
@router.message()
async def handler(
    message: Message,
    bot: Bot,
    config: Config,
    users: UserStorage,
    user_data: UserData,
    manager: Manager,
    album: list[Message] | None = None,
) -> None:
    # The user was read before the previous update, the right answer, was saved
    user_data = await users.get_user(user_data.id) or user_data
    if user_data.is_verified:
        if not user_data.is_banned:
            await send_to_topic(message, album or [message], bot, config, users, user_data, manager)
        return

    for m in album or [message]:
        await safe_delete(m)

    # The captcha is shown in the chosen language; with one language it is set on the first update
    if not user_data.language_code:
        await Window.select_language(manager)
        return

    solution, issued_at = await users.get_captcha(user_data.id) or (None, 0.0)
    if (message.text or "").startswith("/"):
        text_code = "captcha"
    elif solution is None or message.text is None:
        text_code = "captcha_first"
    elif time.time() - issued_at > captcha.TTL:
        text_code = "captcha_expired"
    elif not captcha.is_correct(message.text, solution):
        text_code = "captcha_wrong"
    else:
        user_data = await users.patch_user(user_data.id, is_verified=True) or user_data
        await users.clear_captcha(user_data.id)
        await Window.main_menu(manager)
        # Right away, so that admins see the new user in the group and can /ban
        await flush(bot, users, config, user_data)
        return

    await Window.captcha(manager, text_code)
