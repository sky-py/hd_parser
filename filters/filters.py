from aiogram import types
from aiogram.filters import BaseFilter
from constants import TG_ADMINS, TG_OWNER


class IsOwner(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id == TG_OWNER  # type: ignore


class IsAdmin(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in TG_ADMINS  # type: ignore
