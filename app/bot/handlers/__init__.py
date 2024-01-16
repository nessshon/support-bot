from aiogram import Dispatcher

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


__all__ = [
    "include_routers",
]
