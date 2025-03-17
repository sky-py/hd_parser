import os
from pathlib import Path
from dotenv import load_dotenv


def get_env(var: str) -> str:
    v = os.getenv(var)
    if not v:
        raise ValueError(f'Environment variable {var} is not set')
    return v


BASE_DIR = Path(__file__).parent

OUT_FOLDER = BASE_DIR / 'out'
LINKS_FILE = BASE_DIR / 'links.txt'
STORAGE_STATE_PATH = BASE_DIR / 'state.json'
DATABASE = BASE_DIR / 'database.db'
GOOGLE_CREDENTIALS = BASE_DIR / 'credentials.json'

load_dotenv('.env')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SITE = get_env('SITE')
LOGIN = get_env('LOGIN')
PASSWORD = get_env('PASSWORD')
TG_TOKEN = get_env('TG_TOKEN')
TG_OWNER = int(get_env('TG_OWNER'))
TG_ADMINS = [int(user) for user in get_env('TG_ADMINS').split(',') if user]
TG_MAX_TRIES = 3
TG_MAX_MESSAGE_LENGTH = 4096
DO_SEND_TO_BOT = True

OPENAI_API_MAX_CONCURRENT_REQUESTS = 5
OPENAI_API_MAX_TIMEOUT = 300

GOOGLE_API_MAX_CONCURRENT_REQUESTS = 4
GOOGLE_API_MAX_TIMEOUT = 30

USE_GUI = False
HEADLESS = not USE_GUI
USE_VPN = False  # no need for GUI or VPN already present or VPS

PAGE_PARSE_TIME = 12  # min
TAB_SLEEP_TIME = 1.5  # seconds
GLOBAL_MAX_TRIES = 2

TRIAL_LINKS_LIMIT = 1

EXCLUDE_TABS_FRAGMENTS = ['rave карта', 'дизайн', 'личность', 'ложное я', 'семья', 'общество',
                          'композит', 'возврат солнца', ]

ALL_BUTTONS = False
EXCLUDE_BUTTONS_FRAGMENTS = ['и подробнее на', 'удалить', 'сохранить', 'telegram', 'совместимость с', 'выйти',
                             'временные границы', 'профессиональный', 'простой']


html_page_begin = '''
<!DOCTYPE html>
    <html lang="ru-ru" http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <head>
            <meta charset="UTF-8">
            <title>Human Design</title>
        </head>
    <body>
'''

html_page_end = '</body> </html>'
