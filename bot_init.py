from aiogram import Bot
from constants import TG_TOKEN

bot = Bot(token=TG_TOKEN)


async def close_bot_session():
    if hasattr(bot, 'session') and bot.session:
        await bot.session.close()
