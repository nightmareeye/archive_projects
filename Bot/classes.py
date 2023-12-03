# Создание общего класса для хранения информации
class Info_holder:
    # Инициализация
    def __init__(self, customers: list):
        self.customers = customers

    # Добавление нового пользователяя
    def add_customer(self, c):
        self.customers.append(c)

    # Получение списка всех пользователей
    def get_customers(self):
        return self.customers

    # Поиск пользователя по id
    def find_customer_by_id(self, i):
        for c in self.customers:
            if c.get_id() == i:
                return c


# Создание класса пользователя
class Customer:
    # Инициализация
    def __init__(self, _id, items: list):
        self.id = _id
        self.items = items

    # Получение значения id пользователя
    def get_id(self):
        return self.id

    # Получение списка всех товаров пользователя
    def get_items(self):
        return self.items

    # Добавление товара в список пользователя
    def add_item(self, i):
        self.items.append(i)

    # Поиск товара в списке по его url
    def find_item_by_url(self, i):
        for item in self.items:
            if item.get_info()[3] == i:
                return item

    # Удаление товара из списка пользователя
    def remove_item(self, i):
        self.items.remove(self.find_item_by_url(i))


# Создание класса товара
class Item:
    # Инициализация
    def __init__(self, name, price, img, url):
        self.name = name
        self.price = price
        self.img = img
        self.url = url

    # Получение всей информации по товару
    def get_info(self):
        return [self.name, self.price, self.img, self.url]

    # Запись новой информации о товаре
    def update(self, new_data):
        self.name = new_data[0]
        self.price = new_data[1]
        self.img = new_data[2]
        self.url = new_data[3]