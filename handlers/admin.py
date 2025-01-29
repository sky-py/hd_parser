import db
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_init import bot
from bot_utils import send_text
from filters.filters import IsAdmin

router = Router()


@router.callback_query(F.data.startswith('confirmation'), IsAdmin())
async def confirm_access(callback: CallbackQuery):
    data = callback.data.split(':')  # type: ignore
    user_id = int(data[1])
    if await db.is_user_authorized(user_id=user_id):
        await callback.message.answer('Доступ вже було надано')  # type: ignore
    else:
        await db.authorize_user(user_id=user_id, trial_access='trial' in callback.data)  # type: ignore
        await bot.send_message(
            chat_id=user_id,
            text='Ви успішно авторизовані. Для отримання опису надішліть мені '
            'посилання на сторінку сайту. 1 повідомлення = 1 посилання',
        )
        await callback.message.answer(f'{"Пробний" if "trial" in callback.data else "Повний"} доступ надано')  # type: ignore
    await callback.answer()


@router.message(F.text.in_(['Керування користувачами', '/manage']), IsAdmin())
async def block(message: Message):
    users = await db.get_authorized_users()
    for user_id, user_name, is_trial in users:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text='Блокувати', callback_data=f'block:{user_id}'))
        if is_trial:
            builder.add(InlineKeyboardButton(text='Повний доступ  ', callback_data=f'full_access:{user_id}'))
        await message.answer(text=f'{user_name}', reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('block:'), IsAdmin())
async def block_user(callback: CallbackQuery):
    data = callback.data.split(':')  # type: ignore
    user_id = int(data[1])
    await db.block_user(user_id=user_id)
    await callback.message.answer('Користувача було заблоковано')  # type: ignore
    await callback.answer()


@router.callback_query(F.data.startswith('full_access:'), IsAdmin())
async def full_access(callback: CallbackQuery):
    data = callback.data.split(':')  # type: ignore
    user_id = int(data[1])
    await db.full_access_user(user_id=user_id)
    await callback.message.answer('Користувачу було надано повний доступ.')  # type: ignore
    await callback.answer()
    await send_text(user_id, 'Вам було надано повний доступ до боту.')
