import asyncio
from pathlib import Path
from typing import Optional
import constants
from bot_utils import send_log_tg_message
from bs4 import BeautifulSoup, Tag
from bs_stuff import get_soup, purify_soup
from loguru import logger
from page_stuff import (
    clear_audio,
    close_yandex,
    cookies_agree,
    get_bodygraph_image_link,
    log_spam_counter,
    login,
    make_img_tag,
    mouse_top_click,
    scroll_page,
    send_esc,
    simulate_mouse_move,
)
from playwright.async_api import Locator, Page, async_playwright
from retry import retry
from translate import translate_file

constants.OUT_FOLDER.mkdir(parents=True, exist_ok=True)
EXCLUDE_TABS_FRAGMENTS = [text.lower().strip() for text in constants.EXCLUDE_TABS_FRAGMENTS]
EXCLUDE_BUTTONS_FRAGMENTS = [text.lower().strip() for text in constants.EXCLUDE_BUTTONS_FRAGMENTS]


def init_logger() -> None:
    logger.add(
        sink=(constants.BASE_DIR / 'log' / Path(__file__).stem).with_suffix('.log'),
        format='{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}',
        level='INFO',
    )
    logger.add(
        sink=(constants.BASE_DIR / 'log' / (Path(__file__).stem + '_debug')).with_suffix('.log'),
        format='{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}',
        level='DEBUG',
        backtrace=True,
        diagnose=True,
        rotation='1 week',
        retention='1 month',
    )
    logger.add(sink=send_log_tg_message, format='{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}', level='ERROR')


def read_links(file: str | Path) -> list[str]:
    with open(file, mode='r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines() if len(line.strip()) > 5 and not line.startswith('#')]


def extend_links_list(links: list[str]) -> list[str]:
    extended_links = []
    for link in links:
        link = link.replace('pro=1', '')
        extended_links.append(link)
        if 'rave' in link:
            extended_links.append(link.replace('rave', 'phs'))
        if 'child' in link:
            extended_links.append(link.replace('child', 'phs'))

    return extended_links


def make_final_html(full_description: list[str]) -> str:
    html_content = constants.html_page_begin + '\n<br><br>\n'.join(full_description) + constants.html_page_end
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup.find_all(['h1', 'h2', 'h3']):
        tag.wrap(soup.new_tag('span', style='color:red'))

    return soup.prettify()


async def make_file_name(page: Page, link: str) -> str:
    if 'composit' in link:  # cspell:words composit
        fname = await page.locator('h1').inner_text()  # TODO h4 or timestamp
    else:
        fname = await page.title()

    return fname.replace(':', '-').replace('/', '-')


async def click_element(element: Locator) -> None:
    for i in range(2):
        try:
            await element.click(timeout=2000)
            break
        except Exception as e:
            logger.debug(f'ОШИБКА КЛИКА {i}, {e} пробуем снова...')
            await element.scroll_into_view_if_needed(timeout=2000)
            # await page.evaluate("(element) => element.scrollIntoView()", element)
    else:
        raise


async def init_page(page: Page) -> None:
    await asyncio.sleep(2)
    await mouse_top_click(page)
    await clear_audio(page)
    await cookies_agree(page)
    await close_yandex(page)
    await scroll_page(page)


async def get_outer_html(locator: Locator) -> str:
    return await locator.evaluate('element => element.outerHTML')


async def get_button_tag(locator: Locator) -> Tag:
    html = await get_outer_html(locator)
    return get_soup(html).find('button')  # type: ignore


def get_tag_hash(tag: Tag) -> str:
    return '|'.join(f'{key}:{tag.attrs[key]}' for key in sorted(tag.attrs.keys()) if key.startswith('data-'))


async def get_soup_descriptions(page: Page) -> list[BeautifulSoup]:
    # main_sel = '.uk-modal-dialog:has(button.uk-close) '
    main_sel = ''
    ravedatas = await page.locator(f'{main_sel}#ravedata').all()
    descriptions = [
        get_soup(await get_outer_html(ravedata)) for ravedata in ravedatas
    ]  # cspell:words ravedatas ravedata
    more_elements = await page.locator(
        f'{main_sel}#dream-about, {main_sel}#dream-type-wake, {main_sel}#dream-type-sleep'
    ).all()
    if more_elements:
        try:
            descriptions.extend([(get_soup(await get_outer_html(locator))).div.div for locator in more_elements])  # type: ignore
        except Exception as e:
            logger.error(
                f'Failed to get descriptions for #dream-about, #dream-type-wake, #dream-type-sleep locators {e}'
            )
        else:
            logger.debug('Got locators for #dream-about, #dream-type-wake, #dream-type-sleep')
    return descriptions


def is_processed_button(button: str) -> bool:
    if not button.strip():
        return False
    button_lower = button.lower()
    return constants.ALL_BUTTONS or not any(text in button_lower for text in EXCLUDE_BUTTONS_FRAGMENTS)


def is_processed_tab(tab: str) -> bool:
    tab = tab.lower().strip()
    if any(tab in exclude_tab for exclude_tab in EXCLUDE_TABS_FRAGMENTS):
        return False
    digits = ''.join(char for char in tab if char.isdigit())
    return not (len(digits) == 4 and 'текущий' not in tab)


async def parse_tab(page: Page, processed_buttons: set[str], full_description: list[str]) -> None:
    buttons = page.locator('button.uk-button')
    await buttons.first.wait_for(state='attached')
    for i in range(await buttons.count()):
        if not await buttons.nth(i).is_visible():
            continue

        button_hash = get_tag_hash(await get_button_tag(buttons.nth(i)))
        if button_hash in processed_buttons:
            continue

        button_text = await buttons.nth(i).inner_text()
        if not is_processed_button(button_text):
            processed_buttons.add(button_hash)
            continue

        logger.debug(f'Button: {button_text} clicking ...')
        try:
            await click_element(buttons.nth(i))
        except Exception as e:
            logger.error(f'Error clicking button {button_text} {e}')
            continue
        await simulate_mouse_move(page, constants.TAB_SLEEP_TIME)
        bs_descriptions = await get_soup_descriptions(page)
        for soup in bs_descriptions:  # TODO pure html
            soup = purify_soup(soup)
            html = soup.prettify()
            if html not in full_description and 'Временные границы активации' not in html:
                full_description.append(html)

        processed_buttons.add(button_hash)
        await send_esc(page)


@retry(max_tries=constants.GLOBAL_MAX_TRIES)
async def parse_single_page(page: Page, link: str, save_as: Optional[Path] = None) -> Path:
    await page.goto(link)
    await init_page(page)
    if await login(page):
        await page.goto(link)

    file_name = await make_file_name(page, link)
    logger.info(f'START SCARPING PAGE: {file_name} {link}')

    try:
        bodygraph_image_link = await get_bodygraph_image_link(page)
    except Exception as e:
        logger.error(f'Error getting image link: {e}')
        bodygraph_image_link = ''
    else:
        logger.debug(f'Got image link: {bodygraph_image_link}')

    summary_html = [make_img_tag(bodygraph_image_link)] if bodygraph_image_link else []
    processed_buttons = set()

    tabs = await page.locator('li:not(.uk-active).uk-margin-small-bottom a').all()
    await parse_tab(page, processed_buttons, summary_html)

    for tab in tabs:
        tab_text = await tab.inner_text()
        if tab_text.strip() and is_processed_tab(tab_text):
            logger.debug(f'Tab: {tab_text} clicking and scarping...')
            await click_element(tab)
            await simulate_mouse_move(page, 0.5)
            await parse_tab(page, processed_buttons, summary_html)

    await log_spam_counter(page)

    if not save_as:
        save_as = (constants.OUT_FOLDER / file_name).with_suffix('.html')
    save_as.write_text(data=make_final_html(summary_html), encoding='utf-8')
    logger.info(f'Page {link} scarped and saved as: {save_as}')

    return save_as


async def parse_links_to_files(links: list[str]) -> list[Path]:
    links_plus = extend_links_list(links)
    results = []
    translation_tasks = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=constants.HEADLESS)
        context = await browser.new_context(
            storage_state=constants.STORAGE_STATE_PATH if constants.STORAGE_STATE_PATH.exists() else None
        )
        page = await context.new_page()

        if constants.USE_VPN and not constants.USE_GUI:
            await asyncio.sleep(60)  # wait for manual VPN setup

        for link in links_plus:
            try:
                scarped_file = await parse_single_page(page, link)
                results.append(scarped_file)
            except Exception as e:
                logger.error(f'Error parsing link {link}: {e}')
                continue
            else:
                translation_tasks.append(asyncio.create_task(translate_file(scarped_file)))
                await context.storage_state(path=constants.STORAGE_STATE_PATH)

        for task in translation_tasks:
            try:
                translated_file = await task
            except Exception as e:
                logger.error(f'Error translating file : {e}')
                continue
            else:
                results.append(translated_file)

    return results


async def main() -> None:
    try:
        init_logger()
        files = await parse_links_to_files(read_links(constants.LINKS_FILE))
        logger.info(f'Files parsed: {files}')
    except:
        logger.exception(f'Upper level Exception in {__file__}')
    finally:
        await logger.complete()


if __name__ == '__main__':
    asyncio.run(main())
