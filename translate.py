import asyncio
from pathlib import Path
from typing import Optional
from bs_stuff import split_html_text
from constants import (
    GLOBAL_MAX_TRIES,
    OPENAI_API_KEY,
    OPENAI_API_MAX_CONCURRENT_REQUESTS,
    OPENAI_API_MAX_TIMEOUT,
    html_page_begin,
    html_page_end,
)
from loguru import logger
from openai import AsyncOpenAI
from retry import retry

MAX_TOKENS = {'gpt-4o': 16384, 'gpt-4o-mini': 16384}

MODEL = 'gpt-4o-mini'
FRAGMENT_SIZE = int(MAX_TOKENS[MODEL] / 2 * 3.5)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)
semaphore = asyncio.Semaphore(OPENAI_API_MAX_CONCURRENT_REQUESTS)


async def translate(text: str, additional_instructions: str = '') -> str:
    # response = client.chat.completions.with_raw_response.create(
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                'role': 'system',
                'content': 'Ты аналитик по системе Human Design и переводчик с русского на украинский язык',
            },  # <-- This is the system message that provides context to the model
            {
                'role': 'user',
                'content': 'Переведи с русского на украинский язык фрагмент анализа Rave карты клиента '
                '(или союза двух человек) в системе Human Design. '
                'Обязательно сохрани html разметку исходного текста. '
                'В ответе надо указать ИСКЛЮЧИТЕЛЬНО переведенный текст в формате html. ',
            },
            {'role': 'user', 'content': additional_instructions},
            {'role': 'user', 'content': text},
        ],
        timeout=OPENAI_API_MAX_TIMEOUT,
    )
    # print(response.headers.get('X-My-Header'))
    # print(response.parse())  # get the object that `chat.completions.create()` would have returned

    answer = response.choices[0].message.content
    if answer is None:
        raise Exception('The answer from OpenAI is None')
    return answer


@retry(max_tries=GLOBAL_MAX_TRIES)
async def translate_fragment(text: str, additional_instructions: str = '') -> str:
    async with semaphore:
        return await translate(text, additional_instructions)


def get_additional_instructions(text: str) -> str:
    if 'союз' not in text.lower():
        return ''
    people = text.replace('Союз', '').replace('союз', '').split(' и ')
    return (
        f'Данная Rave карта является союзом двух человек - {people[0]} и {people[1]}. '
        f'При переводе поставь их имена в правильный падеж.'
    )


async def translate_file(file: Path, save_as: Optional[Path] = None) -> Path:
    logger.info(f'Start translating {file} ...')
    additional_instructions = get_additional_instructions(file.stem)
    if not save_as:
        save_as = file.with_stem(file.stem + ' UA')
    html = file.read_text(encoding='utf-8')
    fragments = split_html_text(html, FRAGMENT_SIZE)
    logger.info(f'Found {len(fragments)} fragments')
    results = await asyncio.gather(*[translate_fragment(fragment, additional_instructions) for fragment in fragments])
    results = [fragment.strip().removeprefix('```html').removesuffix('```') for fragment in results]
    full_html = html_page_begin + '\n'.join(results) + html_page_end

    save_as.write_text(full_html, encoding='utf-8')
    logger.info(f'Translated file saved as: {save_as}')
    return save_as


if __name__ == '__main__':
    f = Path(r'd:\user\Dropbox\Python\parser_hd_server\out\Союз Аліна Ісакова и Чоловік Аліни.html')
    asyncio.run(translate_file(f))
