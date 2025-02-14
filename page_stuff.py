import asyncio
import random
from constants import LOGIN, PASSWORD, SITE
from loguru import logger
from playwright.async_api import Page


async def refresh_page(page: Page) -> None:
    await page.reload(wait_until='load')


async def scroll_page(page: Page) -> None:
    await page.evaluate('window.scrollTo(0, document.body.scrollHeight);')
    await asyncio.sleep(0.2)
    await page.evaluate('window.scrollTo(0, 0);')
    await asyncio.sleep(0.2)


async def send_esc(page: Page) -> None:
    await page.keyboard.press('Escape')
    await simulate_mouse_move(page, 0.5)


async def mouse_top_click(page: Page) -> None:
    size = page.viewport_size
    if size:
        await page.mouse.click(size['width'] / 2, size['height'] * 0.1)


async def simulate_mouse_move(page: Page, duration: float) -> None:
    try:
        viewport = page.viewport_size
        width = viewport['width']  # type: ignore
        height = viewport['height']  # type: ignore

        movements = int(random.random() * 15 * duration + 5)
        # logger.debug(f"Будет выполнено {movements} движений мыши")

        delay = duration / movements
        for i in range(movements):
            await page.mouse.move(random.randint(0, width), random.randint(0, height))
            await asyncio.sleep(delay)
        # await log_spam_counter(page)
    except Exception as e:
        logger.debug(f'Ошибка при движении мыши: {e}')
        await asyncio.sleep(duration)


async def log_spam_counter(page: Page) -> None:
    try:
        spam_counter = await page.locator('.sitogon_click_counter').first.get_attribute('value')
        logger.debug(f'Количество действий пользователя: {spam_counter}')
    except Exception as e:
        logger.error(f'Ошибка при получении количества действий пользователя: {e}')


async def login(page: Page) -> bool:
    login_link = page.locator("a[href='#login_modal']:has-text('Вход')")
    if await login_link.count() > 0:
        logger.info('Login link found, will try to login...')
        await login_link.click()
        username_input = page.locator('#modlgn-username')  # cspell:ignore modlgn
        password_input = page.locator('#modlgn-passwd')
        checkbox_input = page.locator('#modlgn-remember-modal')
        submit_button = page.locator("input[type='submit'][name='Submit']")
        await submit_button.wait_for()

        await username_input.fill(LOGIN)
        await password_input.fill(PASSWORD)
        await checkbox_input.check()
        await submit_button.click()
        logger.info('Login completed')
        return True
    return False


async def clear_audio(page: Page) -> None:
    try:
        audio = page.locator('#audioDIv-wrapp')
        if await audio.count() > 0:
            await audio.evaluate('element => element.remove()')
    except Exception as e:
        logger.error(f'Failed to clear audio: {e}')


async def cookies_agree(page: Page) -> None:
    try:
        button = page.locator('.cc-dismiss')
        if await button.is_visible(timeout=2000):
            await button.click(timeout=1000)
    except Exception as e:
        logger.error(f'Failed to click cookies button: {e}')


async def close_yandex(page: Page) -> None:
    try:
        button = page.frame_locator('iframe[src*="autofill.yandex.ru/suggest"]').locator(
            'button[data-t="suggest:header:closer"]'
        )
        if await button.is_visible(timeout=5000):
            await button.click(timeout=2000)
        else:
            logger.debug('Yandex button not found')
    except Exception as e:
        logger.error(f'Failed to click Yandex in frame: {e}')


async def get_bodygraph_image_link(page: Page) -> str:
    button = page.locator('a.uk-button', has_text='охранить').filter(has=page.locator(':visible')).first
    href = await button.get_attribute('href')
    return SITE + href  # type: ignore


def make_img_tag(link: str) -> str:
    return f'<div align="center">\n<img src="{link}" alt="" width="500 px">\n</div>'
