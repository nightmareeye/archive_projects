# Подключение библиотек
import requests
import bs4

# Основной класс-парсер
class Parsing:
    # Инициализация класса
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': '''Mozilla/5.0 (Windows NT 10.0; Win64; x64) 
            AppleWebKit/537.36 (KHTML, like Gecko) 
            Chrome/81.0.4044.138 
            Safari/537.36 OPR/68.0.3618.197''',
            'Accept-Language': 'ru'
        }

    # Загрузка web-страницы по url-адресу
    def loadpage(self, url_1: str):
        res = self.session.get(url=url_1)
        res.raise_for_status()
        return res.text

    # Парсинг ссылок mvideo
    def parsepage_mv(self, text: str):
        # Обработка загруженной страницы
        soup = bs4.BeautifulSoup(text, 'lxml')
        #Получение названия товара из html файла 
        name = soup.find('h1', {'class':'fl-h1'}).get_text().replace('\n','').replace('\t','').replace('\r','')
        #Получение цены товара из html файла                             
        price = soup.find('div', {'class':'fl-pdp-price__current'}).get_text().replace('\xa0', '')[:-2:]
        #Получение изображения товара из html файла
        img = soup.find('img', {'class':'c-carousel__img'})['data-lazy'].replace('s', 'b')[2::]

        out = [name, price, img]
        return out

    # Парсинг ссылок eldorado
    def parsepage_el(self, text: str):
        # Обработка загруженной страницы
        soup = bs4.BeautifulSoup(text, 'lxml')
        #Получение названия товара из html файла
        name = soup.find('h1', {'class':'catalogItemDetailHd'}).get_text().replace('\n', '')     
        #Получение цены товара из html файла
        price = soup.find('div', {'class':'product-box-price__active'}).get_text().replace('\xa0', '').replace('р.', '')
        #Получение изображения товара из html файла
        img = soup.find('img', {'class':'slider-item-image slider-item-image--lazy'})['data-src']

        out = [name, price, img]
        return out

    # Парсинг ссылок avito
    def parsepage_av(self, text: str):
        # Обработка загруженной страницы
        soup = bs4.BeautifulSoup(text, 'html.parser')
        #Получение названия товара из html файла
        name = soup.find('h1', {'class':'title-info-title'}).get_text().replace('\n', '')
        #Получение цены товара из html файла
        price = soup.find('span', {'class':'js-item-price'}).get_text().replace(' ', '')
        #Получение изображения товара из html файла
        img = soup.find('div', {'class':'gallery-img-frame js-gallery-img-frame'})['data-url']
        
        return [name, price, img]