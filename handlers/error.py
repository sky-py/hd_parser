import traceback
from aiogram import Router
from aiogram.types import ErrorEvent
from loguru import logger

router = Router()


@router.errors()
async def error_handler(event: ErrorEvent):
    # Получаем исключение и апдейт из события
    exception = event.exception
    error_message = (
        f'❌ Произошла ошибка!\n\n'
        f'Тип: {type(exception).__name__}\n'
        f'Описание: {str(exception)}\n\n'
        f'Traceback:\n{traceback.format_exc()}\n\n'
    )

    logger.error(error_message)  # logger.exception('Unhandled exception')
