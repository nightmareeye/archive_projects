# Подключение библиотек
import telebot
import pickle
import datetime
import threading
import classes
from prs import Parsing


# Загрузка сохраненных ранее данных
def upload():
    with open('data.txt', 'rb') as f:
        return pickle.load(f)


# Проверка на наличие сохраненных данных
try:
    info = upload()
    print('[SUCCESSFUL_DATA_UPLOAD]')
except:
    info = classes.Info_holder([])
    print('[EMPTY_DATA]')


# Инициализация переменных
_token = "1435226411:AAEVSgsgR2gSu842l-vD86wIyfroNCE6rJw"
bot = telebot.TeleBot(token=_token)
keyboard = telebot.types.ReplyKeyboardMarkup(True)
keyboard.row('/list', '/help')
parser = Parsing()
current_user = None
tmp = []
is_active = False
marker = None
st = datetime.datetime.now()


# Разрешение на обработка 3-х возможных команд
@bot.message_handler(commands=['start', 'list', 'help', 'del'])
# Разрешение на обработку текстовых сообщений
@bot.message_handler(content_types=['text'])
def echo(message):
    global info, current_user, tmp, marker, is_active
    #Определение текущего пользователя
    if info.find_customer_by_id(str(message.chat.id)) == None:
        info.add_customer(classes.Customer(str(message.chat.id), []))
    current_user = info.find_customer_by_id(str(message.chat.id))

    # Обработка команды /start
    if message.text == '/start':
        print('[START]\n>>> USER_ID:', str(message.chat.id))
        # Ответ пользователю
        bot.send_message(
            message.chat.id,
            """Привет! Я прайсбот. Отправьте мне ссылку на товар, который нужно отслеживать или посмотрите свои товары командой /list""",
            reply_markup=keyboard)
        is_active = False

    # Обработка команды /help
    elif message.text == '/help':
        print('[INFO]')
        # Ответ пользователю
        bot.send_message(
            message.chat.id,
            """Бот предназначен для мониторинга цен на товары. \nОтправьте ссылку вида: www.marketplace_name.ru/product_name... чтобы добавить его в список отслеживаемых товаров.\n\nКоманда /list покажет вам список отслеживаемых товаров с возможностью просмотра подробной информации\n\nЧтобы отказаться от подписки на товар, откройте информацию по нему, и после загрузки результатов используйте команду /del \n \n!!! Пожалуйста, при повторном использовании бота обновляйте свой список командой /list, прежде чем запрашивать информацию по товару !!!""")
        is_active = False

    # Обработка команды /start
    elif message.text == '/list':
        # Создание виртуальных кнопок для отображения информации о товаре
        markup = telebot.types.InlineKeyboardMarkup()
        # Добавление виртуальной кнопки на каждый товар
        for i in current_user.get_items():
            tmp.append(i.get_info()[3])
            print('tmp >>', tmp)
            markup.add(
                telebot.types.InlineKeyboardButton(
                    text=i.get_info()[0],
                    callback_data=str(tmp.index(i.get_info()[3]))))
        # Ответ пользователю
        bot.send_message(message.chat.id,
                         text="Список ваших подписок",
                         reply_markup=markup)
        # Сохранение данных                         
        save(info)
        is_active = False

    # Обработка команды /del
    elif message.text == '/del' and is_active:
        # Удаление товара из массива
        current_user.remove_item(marker)
        # Ответ пользователю
        bot.send_message(
            message.chat.id,
            text=
            "Товар удалён из списка отслеживаемых! Проверьте свой список командой /list"
        )

    # Обработка ссылок
    elif '.ru' in message.text:
        print('[FIND_URL]')
        # Добавление ссылки на товар в массив
        tmp.append(message.text)
        item = form_answer(message.text)
        current_user.add_item(
            classes.Item(item[0], item[1], item[2], message.text))
        # Ответ пользователю
        bot.reply_to(
            message,
            text =
            """Ваш товар успешно добавлен в список! Проверьте свой список командой /list"""
        )

    #Отчет по ошибочно введенным данным
    else:
        print('[INCORRECT_URL]')
        # Ответ пользователю
        bot.reply_to(
            message,
            '''Извините, это не ссылка на товар! Я не могу добавить это в ваш список.'''
        )


# Разрешение на обработку нажатий на виртуальные кнопки
@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    global tmp, marker, is_active, bot, current_user, info
    nasted_markup = telebot.types.InlineKeyboardMarkup()
    nasted_markup.add(telebot.types.InlineKeyboardButton(
                    text='Удалить',                                                                                                                                                                                                          
                    callback_data='del'+call.data))
    if 'del' in call.data:
        for i in current_user.get_items():
            print('info >>', i.get_info()[3])

        print('[ITEM_DELETED]')
        url = tmp[int(call.data.replace('del', ''))]
        print('url >>', url)
        current_user.remove_item(tmp[int(call.data.replace('del', ''))])
        answer = 'Товар удалён из списка'
        nasted_markup = None
    else:
        print('call data >>', call.data)
        bot.answer_callback_query(callback_query_id=call.id,
                                text='Подождите, обновляем информацию')
        result = form_answer(tmp[int(call.data)])
        marker = tmp[int(call.data)]
        answer = result[2] + '\nИнформация о товаре\n' + result[
            0] + '\nЦена ' + result[1]
        print('[ANSWER_FORMED]')
        # Отправка сформированного ответa
    bot.send_message(call.message.chat.id, ''.join(answer), reply_markup=nasted_markup)
    save(info)
    is_active = True


# Формирование ответа с подробной информацией о товаре
def form_answer(u):
    global parser, current_user, tmp
    try:
        print('[PARSING_STARTED]')
        if 'mvideo' in u:
            out = parser.parsepage_mv(parser.loadpage(u))
        elif 'eldorado' in u:
            out = parser.parsepage_el(parser.loadpage(u))
        elif 'avito' in u:
            out = parser.parsepage_av(parser.loadpage(u))
        print('[PARSING_FINISHED]')
    except:
        # Отчет об ошибке парсинга
        print('[PARSING_ERROR_OCCURRED]')
        out = 'Извините, произошла ошибка'
    return out


# Сохранение данных
def save(data):
    with open('data.txt', 'wb') as f:
        pickle.dump(data, f)
        print('[DATA_SAVED]')


# Обновление информации 
def refresh(old_data, parser, bot):
    print('[UPDATING...]')
    for user in old_data.get_customers():
        for item in user.get_items():
            print(user.get_items().index(item))
            new_data = form_answer(item.get_info()[3])
            old_price = int(item.get_info()[1])
            new_price = int(new_data[1])
            if new_price < old_price:
                bot.send_message(
                    user.get_id(), 'Цена на ' + item.get_info()[0] +
                    ' опустилась!\nСтарая цена: ' + str(old_price) +
                    '\nНовая цена: ' + str(new_price))
                print('[FIND_NEW_DATA]')
                item.update(new_data)
            else:
                print('[NO_NEW_DATA]')


# Проверка таймера на каждые n минут
def check_time(st, n):
    ct = datetime.datetime.now()
    delta = ct - st
    return delta.seconds % (n * 60) == 0


# Запуск бота (функция для потока)
def bot_func():
    global bot
    bot.polling()


# Обновление информации (функция для потока)
def update_func(t, i, p):
    global bot
    while True:
        try:
            if check_time(t, 3):
                refresh(i, p, bot)
                print('[SUCCESSFUL_DATA_UPDATE]')
        except:
            print('[DATA_UPDATE_ERROR]')


# Запуск потоков для работы бота и обновления информации
if __name__ == "__main__":
    x = threading.Thread(target=bot_func)
    x.start()
    y = threading.Thread(target=update_func, args=(st, info, parser))
    y.start()