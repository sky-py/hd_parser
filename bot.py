import asyncio
from pathlib import Path
import db
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot_init import bot
from bot_utils import send_log_tg_message
from constants import BASE_DIR
from handlers import admin, common, error, owner
from loguru import logger


def init_logger() -> None:
    logger.add(
        sink=(BASE_DIR / 'log' / Path(__file__).stem).with_suffix('.log'),
        format='{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}',
        level='INFO',
    )
    logger.add(
        sink=(BASE_DIR / 'log' / (Path(__file__).stem + '_debug')).with_suffix('.log'),
        format='{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}',
        level='DEBUG',
        backtrace=True,
        diagnose=True,
        rotation='1 week',
        retention='1 month',
    )
    logger.add(sink=send_log_tg_message, format='{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}', level='ERROR')


async def main():
    try:
        init_logger()
        await db.db_init()
        logger.info('STARTING bot...')
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(error.router)
        dp.include_router(owner.router)
        dp.include_router(admin.router)
        dp.include_router(common.router)
        await dp.start_polling(bot)
    except:
        logger.exception(f'Upper level Exception in {__file__}')
    finally:
        await logger.complete()


if __name__ == '__main__':
    asyncio.run(main())
