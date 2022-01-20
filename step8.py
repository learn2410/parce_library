import requests
import os
from bs4 import BeautifulSoup
from lxml import etree

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


def get_book_info(url):
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
    janre = dom.xpath('//*/span[@class="d_book"]/a/text()')
    return {'text_link': text_link,
            'img_link': img_link,
            'name': name,
            'autor': autor,
            'comments': comments,
            'genre': janre,
            }


def main():
    for num in range(1, 11):
        try:
            book = get_book_info(f'{ROOT_URL}/b{num}/')
            print(book['name'])
            print(book['genre'], '\n')
        except requests.exceptions.HTTPError:
            pass


if __name__ == '__main__':
    main()
