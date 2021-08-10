# подключение библиотек для парсинга
import requests
from bs4 import BeautifulSoup


def parse():
    html = requests.get('https://parksirius.ru/').text
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='list-item')

    events = []
    for item in items:
        name = item.find('div', class_='col-lg-10 col-md-9 col-sm-12 col-xs-12')
        if name is not None:
            events.append(name.get_text().replace('\n', ''))
    return events
