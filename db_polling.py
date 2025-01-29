import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable
import aiosqlite
import db
import gdrive
from bot_utils import send_file, send_log_tg_message, send_text
from constants import BASE_DIR, DATABASE, GOOGLE_API_MAX_CONCURRENT_REQUESTS, GOOGLE_API_MAX_TIMEOUT
from hd_parse import parse_links_to_files
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


async def run_as_async(fn: Callable, args_list: list[tuple]) -> list[Any]:
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=GOOGLE_API_MAX_CONCURRENT_REQUESTS) as executor:
        tasks = [loop.run_in_executor(executor, fn, *args) for args in args_list]
        return await asyncio.wait_for(asyncio.gather(*tasks), timeout=GOOGLE_API_MAX_TIMEOUT)


async def send_files(user_id, files):
    await send_text(
        user_id, 'Файли опису готові. Їх можна відкрити у Word або запустити та скопіювати текст через Ctrl+A, Ctrl+C'
    )
    for file in files:
        await send_file(user_id, file)


async def get_google_documents_links(files):
    google_links = []
    try:
        google_links = await run_as_async(fn=gdrive.upload_file_as_document, args_list=[(file,) for file in files])
    except asyncio.TimeoutError:
        logger.error('Google API TimeoutError')
    except Exception as e:
        logger.error(f'Error uploading file to Google Drive: {e}')
    # google_links = [gdrive.upload_file_as_document(file) for file in files]   # Alternative sync way
    return google_links


async def send_google_documents_links(user_id, google_links):
    await send_text(
        user_id,
        'Відповідні посилання на Google Docs. Ви можете редагувати їх онлайн '
        'та одразу передавати клієнтам посилання на них:',
    )
    for g_link in google_links:
        await send_text(user_id, g_link)


async def db_polling() -> None:
    logger.info('Starting DB polling...')
    db = await aiosqlite.connect(DATABASE)
    db.row_factory = aiosqlite.Row
    try:
        while True:
            cursor = await db.execute('SELECT id, user_id, link FROM links WHERE is_processed = 0 ORDER BY id ASC')
            row = await cursor.fetchone()
            if not row:
                await asyncio.sleep(5)
                continue

            db_id, user_id, link = row['id'], row['user_id'], row['link']
            logger.info(f'Got link from db {link} for user {user_id}')

            files = await parse_links_to_files([link])
            google_links = await get_google_documents_links(files)

            if files:
                await send_files(user_id, files)
                await db.execute('UPDATE users SET trial_links = (trial_links + 1) WHERE user_id = ?', (user_id,))
                await db.commit()
            else:
                await send_text(user_id, 'Не вдалося отримати жодного опису')
                logger.error(f'FAILED TO GET ANY DESCRIPTION FOR LINK {link}')

            if google_links:
                await send_google_documents_links(user_id, google_links)

            await db.execute('UPDATE links SET is_processed = 1 WHERE id = ?', (db_id,))
            await db.commit()
            logger.info(f'Link {link} was marked as processed. Waiting for next link...')
    finally:
        await db.close()


async def main() -> None:
    try:
        init_logger()
        await db.db_init()
        await db_polling()
    except:
        logger.exception(f'Upper level Exception in {__file__}')
    finally:
        await logger.complete()


if __name__ == '__main__':
    asyncio.run(main())
