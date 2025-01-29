import db
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, KeyboardButton, Message, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_init import bot
from constants import PAGE_PARSE_TIME, TG_ADMINS, TG_OWNER, SITE
from loguru import logger

router = Router()


def make_user_name(entity: Message | CallbackQuery) -> str:
    return f'{entity.from_user.first_name or ""} {entity.from_user.last_name or ""}'.strip()  # type: ignore


@router.message(Command('start'))
async def start(message: Message):
    await db.add_user(user_id=message.from_user.id, name=make_user_name(message))  # type: ignore
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text='Авторизуватись', callback_data='authorization'))
    await message.answer(
        text='Привіт, цей бот допоможе отримати описи по Human Design та перекласти їх на українську мову'
    )
    if not await db.is_user_authorized(message.from_user.id):  # type: ignore
        await message.answer(text='Для початку треба авторизуватись', reply_markup=builder.as_markup())
    else:
        await message.answer(
            text='Ви успішно авторизовані. Для отримання опису надішліть мені '
            'посилання на сторінку сайту. 1 повідомлення = 1 посилання'
        )


@router.message(Command('help'))
async def help_start(message: Message):
    await message.answer(
        text='/start - початок роботи з ботом\n/manage - керування користувачами\n/help - список команд бота'
    )


@router.callback_query(F.data == 'authorization')
async def send_to_authorization(callback: CallbackQuery):
    await callback.message.answer('Ваш запит надіслано на авторизацію')  # type: ignore # message always exists for inline keyboard callbacks
    await callback.answer()

    # callback_data = f'confirmation:{callback.from_user.id}:{user_name}'.encode('utf-8')[:64].decode('utf-8', errors='ignore')
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text='Підтвердити', callback_data=f'confirmation:{callback.from_user.id}'),
        InlineKeyboardButton(text='Пробний доступ', callback_data=f'confirmation_trial:{callback.from_user.id}'),
    )
    for admin_id in TG_ADMINS:
        await bot.send_message(
            chat_id=admin_id,
            text=f'{make_user_name(callback)} запрошує доступ до боту Описів Human Design',
            reply_markup=builder.as_markup(),
        )


@router.message(F.text)
async def main_handler(message: Message):
    logger.debug(f'User {message.from_user.id} sent message: {message.text}')  # type: ignore

    if not await db.is_user_authorized(message.from_user.id):  # type: ignore
        await message.answer('Ви не авторизовані для використання цього боту. Для авторизації надішліть /start')
        return

    if not await db.is_user_limit_valid(message.from_user.id):  # type: ignore
        await message.answer(
            'Ліміт безкоштовних описів вичерпано. Для продовження користування ботом сплатіть абонплату'
        )
        return

    keyboard = None
    if message.from_user.id in TG_ADMINS:  # type: ignore
        buttons = [[KeyboardButton(text='Керування користувачами')]]
        if message.from_user.id == TG_OWNER:  # type: ignore
            buttons.extend([
                [KeyboardButton(text='Загальне повідомлення'), KeyboardButton(text='Скасувати повідомлення')]
            ])
        keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, is_persistent=True)

    if SITE not in message.text:  # type: ignore because of F.text
        await message.answer(text='Хибний формат посилання. Очікую посилання на опис...', reply_markup=keyboard)
    else:
        queue_number = await db.add_link(user_id=message.from_user.id, link=message.text)  # type: ignore
        await message.answer(
            text=f'Посилання додано до черги. Номер в черзі: {queue_number}.\n'
            f'Орієнтований час отримання опису: {queue_number * PAGE_PARSE_TIME} хв.',
            reply_markup=keyboard,
        )


@router.message()
async def unknown(message: Message):
    await message.answer(text='Невідома команда')
