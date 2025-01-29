import db
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from bot_utils import send_tg_message_to_users
from filters.filters import IsOwner

router = Router()


class Mailing(StatesGroup):
    composing_message = State()


@router.message(F.text == 'Загальне повідомлення', IsOwner())
async def email(message: Message, state: FSMContext) -> None:
    await state.set_state(Mailing.composing_message)
    await message.answer('Введіть повідомлення')


@router.message(F.text == 'Скасувати повідомлення', IsOwner())
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text='Надсилання повідомлення скасовано')


@router.message(Mailing.composing_message, IsOwner(), F.text)
async def send_to_all(message: Message, state: FSMContext) -> None:
    users_data = await db.get_authorized_users()
    users = [user_id for user_id, _, _ in users_data]
    await send_tg_message_to_users(*users, text=message.text)  # type: ignore because of F.text
    await state.clear()
