from bs4 import BeautifulSoup


def get_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, 'html.parser')


def purify_soup(soup: BeautifulSoup) -> BeautifulSoup:
    if alert := soup.find('div', class_='uk-alert'):
        alert.decompose()  # type: ignore
    if link := soup.find('a', string=lambda text: 'Мне непонятно о чем здесь написано' in text):
        link.decompose()  # type: ignore
    for tag in soup.find_all():
        tag.attrs = {}
        if tag.name == 'a':
            tag.name = 'p'
    return soup


def split_html_text(html: str, max_fragment_size=30000) -> list[str]:
    soup = get_soup(html)
    start = soup.find('body').find_next()  # type: ignore
    elements = [start] + start.find_next_siblings()  # type: ignore

    fragments = []
    curr_len = 0
    curr_fragment = ''

    for el in elements:
        if curr_len + len(str(el)) <= max_fragment_size:
            curr_len += len(str(el))
            curr_fragment += f'{el}\n'
        else:
            fragments.append(curr_fragment)
            curr_len = len(str(el))
            curr_fragment = str(el)

    fragments.append(curr_fragment)  # the last one
    return fragments
