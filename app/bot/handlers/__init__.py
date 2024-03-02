from aiogram import Dispatcher
from aiogram_newsletter.handlers import AiogramNewsletterHandlers

from . import errors
from . import group
from . import private


def include_routers(dp: Dispatcher) -> None:
    """
    Include bot routers.

    :param dp: Dispatcher object.
    :return: None
    """
    dp.include_routers(
        *[
            *group.routers,
            *private.routers,
            errors.router,
        ]
    )
    AiogramNewsletterHandlers().register(dp)


__all__ = [
    "include_routers",
]
