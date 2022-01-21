import os
import sys
import argparse

import requests
from bs4 import BeautifulSoup
from lxml import etree
from pathvalidate import sanitize_filename

# корневой url
ROOT_URL = "https://tululu.org"
# папка со скачанными книгами
TEXTS_DIR = 'books/'
# папка со скачанными обложками
COVERS_DIR = 'images/'
# папка с описаниями и комментариями к книгам
DESCRIPTION_DIR = 'catalog/'


# проверяет существует ли папка и если нет -создает ее
def check_need_path(path):
    if not os.path.exists(path):
        os.mkdir(path)
    elif os.path.isfile(path):
        # print(f'ошибка: в папке есть файл с таким-же именем ({path})')
        return False
    return True


# проверяет/создает необходимые для работы программы папки
def make_work_dirs():
    return check_need_path(TEXTS_DIR) and check_need_path(COVERS_DIR) and check_need_path(DESCRIPTION_DIR)


# проверка на редирект
def check_for_redirect(response, text="вызван редирект"):
    if response.is_redirect:
        raise requests.HTTPError(text)


def download_txt(url, filename, folder=TEXTS_DIR):
    """Функция для скачивания текстовых и других файлов.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    if url == ROOT_URL:
        print(f'--- ошибка[dowmnload_txt]: "{filename}" нельзя скачать\n')
        return
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response, text=f'--- ошибка[dowmnload_txt]: url "{url}" вызвал редирект')
    with open(os.path.join(folder, filename), 'wb') as file:
        file.write(response.content)


# функция скачивания картинок с обложками
def download_image(url, filename, folder=COVERS_DIR):
    download_txt(url, filename, folder)


# парсинг странички с книгой, вывод значимых параметров в виде словаря
def parse_book_page(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response, text=f'---ошибка[get_book_info]: url "{url}" вызвал редирект')
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


# скачивание книги с указанным id (результат 3 файла: текст, обложка, описание)
def download_book(id_number):
    try:
        book = parse_book_page(f'{ROOT_URL}/b{id_number}/')
        book_filename = sanitize_filename(f'{id_number}. {book["name"]}.txt')
        # --- скачиваем книгу
        download_txt(f'{ROOT_URL}{book["text_link"]}', book_filename)
        # --- скачиваем обложку
        img_file = book['img_link'].split('/')[-1]
        if not os.path.exists(f'{COVERS_DIR}{img_file}'):
            download_image(f'{ROOT_URL}{book["img_link"]}', sanitize_filename(img_file))
        # --- описание- в файл
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
    except requests.exceptions.HTTPError:
        pass


# парсер аргументов скрипта
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
    if not make_work_dirs():
        print('ошибка при создании рабочих подпапок, работа завершена')
    for num in range(args.start_id, args.end_id + 1):
        download_book(num)
    print('*** работа завершена ***')


if __name__ == '__main__':
    main()
