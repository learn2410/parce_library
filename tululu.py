import os
import sys
import argparse
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from lxml import etree
from pathvalidate import sanitize_filename

ROOT_URL = "https://tululu.org"
TEXTS_DIR = 'books/'
COVERS_DIR = 'images/'
DESCRIPTION_DIR = 'catalog/'


def check_for_redirect(response):
    if response.is_redirect:
        raise requests.HTTPError('вызвано исключение- редирект')


def download_file(url, filename, folder):
    """Функция для скачивания текстовых и других файлов.
    Args:
        url (str): Cсылка на текст/изображение, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст/изображение.
    """
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    print(response.headers['Content-Type'])
    if 'text/plain' in response.headers['Content-Type']:
        with open(os.path.join(folder, filename), 'w') as file:
            file.write(response.text)
    else:
        with open(os.path.join(folder, filename), 'wb') as file:
            file.write(response.content)


def get_book_page(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)
    return response


def parse_book_page(response):
    content_block = BeautifulSoup(response.content, 'lxml') \
        .find('div', attrs={'id': 'content'})
    dom = etree.HTML(str(content_block))
    text_link = ''.join(dom.xpath('//*/a[starts-with(@href,"/txt.php")]/@href'))
    img_link = ''.join(dom.xpath('//*/div[@class="bookimage"]/a/img/@src'))
    name = ''.join(dom.xpath('//h1/text()')).replace('::', '  ').strip()
    autor = ''.join(dom.xpath('//h1/a/text()')).strip()
    comments = '\n'.join(dom.xpath('//*/div[@class="texts"]/span[@class="black"]/text()')).strip()
    genre = dom.xpath('//*/span[@class="d_book"]/a/text()')
    return {'text_link': text_link,
            'img_link': img_link,
            'name': name,
            'autor': autor,
            'comments': comments,
            'genre': genre,
            }


def download_book(id_number):
    book = parse_book_page(get_book_page(f'{ROOT_URL}/b{id_number}/'))
    book_filename = sanitize_filename(f'{id_number}. {book["name"]}.txt')
    if book["text_link"]:
        download_file(f'{ROOT_URL}{book["text_link"]}', book_filename, TEXTS_DIR)
    else:
        print(f'!!! текст книги {id_number} нельзя скачать')
    img_file = urlparse(ROOT_URL + book['img_link']).path.split('/')[-1]
    if not os.path.exists(f'{COVERS_DIR}{img_file}'):
        download_file(f'{ROOT_URL}{book["img_link"]}', sanitize_filename(img_file), COVERS_DIR)
    with open(os.path.join(DESCRIPTION_DIR, book_filename), 'w') as file:
        file.write('\n'.join([
            f'id: {id_number}',
            f'название: {book["name"]}',
            f'автор: {book["autor"]}',
            f'жанр: {str(book["genre"])}',
            f'обложка: {img_file}',
            f'комментарии:\n{book["comments"]}',
        ]))
    print(f'---- скачана книга {id_number} -----')
    print('название:', book['name'])
    print('Автор:', book['autor'], '\n')
    return True


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('start_id', nargs='?', default=1, type=int)
    parser.add_argument('end_id', nargs='?', default=1, type=int)
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args(sys.argv[1:])
    if args.end_id <= args.start_id:
        args.end_id = args.start_id
        print(f'скачивание книги с номером {args.start_id}')
    else:
        print(f'скачивание книг с номерами от {args.start_id} до {args.end_id}')
    for work_dir in [TEXTS_DIR, COVERS_DIR, DESCRIPTION_DIR]:
        os.makedirs(work_dir, exist_ok=True)
    for num in range(args.start_id, args.end_id + 1):
        try:
            download_book(num)
        except requests.exceptions.HTTPError:
            print(f'!!! книга {num} отсутствует на сайте ----\n')
            pass
    print('*** работа завершена ***')


if __name__ == '__main__':
    main()
