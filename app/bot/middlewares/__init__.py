from aiogram import Dispatcher

from .album import MediaGroupAggregatorMiddleware
from .chat_order import ChatOrder
from .throttling import ThrottlingMiddleware
from .user import UserMiddleware


def register_middlewares(dp: Dispatcher) -> None:
    chat_order_middleware = dp["chat_order"] = ChatOrder()
    # First: nothing awaits before it, so updates are noted in the order Telegram sent them
    dp.update.outer_middleware.register(chat_order_middleware.note)

    # Before the handlers' data, so that handlers get the whole album as `album: list[Message]`
    dp.update.outer_middleware.register(MediaGroupAggregatorMiddleware())

    dp.update.outer_middleware.register(UserMiddleware())

    # One instance: commands and buttons share the limits
    throttling_middleware = ThrottlingMiddleware()
    dp.message.middleware.register(throttling_middleware)
    dp.callback_query.middleware.register(throttling_middleware)

    # After the throttling: a dropped message does not wait for its turn
    dp.message.middleware.register(chat_order_middleware.wait)
    dp.edited_message.middleware.register(chat_order_middleware.wait)


__all__ = ["register_middlewares"]
