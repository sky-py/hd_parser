import aiosqlite
from constants import DATABASE, TRIAL_LINKS_LIMIT
from loguru import logger


async def db_init() -> None:
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS links
                        (id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        link TEXT,
                        is_processed INTEGER DEFAULT 0)""")

        await db.execute("""CREATE TABLE IF NOT EXISTS users
                        (user_id INTEGER PRIMARY KEY,
                        name TEXT,
                        is_blocked INTEGER DEFAULT 1,
                        is_trial INTEGER DEFAULT 0,
                        trial_links INTEGER DEFAULT 0)""")

        await db.execute('CREATE INDEX IF NOT EXISTS idx_links_user_id ON links(user_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_links_is_processed ON links(is_processed)')

        await db.commit()


async def add_user(user_id: int, name: str) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        try:
            await db.execute('INSERT INTO users (user_id, name) VALUES (?, ?)', (user_id, name))
            await db.commit()
        except aiosqlite.IntegrityError:
            logger.info(f'User {name} with id {user_id} was already added to the database')
        else:
            logger.info(f'User {name} with id {user_id} was added to the database')


async def authorize_user(user_id: int, trial_access: bool = False) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            'UPDATE users SET is_blocked = 0, is_trial = ? WHERE user_id = ?', (int(trial_access), user_id)
        )
        await db.commit()
    logger.info(f'User id {user_id} - {"trial " if trial_access else ""}access to the bot was granted')


async def is_user_authorized(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        async with await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return bool(row and not row['is_blocked'])


async def is_user_limit_valid(user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        async with await db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return not row['is_trial'] or row['trial_links'] < TRIAL_LINKS_LIMIT  # type: ignore


async def add_link(user_id: int, link: str) -> int:
    """
    Add new link to links table and return number of links in queue
    """
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('INSERT INTO links (user_id, link) VALUES (?, ?)', (user_id, link))
        await db.commit()
        logger.info(f'User {user_id} added link {link} to db')
        async with db.execute('SELECT COUNT(*) FROM links WHERE is_processed = 0') as cursor:
            count = await cursor.fetchone()
            return count[0]  # type: ignore


async def get_authorized_users() -> list[tuple[int, str, int]]:
    """
    Retrieves a list of authorized users from the database.

    :return: A list of tuples, where each tuple contains:
             - user_id (int): The unique ID of the user
             - name (str): The name of the user
             - is_trial (int): The trial status of the user (0 or 1)
    :rtype: list[tuple[int, str, int]]
    """
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        async with await db.execute('SELECT user_id, name, is_trial FROM users WHERE is_blocked = 0') as cursor:
            return [(int(row['user_id']), row['name'], row['is_trial']) for row in await cursor.fetchall()]


async def block_user(user_id) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
        await db.commit()
    logger.info(f'User {user_id} was blocked')


async def full_access_user(user_id) -> None:
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('UPDATE users SET is_blocked = 0, is_trial = 0 WHERE user_id = ?', (user_id,))
        await db.commit()
    logger.info(f'User {user_id} full access was granted')
