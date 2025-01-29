from pathlib import Path
from aiogram.types import FSInputFile
from bot_init import bot
from constants import DO_SEND_TO_BOT, TG_MAX_MESSAGE_LENGTH, TG_OWNER, TG_TOKEN
from loguru import logger


async def send_file(user_id: int, file_path: Path) -> None:
    await bot.send_document(chat_id=user_id, document=FSInputFile(file_path))
    logger.info(f'{user_id}: send file {file_path}')


async def send_text(user_id: int, text: str) -> None:
    await bot.send_message(chat_id=user_id, text=text)
    logger.info(f'{user_id}: send message: {text}')


async def send_tg_message_to_users(*users: int, text: str):
    text = text[0:TG_MAX_MESSAGE_LENGTH]
    if not DO_SEND_TO_BOT:
        print('=== TEST MODE === ', text)
        return
    for user in users:
        try:
            await send_text(user, text)
        except Exception as e:
            logger.error(f'Ошибка отправки сообщения пользователю {user} {e}')


async def send_owner_tg_message(text: str):
    text = text[0:TG_MAX_MESSAGE_LENGTH]
    await send_text(TG_OWNER, text)


async def send_log_tg_message(text: str):
    try:
        await send_owner_tg_message(text)
    except:
        import httpx

        with httpx.Client() as client:
            client.get(
                url=f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage',
                params={'chat_id': TG_OWNER, 'text': text[0:TG_MAX_MESSAGE_LENGTH]},
                headers={'Content-Type': 'application/json'},
            )
