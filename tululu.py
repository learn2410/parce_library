import os
import sys
import argparse

import requests
from bs4 import BeautifulSoup
from lxml import etree
from pathvalidate import sanitize_filename

# корневой url
ROOT_URL = "https://tululu.org"


def check_need_path(path='books/'):
    if not os.path.exists(path):
        os.mkdir(path)
    elif os.path.isfile(path):
        print(f'ошибка: в папке есть файл с таким-же именем ({path})')
        return False
    return True


def check_for_redirect(response, text="вызван редирект"):
    if response.is_redirect:
        raise requests.HTTPError(text)


def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых и других файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    if url == ROOT_URL:
        print(f'ошибка[dowmnload_txt]: книгу "{filename}" нельзя скачать')
        return
    if not check_need_path(folder):
        return
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response, text=f'ошибка[dowmnload_txt]: url "{url}" вызвал редирект')
    with open(os.path.join(folder, filename), 'wb') as file:
        file.write(response.content)


def download_image(url, filename, folder='images/'):
    download_txt(url, filename, folder)


def parse_book_page(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response, text=f'ошибка[get_book_info]: url "{url}" вызвал редирект')
    # --- блок content
    cont = BeautifulSoup(response.content, 'lxml') \
        .find('div', attrs={'id': 'content'})
    dom = etree.HTML(str(cont))
    # --- ищем поля
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


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('start_id', default=1, type=int)
    parser.add_argument('end_id', default=1, type=int)
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args(sys.argv[1:])
    for num in range(args.start_id, args.end_id + 1):
        try:
            book = parse_book_page(f'{ROOT_URL}/b{num}/')
            book_file = sanitize_filename(f'{num}. {book["name"]}.txt')
            # --- скачиваем книгу
            download_txt(f'{ROOT_URL}{book["text_link"]}', book_file)
            # --- скачиваем обложку
            img_file = book['img_link'].split('/')[-1]
            if not os.path.exists(f'images/{img_file}'):
                download_image(f'{ROOT_URL}{book["img_link"]}', sanitize_filename(img_file))
            # --- записываем аннотацию
            folder = 'catalog/'
            if not check_need_path(folder):
                continue
            with open(os.path.join(folder, book_file), 'w') as file:
                file.write('\n'.join([
                    f'id: {num}',
                    f'название: {book["name"]}',
                    f'автор: {book["autor"]}',
                    f'жанр: {str(book["genre"])}',
                    f'обложка: {img_file}',
                    f'комментарии:\n{book["comments"]}',
                ]))
            print('название:', book['name'])
            print('Автор:', book['autor'], '\n')
        except requests.exceptions.HTTPError:
            pass


if __name__ == '__main__':
    main()
