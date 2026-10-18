from aiogram import Dispatcher

from . import errors, group, private, reaction


def include_routers(dp: Dispatcher) -> None:
    dp.include_routers(group.id_router, group.router, private.router, reaction.router, errors.router)


__all__ = ["include_routers"]
