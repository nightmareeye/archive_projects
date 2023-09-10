from telethon import TelegramClient
from openpyxl import Workbook

# Введите свои данные API Telegram
api_id = 20053893
api_hash = '07c25b6c56c559615607578d26bc6124'
phone_number = '+79142083230'

# Создаем клиента Telegram
client = TelegramClient('first2', api_id, api_hash)

# Авторизуемся
client.start(phone_number)

# Получаем список пользователей чата
chat_users = await client.get_participants('https://t.me/BinanceRussian')

# Создаем файл Excel и добавляем заголовки столбцов
wb = Workbook()
ws = wb.active
ws.append(['ID', 'Имя', 'Фамилия', 'Никнейм'])

# Добавляем данные пользователей в таблицу
for user in chat_users:
    ws.append([user.id, user.first_name, user.last_name, user.username])

# Сохраняем файл Excel
wb.save('chat_users.xlsx')