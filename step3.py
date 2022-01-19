import requests
from bs4 import BeautifulSoup
import os

# корневой url
ROOT_URL = "https://tululu.org"
# url с научной фантастикой
ROOT_URL_NF = ROOT_URL + "/l55/"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKS_PATH = os.path.join(BASE_DIR, 'books')


def get_books_shortlinks(page=1):
    response = requests.get(f'{ROOT_URL_NF}/{page}/')
    response.raise_for_status()
    b = BeautifulSoup(response.content, 'html.parser').find_all('table', attrs={'class': 'd_book'})
    href = [h.find('a')['href'] for h in b]
    title = [t.find('a')['title'] for t in b]
    return dict(zip(href, title))


def get_maxpage():
    response = requests.get(ROOT_URL_NF)
    response.raise_for_status()
    p = BeautifulSoup(response.content, 'html.parser').find_all('a', attrs={'class': 'npage'})
    return int(p[-1]['href'].split('/')[-2]) if len(p) != 0 else 1


def check_need_path(path=BOOKS_PATH):
    if not os.path.exists(BOOKS_PATH):
        os.mkdir(BOOKS_PATH)
    elif os.path.isfile(BOOKS_PATH):
        print(f'ошибка: в папке есть файл с таким-же именем ({path})')
        return False
    return True


def download(shortlink, filename):
    if not check_need_path(BOOKS_PATH):
        return
    num = ''.join([n for n in shortlink if n.isdigit()])
    if num:
        response = requests.get(f'{ROOT_URL}/txt.php?id={num}')
        response.raise_for_status()
        trantab = str.maketrans(r':\/*?"<>|+%!@', '~~~~~~~~~~~~~')
        fname = os.path.join(BOOKS_PATH, filename.translate(trantab).strip())
        with open(fname, 'wb') as file:
            file.write(response.content)
    return


def download_10():
    if not check_need_path(BOOKS_PATH):
        return
    for num in range(1, 10):
        response = requests.get(f'{ROOT_URL}/txt.php?id={num}')
        response.raise_for_status()
        with open(os.path.join(BOOKS_PATH, f'id{num}.txt'), 'wb') as file:
            file.write(response.content)


# выгрузка 10 книг по ТЗ
def main():
    d = get_books_shortlinks()
    for h in tuple(d.keys())[:10]:
        download(h, d[h])


if __name__ == '__main__':
    download_10()
