import time, hashlib, telebot, sqlite3, os
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import hmac
from datetime import datetime, timedelta

#TOKEN = "6831494435:AAG2ZivO5eOWM0x1KgCQvaED-dnMTf0oLQw"
TOKEN="6572146217:AAEQHLUtE9FvMnmNJnKZqMnN1sN6MNUO6Ss"
bot = telebot.TeleBot(TOKEN)
managers = []
conn = sqlite3.connect('../data/botdb', check_same_thread=False)
cursor = conn.cursor()
cursor.execute("SELECT telegram_id FROM admins")
admins = [item[0] for item in cursor.fetchall()]
admins.append(6651973282)  
admins.append(5252948559)
NOTIFICATION_INTERVAL = 60  
NOTIFICATION_MEDIA_ID = None
NOTIFICATION_MESSAGE = None
LAST_BOT_MESSAGE_ID = None
BONUS_REFERRAL = 500
MANAGER_PERCENT = 30
user_state = {}
MERCHANT_ID = '41272'
SECRET_KEY = 'wRGg]F_k?f_BOdF'
api_key = '2f36e773e9e164a64c7d348df9f07eb5'
ASKING_PAYMENT_ID = "asking_payment_id"
ASKING_AMOUNT = "asking_amount"
user_states={}
manager_state={}
editing_manager = None
editing_user = None

def admin_required(func):
    def wrapper(message):
        if message.from_user.id in admins:
            return func(message)
        else:
            bot.reply_to(message, "Доступ запрещен!")
    return wrapper


def is_manager(tg_id):
    cursor = conn.cursor()
    cursor.execute("SELECT tg_id FROM managers WHERE tg_id=?", (tg_id,))
    result = cursor.fetchone()
    cursor.close()

    return bool(result)  

def is_user(tg_id):
    cursor = conn.cursor()
    cursor.execute("SELECT tg_id FROM users WHERE tg_id=?", (tg_id,))
    result = cursor.fetchone()
    cursor.close()

    return bool(result)  


def add_manager_to_db(tg_id, name, contacts):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO managers (tg_id, name, contacts) VALUES (?, ?, ?)", (tg_id, name, contacts))
    conn.commit()
    cursor.close()

def remove_manager_from_db(tg_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM managers WHERE tg_id=?", (tg_id,))
    conn.commit()
    cursor.close()

def fetch_admins_and_managers(message):
    cursor = conn.cursor()
    
    output = "Администраторы:\n"
    for admin in admins:
        uname = bot.get_chat(admin).username
        output+=f"\t\t-Telegram ID: {admin}, \n\t\t Username: {uname}\n"
    
    # Fetching managers
    cursor.execute("SELECT tg_id, name, contacts FROM managers")
    managers = cursor.fetchall()
    output+="\nМенеджеры:\n"
    for manager in managers:
        output+=f"\t\t -Telegram ID: {manager[0]}, \n\t\t Name: {manager[1]}, \n\t\t Contacts: {manager[2]}\n"
    
    bot.send_message(message.chat.id, output)

def get_manager_contacts(tg_id):
    cursor = conn.cursor()
    
    cursor.execute("SELECT contacts FROM managers WHERE tg_id=?", (tg_id,))
    result = cursor.fetchone()
        
    if result:
        return result[0]
    return None

@bot.message_handler(func=lambda message: is_manager(message.from_user.id) and not get_manager_contacts(message.from_user.id), content_types=["text"])
def handle_manager(message):
    telegram_id = message.chat.id
    contacts = get_manager_contacts(telegram_id)
    if not contacts and not "@" in message.text:
        bot.send_message(telegram_id, "Пожалуйста, укажите свои контактные данные (@ваш_юзернейм).")
    else:
        save_contacts(message)
        

def save_contacts(message):
    if "@" in message.text:
        cursor = conn.cursor()
        cursor.execute("UPDATE managers SET contacts=? WHERE tg_id=?", (message.text, int(message.chat.id)))
        conn.commit()
        delete_last_two_messages(message)
        bot.send_message(message.chat.id, "Контактные данные обновлены!", reply_markup=generate_manager_keyboard(message))
    else:
        bot.send_message(message.chat.id, "Пожалуйста, убедитесь, что ваш текст содержит '@'.", reply_markup=generate_manager_keyboard(message))

#REFERRALS:
def add_referral(user_id, referral_id):
    cursor.execute("SELECT * FROM referrals WHERE user_id=? AND referral_id=?", (user_id, referral_id))
    if cursor.fetchone():
        return

    cursor.execute("SELECT * FROM managers where tg_id=?", (referral_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE managers SET link_clicks=link_clicks + 1 WHERE tg_id=?", (referral_id,))


    cursor.execute("INSERT INTO referrals (user_id, referral_id) VALUES (?, ?)", (user_id, referral_id))
    conn.commit()

def get_referrals(user_id):
    cursor.execute("SELECT referral_id FROM referrals WHERE user_id=?", (user_id,))
    return [row[0] for row in cursor.fetchall()]

def referral_made_purchase(referral_id):
    cursor.execute("SELECT COUNT(*) FROM purchases WHERE user_id=?", (referral_id,))
    return cursor.fetchone()[0] > 0

def add_referral_bonus_if_purchase_made(user_id, referral_id):
    if referral_made_purchase(referral_id):
        cursor.execute("UPDATE users SET referral_balance = referral_balance + ? WHERE tg_id=?", (BONUS_REFERRAL, user_id))
        conn.commit()

def purchase_product(user_id, id):
    
    cursor.execute("SELECT user_id FROM referrals WHERE referral_id=?", (user_id,))
    referrer = cursor.fetchone()
    
    if referrer:  
        add_referral_bonus_if_purchase_made(referrer[0], user_id)


def send_bot_message(chat_id, text):
    global LAST_BOT_MESSAGE_ID
    msg = bot.send_message(chat_id, text)
    LAST_BOT_MESSAGE_ID = msg.message_id

def delete_last_two_messages(message):
    try:
        user_message_id = message.message_id
        bot_message_id = LAST_BOT_MESSAGE_ID if LAST_BOT_MESSAGE_ID else user_message_id - 1
        bot.delete_message(message.chat.id, user_message_id)
        bot.delete_message(message.chat.id, bot_message_id)
    except Exception as e:
        print(f"Error deleting messages: {e}")

def get_managers_from_db():
    cursor.execute("SELECT * FROM managers")
    return cursor.fetchall()

def get_manager_info_from_db(manager_id):
    cursor.execute("SELECT * FROM managers WHERE tg_id = ?", (manager_id,))
    return cursor.fetchone()

def get_general_stats_from_db():
    cursor.execute("SELECT SUM(link_clicks), SUM(total_purchases), SUM(total_amount), SUM(all_total_amount) FROM managers")
    return cursor.fetchone()


def admin_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Управление пользователями", "Управление финансами", "Информация")
    return markup

def user_management_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Добавить админа", "Удалить админа")
    markup.add("Добавить менеджера", "Удалить менеджера")
    markup.add("Информация о менеджерах")
    markup.add("Назад")
    return markup

def finance_management_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Установить процент менеджерам", "Установить сумму реферала пользователей")
    markup.add("Добавить товар","Удалить товар")
    markup.add("Добавить медиа")
    markup.add("Изменить текст реферала","Создать ссылку на оплату")
    markup.add("Добавить баланс менеджерам", "Стереть баланс менеджеров")
    markup.add("Добавить баланс пользователям", "Стереть баланс пользователей")
    markup.add("Назад")
    return markup

def info_keyboard(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Оповещения", "Конструктор промокодов")
    markup.add("Редактор промокодов", "Приветственное сообщение")
    markup.add("Менеджер по умолчанию", "Назад")
    markup.add("Информация по пользователю")
    markup.add("Выгрузить информацию в файл")
    return markup


def generate_manager_keyboard(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Изменить контактные данные")
    markup.add("Посмотреть статистику")
    markup.add("Моя ссылка", "Покупатели")
    markup.add("Стереть баланс пользователей")
    markup.add("Информация по пользователю")
    markup.add("Оповещения")
    return markup



def managers_keyboard():
    markup = types.InlineKeyboardMarkup()
    
    managers_list = get_managers_from_db()
    
    for manager in managers_list:
        markup.add(types.InlineKeyboardButton(text=manager[2], callback_data=f"set_manager.{manager[2]}"))
    
    return markup

@bot.message_handler(func=lambda message: message.text == "Менеджер по умолчанию")
def show_managers_list(message):
    bot.send_message(message.chat.id, "Выберите менеджера по умолчанию:", reply_markup=managers_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_manager."))
def set_default_manager(call):
    manager_username = call.data.split(".")[1]
    
    cursor.execute("DELETE FROM default_manager")  # Удаляем текущего менеджера
    cursor.execute("INSERT INTO default_manager (username) VALUES (?)", (manager_username,))  # Добавляем нового
    conn.commit()
    delete_last_two_messages(call.message)
    bot.send_message(call.message.chat.id, f"Менеджер {manager_username} установлен как менеджер по умолчанию.", reply_markup=info_keyboard(call.message))


# Конструктор промокодов
@bot.message_handler(func=lambda message: message.text == "Конструктор промокодов")
def request_promocode(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Отмена")
    msg = bot.send_message(message.chat.id, "Введите промокод и скидку в процентах через пробел:", reply_markup=markup)
    bot.register_next_step_handler(msg, save_promocode)

def generate_users_clear_inline_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Назад", callback_data="back_to_finance"))
    return markup    


@bot.callback_query_handler(func=lambda call: "user_remove_balance" in call.data)
def handle_user_clear_selection(call):
    delete_last_two_messages(call.message)
    user_id = int(call.data.split(".")[1])
    cursor.execute("UPDATE users SET referral_balance = 0 WHERE tg_id = ?", (user_id,))
    bot.send_message(call.message.chat.id, "Баланс пользователя сброшен.", reply_markup=finance_management_keyboard())

@bot.callback_query_handler(func=lambda call: "user_add_balance" in call.data)
def handle_user_add_selection(call):
    delete_last_two_messages(call.message)
    user_id = int(call.data.split(".")[1])
    global editing_user
    editing_user = user_id
    msg = bot.send_message(call.message.chat.id, "Введите сумму для увеличения баланса пользователя:")
    bot.register_next_step_handler(msg, process_add_user_balance)

def process_add_user_balance(message):
    value = message.text
    if value.isdigit():
        cursor.execute("UPDATE users SET referral_balance = referral_balance + ? WHERE tg_id = ?", (value, editing_user))
        conn.commit()
        if is_manager(message.from_user.id):
                bot.send_message(message.chat.id, f"Баланс пользователя увеличен на {value}", reply_markup=generate_manager_keyboard(message))
                return
        bot.send_message(message.chat.id, f"Баланс пользователя увеличен на {value}", reply_markup=finance_management_keyboard())
    else:
        if is_manager(message.from_user.id):
                bot.send_message(message.chat.id, "Пожалуйста, введите корректное числовое значение.", reply_markup=generate_manager_keyboard(message))
                return
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное числовое значение.", reply_markup=finance_management_keyboard())

@bot.message_handler(func=lambda message: message.text == "Добавить баланс пользователям")
def add_user_balance(message):
    msg = bot.send_message(message.chat.id, "Введите ID пользователя:", reply_markup=generate_users_clear_inline_keyboard())
    bot.register_next_step_handler(msg, process_add_user_id)

@bot.message_handler(func=lambda message: message.text == "Выгрузить информацию в файл")
def export_manager_info(message):
    '''if is_manager(message.from_user.id):
        cursor.execute("""
        SELECT u.tg_id
        FROM users u 
        INNER JOIN referrals r ON u.tg_id = r.user_id 
        WHERE r.referral_id = ?
        """, (message.from_user.id,))
        users = cursor.fetchall()
        cursor.execute("SELECT contacts FROM managers WHERE tg_id=?", (message.from_user.id,))
        contact = cursor.fetchone()[0]
        with open(f"manager_{contact}_users.txt", "w") as file:
            for user in users:
                user_info_p = bot.get_chat(user[0]) 
                username = user_info_p.username
                file.write(f"Username: {username}\n")
        with open(f"manager_{contact}_users.txt", "rb") as file:
            bot.send_document(message.chat.id, file, reply_markup=generate_manager_keyboard(message))
        os.remove(f"manager_{contact}_users.txt")
        return'''
    
    cursor.execute("SELECT tg_id FROM managers")
    managers = cursor.fetchall()
    with open("managers_and_users.txt", "w") as file:
        for manager in managers:
            cursor.execute("SELECT contacts FROM managers WHERE tg_id=?", (manager[0],))
            contact = cursor.fetchone()[0]
            file.write(f"Менеджер {manager[0]}, {contact}\n")
            cursor.execute("""
            WITH RECURSIVE referrals_recursive AS (
            SELECT u.tg_id, u.referrer_id
            FROM users u 
            WHERE u.referrer_id = ?
            UNION ALL
            SELECT u.tg_id, u.referrer_id
            FROM users u
            JOIN referrals_recursive r ON u.referrer_id = r.tg_id
            )
            SELECT tg_id FROM referrals_recursive
            """, (manager[0],))
            users = cursor.fetchall()
            for user in users:
                user_info_p = bot.get_chat(user[0]) 
                username = user_info_p.username
                file.write(f"Username: @{username}\n")
            file.write("-----------------------------------------\n")
    with open("managers_and_users.txt", "rb") as file:
        bot.send_document(message.chat.id, file, reply_markup=info_keyboard(message))
    os.remove("managers_and_users.txt")
        



@bot.message_handler(func=lambda message: message.text == "Информация по пользователю")
def info_user_info(message):
    msg = bot.send_message(message.chat.id, "Введите ID пользователя:", reply_markup=generate_users_clear_inline_keyboard())
    bot.register_next_step_handler(msg, process_info_user_id)

def process_info_user_id(message):
    try:
        user_id = int(message.text)
        if is_user(user_id):
            cursor.execute("SELECT * FROM users WHERE tg_id = ?", (user_id,))
            user_info=cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM referrals WHERE referral_id = ?", (user_id,))
            referrals_from_bd = cursor.fetchone()[0]
            user_info_p = bot.get_chat(user_id) 
            username = user_info_p.username
            if is_manager(message.from_user.id):
                bot.send_message(message.chat.id, f"Пользователь {username}:\nБаланс: {user_info[1]},\nКол-во переходов: {referrals_from_bd}", reply_markup=generate_manager_keyboard(message))
                return
            bot.send_message(message.chat.id, f"Пользователь {username}:\nБаланс: {user_info[1]},\nКол-во переходов: {referrals_from_bd}", reply_markup=finance_management_keyboard())
        else:
            if is_manager(message.from_user.id):
                    bot.send_message(message.chat.id, "Такой пользователь не существует", reply_markup=generate_manager_keyboard(message))
                    return
            bot.send_message(message.chat.id, "Такой пользователь не существует")
        handle_back(message)
    
    except IndexError:
        bot.send_message(message.chat.id, "Укажите ID менеджера для удаления!")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID!")

@bot.message_handler(func=lambda message: message.text == "Стереть баланс пользователей")
def remove_user_balance(message):
    msg = bot.send_message(message.chat.id, "Введите ID пользователя:", reply_markup=generate_users_clear_inline_keyboard())
    bot.register_next_step_handler(msg, process_clear_user_id)

def process_clear_user_id(message):
    try:
        user_id = int(message.text)
        if is_user(user_id):
            cursor.execute("UPDATE users SET referral_balance = 0 WHERE tg_id = ?", (user_id,))
            conn.commit()
            if is_manager(message.from_user.id):
                bot.send_message(message.chat.id, "Баланс пользователя сброшен.", reply_markup=generate_manager_keyboard(message))
                return
            bot.send_message(message.chat.id, "Баланс пользователя сброшен.", reply_markup=finance_management_keyboard())
        else:
            if is_manager(message.from_user.id):
                    bot.send_message(message.chat.id, "Такой пользователь не существует", reply_markup=generate_manager_keyboard(message))
                    return
            bot.send_message(message.chat.id, "Такой пользователь не существует")
        handle_back(message)

    except IndexError:
        bot.send_message(message.chat.id, "Укажите ID менеджера для удаления!")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID!")

def process_add_user_id(message):
    try:
        user_id = int(message.text)
        if is_user(user_id):
            global editing_user
            editing_user = user_id
            msg = bot.send_message(message.chat.id, "Введите сумму для увеличения баланса пользователя:", reply_markup=generate_users_clear_inline_keyboard())
            bot.register_next_step_handler(msg, process_add_user_balance)
        else:
            if is_manager(message.from_user.id):
                    bot.send_message(message.chat.id, "Такой пользователь не существует", reply_markup=generate_manager_keyboard(message))
                    return
            bot.send_message(message.chat.id, "Такой пользователь не существует")
        handle_back(message)

    except IndexError:
        bot.send_message(message.chat.id, "Укажите ID менеджера для удаления!")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID!")


def generate_managers_add_inline_keyboard():
    markup = InlineKeyboardMarkup()
    cursor.execute("SELECT tg_id, contacts FROM managers")
    managers = cursor.fetchall()
    for manager in managers:
        markup.add(InlineKeyboardButton(text=manager[1], callback_data=f"manager_add_balance.{manager[0]}"))
    markup.add(InlineKeyboardButton(text="Назад", callback_data="back_to_finance"))
    return markup

def generate_managers_clear_inline_keyboard():
    markup = InlineKeyboardMarkup()
    cursor.execute("SELECT tg_id, contacts FROM managers")
    managers = cursor.fetchall()
    for manager in managers:
        markup.add(InlineKeyboardButton(text=manager[1], callback_data=f"manager_remove_balance.{manager[0]}"))
    markup.add(InlineKeyboardButton(text="Назад", callback_data="back_to_finance"))
    return markup    

@bot.callback_query_handler(func=lambda call: "back_to_finance" in call.data)
def handle_back_to_finance_keyb(call):
    delete_last_two_messages(call.message)
    if is_manager(call.message.from_user.id):
            bot.send_message(call.message.chat.id, "Выберите действие",reply_markup=generate_manager_keyboard(call.message))
            return
    bot.send_message(call.message.chat.id, "Выберите действие",reply_markup=finance_management_keyboard())


@bot.callback_query_handler(func=lambda call: "manager_remove_balance" in call.data)
def handle_manager_clear_selection(call):
    delete_last_two_messages(call.message)
    manager_id = int(call.data.split(".")[1])
    cursor.execute("UPDATE managers SET total_amount = 0 WHERE tg_id = ?", (manager_id,))
    bot.send_message(call.message.chat.id, "Баланс менеджера сброшен.", reply_markup=finance_management_keyboard())

@bot.callback_query_handler(func=lambda call: "manager_add_balance" in call.data)
def handle_manager_add_selection(call):
    delete_last_two_messages(call.message)
    manager_id = int(call.data.split(".")[1])
    global editing_manager
    editing_manager = manager_id
    msg = bot.send_message(call.message.chat.id, "Введите сумму для увеличения баланса менеджера:")
    bot.register_next_step_handler(msg, process_add_balance)

def process_add_balance(message):
    value = message.text
    if value.isdigit():
        cursor.execute("UPDATE managers SET total_amount = total_amount + ? WHERE tg_id = ?", (value, editing_manager))
        bot.send_message(message.chat.id, f"Баланс менеджера увеличен на {value}", reply_markup=finance_management_keyboard())
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное числовое значение.", reply_markup=finance_management_keyboard())

@bot.message_handler(func=lambda message: message.text == "Добавить баланс менеджерам")
def add_balance(message):
    bot.send_message(message.chat.id, "Выберите менеджера для добавления баланса:", reply_markup=generate_managers_add_inline_keyboard())

@bot.message_handler(func=lambda message: message.text == "Стереть баланс менеджеров")
def remove_balance(message):
    bot.send_message(message.chat.id, "Выберите менеджера для сброса баланса:", reply_markup=generate_managers_clear_inline_keyboard())

def save_promocode(message):
    if message.text.lower() == "отмена":
        bot.send_message(message.chat.id, "Создание промокода отменено.", reply_markup=info_keyboard(message))
        return

    try:
        code, discount_percent = message.text.split()
        discount_percent = int(discount_percent)
        
        if not (0 <= discount_percent <= 100):
            raise ValueError
        
        cursor.execute("INSERT INTO promocodes (code, discount_percent) VALUES (?, ?)", (code, discount_percent))
        conn.commit()
        
        bot.send_message(message.chat.id, "Промокод добавлен!", reply_markup=info_keyboard(message))
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка. Убедитесь, что вводите данные в правильном формате и попробуйте снова.", reply_markup=info_keyboard(message))

@bot.callback_query_handler(func=lambda call: call.data == "admin_go_back")
def callback_inline_back_admin(call):
    delete_last_two_messages(call.message)
    bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=info_keyboard(call.message))

# Редактор промокодов
@bot.message_handler(func=lambda message: message.text == "Редактор промокодов")
def edit_promocode(message):
    cursor.execute("SELECT * FROM promocodes")
    promocodes = cursor.fetchall()
    delete_last_two_messages(message)

    markup = types.InlineKeyboardMarkup()
    for promo in promocodes:
        markup.add(types.InlineKeyboardButton(text=f"{promo[1]}, {promo[2]}%, {'активен' if promo[3] else 'неактивен'}", 
                                             callback_data=f"toggle_{promo[1]}"))
    markup.add(types.InlineKeyboardButton(text="Назад", callback_data="admin_go_back"))

    bot.send_message(message.chat.id, "Выберите промокод для изменения статуса:", reply_markup=markup)

@bot.callback_query_handler(lambda call: call.data.startswith("toggle"))
def toggle_promocode(call):
    promo_id = call.data.split("_")[1]
    cursor.execute("UPDATE promocodes SET is_active = NOT is_active WHERE code = ?", (promo_id,))
    conn.commit()
    delete_last_two_messages(call.message)
    bot.send_message(call.message.chat.id, "Статус промокода изменен!", reply_markup=info_keyboard(call.message))




@bot.message_handler(func=lambda message: message.text == "Изменить контактные данные")
def change_contact_data(message):
    msg = bot.send_message(message.chat.id, "Введите новые контактные данные:")
    bot.register_next_step_handler(msg, save_contacts)

def save_new_contact_data(message):
    new_contacts = message.text
    cursor.execute("UPDATE managers SET contacts=? WHERE tg_id=?", (new_contacts, message.chat.id))
    conn.commit()
    bot.send_message(message.chat.id, "Контактные данные обновлены!", reply_markup=generate_manager_keyboard(message))

@bot.message_handler(func=lambda message: message.text == "Посмотреть статистику")
def show_statistics(message):
    cursor.execute("SELECT * FROM managers WHERE tg_id=?", (message.chat.id,))
    manager_data = cursor.fetchone()
    bot.send_message(message.chat.id, f"Статистика:\n"
                                      f"Имя: {manager_data[1]}\n"
                                      f"Клики по ссылке: {manager_data[3]}\n"
                                      f"Всего покупок: {manager_data[4]}\n"
                                      f"Общая сумма: {manager_data[5]}\n"
                                      f"Процент: {manager_data[6]}%", reply_markup=generate_manager_keyboard(message))

@bot.message_handler(func=lambda message: message.text == "Моя ссылка")
def show_link(message):
    user_id = message.chat.id
    name = bot.get_me().username
    referral_link = f'https://t.me/{name}?start={user_id}'
    bot.send_message(message.chat.id, f"\nВаша реферальная ссылка: {referral_link}", reply_markup=generate_manager_keyboard(message))

@bot.message_handler(func=lambda message: message.text == "Покупатели")
def show_buyers(message):
    cursor.execute("SELECT user_id FROM referrals WHERE referral_id=?", (message.chat.id,))
    user_ids = cursor.fetchall()
    
    buyers_msg = "Покупатели:\n"

    for user_id_tuple in user_ids:
        user_id = user_id_tuple[0]
        
        cursor.execute("SELECT COUNT(*) FROM purchases WHERE user_id=?", (user_id,))
        purchase_count = cursor.fetchone()[0]

        if purchase_count > 0:  
            cursor.execute("SELECT * FROM users WHERE tg_id=?", (user_id,))
            buyer = cursor.fetchone()
            
            if buyer:
                buyers_msg += f"ID: {buyer[0]}, Покупок: {purchase_count}, Баланс: {buyer[1]}\n"
    
    bot.send_message(message.chat.id, buyers_msg, reply_markup=generate_manager_keyboard(message))



@bot.message_handler(func=lambda m: m.text == "Оповещения")
def handle_interval_notification(message):
    delete_last_two_messages(message)
    send_notification_settings(message)

def send_notification_settings(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Оповестить пользователей")
    markup.add("Сообщение оповещения")
    markup.add("Назад")
    bot.send_message(message.chat.id, "Выберите настройку для изменения:", reply_markup=markup)
    return markup


@bot.message_handler(func=lambda m: m.text == "Создать ссылку на оплату" and m.from_user.id in admins)
def create_custom_pay_link(message):
    user_states[message.chat.id] = ASKING_PAYMENT_ID
    bot.send_photo(message.chat.id, photo=open("./assets/codes/payment_id.png", 'rb'), caption="Пожалуйста, введите ID платежной системы:")



@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == ASKING_PAYMENT_ID)
def handle_payment_id(message):
    if message.text.isdigit(): 
        user_states[message.chat.id] = ASKING_AMOUNT
        user_states[f"{message.chat.id}_payment_id"] = message.text
        bot.send_message(message.chat.id, "Введите сумму для оплаты:")
    else:
        bot.send_message(message.chat.id, "Неверный ID платежной системы. Пожалуйста, введите целое число:")


order_id_def = 1111111111 

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == ASKING_AMOUNT)
def handle_amount(message):
    try:
        amount = float(message.text)  
        if amount <= 0:  
            raise ValueError("Сумма должна быть положительной", reply_markup=admin_main_keyboard())
        user_states[message.chat.id] = None
        global order_id_def
        order_id_def +=1
        payment_id = user_states.get(f"{message.chat.id}_payment_id")
        link = generate_payment_link(amount, order_id_def ,payment_id)
        bot.send_message(message.chat.id, f"Создание ссылки на оплату с ID платежной системы {payment_id} на сумму {amount}:\n{link}", reply_markup=admin_main_keyboard())
        #is_order_paid(order_id_def)

    except ValueError as e:
        bot.send_message(message.chat.id, f"Неверная сумма. Пожалуйста, введите положительное число. ({str(e)})", reply_markup=admin_main_keyboard())


@bot.message_handler(func=lambda message: message.text == "Изменить текст реферала")
def handle_refferal_message(message):
    user_state[message.chat.id] = "AWAITING_REFERRAL"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Отмена")
    bot.send_message(message.chat.id, "Пожалуйста, прислать фото или видео, которое нужно добавить. Или нажмите 'Отмена' для отмены действия.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Добавить медиа")
def handle_add_media(message):
    user_state[message.chat.id] = "AWAITING_MEDIA"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Отмена")
    bot.send_message(message.chat.id, "Пожалуйста, прислать фото или видео, которое нужно добавить. Или нажмите 'Отмена' для отмены действия.", reply_markup=markup)


def send_referral_message(chat_id):
    media_folder = "./assets/referral_message/"
    caption_file_path = os.path.join(media_folder, "caption.txt")
    photo_path = os.path.join(media_folder, "referral_message.jpg")
    video_path = os.path.join(media_folder, "referral_message.mp4")
    markup = types.InlineKeyboardMarkup()    # Создаем кнопки
    ref_balance_btn = types.InlineKeyboardButton('Мой баланс', callback_data='ref_balance')
    my_referrals_btn = types.InlineKeyboardButton('Мои рефералы', callback_data='my_referrals')
    message_ref = types.InlineKeyboardButton('Реферальная ссылка отдельным сообщением', callback_data='ref_mes_link')
    go_back = types.InlineKeyboardButton('Назад', callback_data='go_back_user')
    
    markup.add(ref_balance_btn, my_referrals_btn)
    markup.add(message_ref)
    markup.add(go_back)
    user_id = chat_id
    name = bot.get_me().username
    referral_link = f'https://t.me/{name}?start={user_id}'

    caption = ""
    if os.path.exists(caption_file_path):
        with open(caption_file_path, 'r', encoding='utf-8') as caption_file:
            caption = caption_file.read()
    else:
        bot.send_message(chat_id, "Сожалеем, сообщение недоступно."+f"\nВаша реферальная ссылка: {referral_link}", reply_markup=markup)

    if os.path.exists(photo_path):
        with open(photo_path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=caption+f"Ваша реферальная ссылка: {referral_link}", reply_markup=markup)
    elif os.path.exists(video_path):
        with open(video_path, 'rb') as video:
            bot.send_video(chat_id, video, caption=caption+f"Ваша реферальная ссылка: {referral_link}", reply_markup=markup)
    else:
        bot.send_message(chat_id, caption+f"Ваша реферальная ссылка: {referral_link}", reply_markup=markup)

@bot.message_handler(content_types=['photo', 'video'], func=lambda message: user_state.get(message.chat.id) == "AWAITING_REFERRAL")
def handle_referral_message_add(message):
    file_info = None
    extension = ""
    caption = message.caption if message.caption else ""

    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        extension = ".jpg"
    elif message.video:
        file_info = bot.get_file(message.video.file_id)
        extension = ".mp4"

    if file_info:
        downloaded_file = bot.download_file(file_info.file_path)

        media_folder = "./assets/referral_message/"
        if not os.path.exists(media_folder):
            os.makedirs(media_folder)

        for filename in os.listdir(media_folder):
            file_path = os.path.join(media_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

        new_file_path = os.path.join(media_folder, f"referral_message{extension}")
        with open(new_file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        if caption:
            caption_file_path = os.path.join(media_folder, "caption.txt")
            with open(caption_file_path, 'w', encoding='utf-8') as caption_file:
                caption_file.write(caption)

        user_state[message.chat.id] = None
        markup = finance_management_keyboard()
        bot.send_message(message.chat.id, "Сообщение добавлено!", reply_markup=markup)


@bot.message_handler(content_types=['photo', 'video'], func=lambda message: user_state.get(message.chat.id) == "AWAITING_MEDIA")
def handle_media(message):
    file_info = None
    extension = ""

    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        extension = ".jpg"
    elif message.video:
        file_info = bot.get_file(message.video.file_id)
        extension = ".mp4"

    if file_info:
        downloaded_file = bot.download_file(file_info.file_path)

        media_folder = "./assets/welcome_media/"
        if not os.path.exists(media_folder):
            os.makedirs(media_folder)

        for filename in os.listdir(media_folder):
            file_path = os.path.join(media_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

        new_file_path = os.path.join(media_folder, f"welcome_media{extension}")
        with open(new_file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        user_state[message.chat.id] = None
        markup = finance_management_keyboard()
        bot.send_message(message.chat.id, "Медиа добавлено!", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Отмена" and user_state.get(message.chat.id) == "AWAITING_MEDIA")
def handle_cancel(message):
    user_state[message.chat.id] = None
    markup = finance_management_keyboard()
    bot.send_message(message.chat.id, "Действие отменено.", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Информация о менеджерах")
def managers_info(message):
    all_managers = get_managers_from_db() 
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for manager in all_managers:
        markup.add(types.InlineKeyboardButton(text=manager[1], callback_data=f"info_{manager[0]}"))
    markup.add(types.InlineKeyboardButton(text="Общая статистика", callback_data="general_stats"))
    markup.add(types.InlineKeyboardButton(text="Назад", callback_data="back_to_management"))
    
    bot.send_message(message.chat.id, "Выберите менеджера или посмотрите общую статистику:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True and call.from_user.id in admins)
def callback_inline(call):
    if call.message:
        if call.data.startswith("info_"):
            manager_id = int(call.data.split("_")[1])
            manager_info = get_manager_info_from_db(manager_id)  
            if manager_info:
                info_message = f"""
                Имя: \t{manager_info[1]}\nКонтакты: \t{manager_info[2]}\nПереходов: \t{manager_info[3]}\nВсего продано: \t{manager_info[4]}\nОбщая сумма: \t{manager_info[5]}\nПроцент: \t{manager_info[6]}%\nОбщая сумма за все время: {manager_info[7]}
                """
                bot.send_message(call.message.chat.id, info_message, reply_markup=admin_main_keyboard())
            else:
                bot.send_message(call.message.chat.id, "Информация о менеджере не найдена.", reply_markup=admin_main_keyboard())

        elif call.data == "general_stats":
            stats = get_general_stats_from_db()  
            if stats and all(stats):
                general_stats_message = f"""
                Общая статистика менеджеров:
                Кликов по ссылке: {stats[0]}
                Всего покупок: {stats[1]}
                Общая сумма: {stats[2]}
                Общая сумма за все время: {stats[3]}
                """
                bot.send_message(call.message.chat.id, general_stats_message)
            else:
                bot.send_message(call.message.chat.id, "Статистика менеджеров не найдена или некоторые данные отсутствуют.", reply_markup=user_management_keyboard())

        elif call.data == "back_to_management":
            delete_last_two_messages(call.message)
            bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=user_management_keyboard())
        elif call.data.startswith("setpercent_"):
            manager_name = call.data.split("_")[1]
            current_percent = get_current_percent(manager_name)
            delete_last_two_messages(call.message)
            msg_text = (f"Текущий процент для {manager_name} составляет {current_percent}%.\n\n"
                        "Введите новый процент или отправьте /cancel для отмены.")

            bot.send_message(call.message.chat.id, msg_text)
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, receive_new_percent, manager_name)




def get_managers_name_from_db():
    cursor.execute("SELECT name FROM managers")
    managerss = [row[0] for row in cursor.fetchall()]
    return managerss

def get_current_percent(manager_name):
    cursor.execute("SELECT percent FROM managers WHERE name=?", (manager_name,))
    percent = cursor.fetchone()[0]
    return percent

def set_new_percent(manager_name, new_percent):
    cursor.execute("UPDATE managers SET percent=? WHERE name=?", (new_percent, manager_name))
    conn.commit()

@bot.message_handler(func=lambda message: message.text == "Установить процент менеджерам")
def set_manager_percent(message):
    managerss = get_managers_name_from_db()
    delete_last_two_messages(message)
    if not managerss:
        bot.send_message(message.chat.id, "Менеджеры не найдены.", reply_markup=admin_main_keyboard())
        return

    markup = types.InlineKeyboardMarkup()
    for manager in managerss:
        markup.add(types.InlineKeyboardButton(manager, callback_data=f"setpercent_{manager}"))

    bot.send_message(message.chat.id, "Выберите менеджера:", reply_markup=markup)



def receive_new_percent(message, manager_name):
    delete_last_two_messages(message)
    if message.text.lower() == '/cancel':
        bot.send_message(message.chat.id, "Операция отменена.", reply_markup=admin_main_keyboard())
        return

    try:
        new_percent = float(message.text)
        if not (0 <= new_percent <= 100):
            raise ValueError("Процент должен быть в диапазоне от 0 до 100.", reply_markup=admin_main_keyboard())
    except ValueError as ve:
        bot.send_message(message.chat.id, str(ve) + " Попробуйте снова.", reply_markup=admin_main_keyboard())
        return

    set_new_percent(manager_name, new_percent)
    bot.send_message(message.chat.id, f"Установлен новый процент для {manager_name}: {new_percent}%", reply_markup=admin_main_keyboard())



@bot.message_handler(func=lambda message: message.text == "Установить сумму реферала пользователей")
def set_referral_sum(message):
    msg = bot.send_message(message.chat.id, f"Текущая сумма {BONUS_REFERRAL}\nВведите сумму реферала для пользователей:")
    bot.register_next_step_handler(msg, process_referral_sum)

def process_manager_percent(message):
    global BONUS_REFERRAL
    value = message.text
    if value.isdigit():
        global MANAGER_PERCENT
        MANAGER_PERCENT = value
        bot.send_message(message.chat.id, f"Установлен процент менеджерам: {value}%", reply_markup=finance_management_keyboard())
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное числовое значение.", reply_markup=finance_management_keyboard())

def process_referral_sum(message):
    global BONUS_REFERRAL
    value = message.text
    if value.isdigit():
        BONUS_REFERRAL = value
        bot.send_message(message.chat.id, f"Установлена сумма реферала для пользователей: {value}", reply_markup=finance_management_keyboard())
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное числовое значение.", reply_markup=finance_management_keyboard())

@bot.message_handler(func=lambda message: message.text == "Назад" and message.from_user.id in admins)
def go_back(message):
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=admin_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "Оповестить пользователей")
def notify_all_users(message):
    global NOTIFICATION_MESSAGE, NOTIFICATION_MEDIA_ID

    if NOTIFICATION_MESSAGE is None:
        bot.send_message(message.chat.id,"Сначала введите сообщение оповещения!", reply_markup=send_notification_settings(message))
        return

    if is_manager(message.from_user.id):
        cursor.execute("SELECT tg_id FROM users WHERE referrer_id=?", (message.from_user.id,))
        users = cursor.fetchall()
        for user in users:
            try:
                if NOTIFICATION_MEDIA_ID:
                    bot.send_photo(user[0], NOTIFICATION_MEDIA_ID, caption=NOTIFICATION_MESSAGE)
                else:
                    bot.send_message(user[0], NOTIFICATION_MESSAGE)
                NOTIFICATION_MESSAGE = None
                NOTIFICATION_MEDIA_ID = None
            except Exception as e:
                print(f"Failed to send message to {user[0]}: {str(e)}")
        bot.send_message(message.chat.id,"Пользователи оповещены", reply_markup=send_notification_settings(message))
        return

    cursor.execute("SELECT tg_id FROM users")
    users = cursor.fetchall()
    for user in users:
        try:
            if NOTIFICATION_MEDIA_ID:
                bot.send_photo(user[0], NOTIFICATION_MEDIA_ID, caption=NOTIFICATION_MESSAGE)
            else:
                bot.send_message(user[0], NOTIFICATION_MESSAGE)
            NOTIFICATION_MESSAGE = None
            NOTIFICATION_MEDIA_ID = None
        except Exception as e:
            print(f"Failed to send message to {user[0]}: {str(e)}")

    bot.send_message(message.chat.id,"Пользователи оповещены", reply_markup=send_notification_settings(message))    
    
def save_interval(message):
    global NOTIFICATION_INTERVAL

    if message.text == "Назад":
        delete_last_two_messages(message)
        send_notification_settings(message)
        return

    if message.text.isdigit():
        NOTIFICATION_INTERVAL = int(message.text)
        bot.send_message(message.chat.id, f"Интервал оповещения обновлен на {NOTIFICATION_INTERVAL} минут!")
        send_notification_settings(message)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число. Попробуйте снова.")
        set_interval(message)

@bot.message_handler(func=lambda m: m.text == "Назад" and is_manager(m.from_user.id))
def handle_back(message):
    delete_last_two_messages(message)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=generate_manager_keyboard(message))

@bot.message_handler(func=lambda m: m.text == "Сообщение оповещения")
def set_notification_message(message):
    delete_last_two_messages(message)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Назад")
    if NOTIFICATION_MEDIA_ID:
        sent = bot.send_photo(message.chat.id, NOTIFICATION_MEDIA_ID, caption=f"Текущее сообщение:\n{NOTIFICATION_MESSAGE} \n\nВведите новый текст сообщения оповещения:")
    else:
        sent =bot.send_message(message.chat.id, f"Текущее сообщение:\n{NOTIFICATION_MESSAGE} \n\nВведите новый текст сообщения оповещения:")
    bot.register_next_step_handler(sent, save_notification_message)
    return markup

def save_notification_message(message):
    global NOTIFICATION_MESSAGE, NOTIFICATION_MEDIA_ID
    
    if message.content_type == 'photo':
        NOTIFICATION_MEDIA_ID = message.photo[-1].file_id
        if message.caption: 
            NOTIFICATION_MESSAGE = message.caption
        bot.send_message(message.chat.id, "Фото и подпись к изображению обновлены!")
        send_notification_settings(message)

    elif message.content_type == 'text':
        NOTIFICATION_MESSAGE = message.text
        NOTIFICATION_MEDIA_ID = None
        bot.send_message(message.chat.id, "Текст оповещения обновлен!")
        send_notification_settings(message)

@bot.message_handler(func=lambda m: m.text == "Приветственное сообщение" and m.from_user.id in admins)
def handle_welcome_message(message):
    delete_last_two_messages(message)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Назад")
    msg = bot.send_message(message.chat.id, "Введите новое приветственное сообщение:", reply_markup=markup)
    bot.register_next_step_handler(msg, admin_update_welcome)
    return markup

def admin_update_welcome(message):
    cursor = conn.cursor()

    if message.text == "Назад":
        delete_last_two_messages(message)
        handle_info(message)
        return
    else:
        if message.content_type == 'photo':
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            new_image_path = "assets/hello_message/start.jpg"

            with open(new_image_path, 'wb') as new_file:
                new_file.write(downloaded_file)
        
            cursor.execute("DELETE FROM welcome")  
            cursor.execute("INSERT INTO welcome (message, image_path) VALUES (?, ?)", (message.caption, new_image_path))
    
        else:
            cursor.execute("DELETE FROM welcome")  
            cursor.execute("INSERT INTO welcome (message) VALUES (?)", (message.text,))

        conn.commit()

        bot.send_message(message.chat.id, "Приветственное сообщение/картинка обновлены!")



@bot.message_handler(func=lambda m: m.text == "Добавить админа")
@admin_required
def handle_add_admin(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Отмена")
    msg = bot.send_message(message.chat.id, "Введите Telegram ID нового админа:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_add_admin)
    return markup

def process_add_admin(message):
    if message.text == "Отмена":
        delete_last_two_messages(message)
        handle_back(message)
        return
    try:
        admin_id = int(message.text)
        user_info = bot.get_chat(admin_id) 
        username = user_info.username
        admins.append(admin_id)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO admins (telegram_id, username) VALUES (?, ?)", (admin_id, username))
        conn.commit()

        bot.send_message(message.chat.id, f"""Админ {username} успешно добавлен!""")
        handle_back(message)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

@bot.message_handler(func=lambda m: m.text == "Удалить админа")
@admin_required
def handle_remove_admin(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Отмена")
    msg = bot.send_message(message.chat.id, "Введите Telegram ID админа для удаления:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_remove_admin)
    return markup

def process_remove_admin(message):
    if message.text == "Отмена":
        delete_last_two_messages(message)
        handle_back(message)
        return
    try:
        admin_id = int(message.text)
        user_info = bot.get_chat(admin_id) 
        username = user_info.username
        cursor = conn.cursor()
        cursor.execute("DELETE FROM admins WHERE telegram_id=?", (admin_id,))
        conn.commit()
        admins.remove(admin_id)

        bot.send_message(message.chat.id, f"""Админ {username} успешно удален!""")
        handle_back(message)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")


@bot.message_handler(func=lambda m: m.text == "Добавить менеджера")
@admin_required
def handle_add_manager(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Отмена")
    msg = bot.send_message(message.chat.id, "Введите Telegram ID нового менеджера:",reply_markup=markup)
    bot.register_next_step_handler(msg, process_add_manager)
    return markup

def process_add_manager(message):
    if message.text == "Отмена":
        delete_last_two_messages(message)
        handle_back(message)
        return
    try:
        manager_id = int(message.text)  
        try:
            user_info = bot.get_chat(manager_id)

            manager_name = user_info.first_name or user_info.username
            add_manager_to_db(manager_id, manager_name, "")
        
            bot.send_message(message.chat.id, f"Менеджер {manager_name} ({manager_id}) добавлен!")
            handle_back(message)
        except telebot.apihelper.ApiTelegramException:
            handle_back(message)
            bot.send_message(message.chat.id, "Пользователю необходимо сначала вступить в бота!")
    except IndexError:
        bot.send_message(message.chat.id, "Укажите ID менеджера для добавления!")
        handle_back(message)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID!")
        handle_back(message)




@bot.message_handler(func=lambda m: m.text == "Удалить менеджера")
@admin_required
def handle_remove_manager(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Отмена")
    msg = bot.send_message(message.chat.id, "Введите Telegram ID менеджера для удаления:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_remove_manager)
    return markup

def process_remove_manager(message):
    if message.text == "Отмена":
        delete_last_two_messages(message)
        handle_back(message)
        return
    try:
        manager_id = int(message.text)
        if is_manager(manager_id):
            remove_manager_from_db(manager_id)
            bot.send_message(message.chat.id, f"Пользователь {manager_id} удален из менеджеров!")
        else:
            bot.send_message(message.chat.id, "Этот пользователь не является менеджером!")
        handle_back(message)

    except IndexError:
        bot.send_message(message.chat.id, "Укажите ID менеджера для удаления!")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID!")



@bot.message_handler(func=lambda m: m.text == "Назад" and m.from_user.id in admins)
def handle_back(message):
    delete_last_two_messages(message)
    markup = admin_main_keyboard()
    bot.send_message(message.chat.id, "Выберите основное действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Управление пользователями")
@admin_required
def handle_user_management(message):
    delete_last_two_messages(message)
    fetch_admins_and_managers(message)
    markup = user_management_keyboard()
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Управление финансами")
@admin_required
def handle_finance_management(message):
    delete_last_two_messages(message)
    markup = finance_management_keyboard()
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Информация")
@admin_required
def handle_info(message):
    delete_last_two_messages(message)
    markup = info_keyboard(message)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)


def generate_user_markup():
    markup = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=True)
    
    button_product = KeyboardButton("Сервисы🛍️")
    button_contacts = KeyboardButton("Тех. поддержка💬")
    button_referrals = KeyboardButton("Рефералка👨‍👨‍👧‍👦")
    
    markup.add(button_product, button_contacts, button_referrals)
    
    return markup

#PRODUCTS


current_product_data = {}

@bot.message_handler(func=lambda message: message.text == "Удалить товар" and message.from_user.id in admins)
def start_deleting_product(message):
    bot.send_message(message.chat.id, "Введите название товара или слово 'Отмена':")
    bot.register_next_step_handler(message, get_product_name_delete)

def get_product_name_delete(message):
    if message.text=="Отмена":
        handle_finance_management(message)
        return
    product_name = message.text
    cursor.execute("SELECT * from products where name=?", (product_name,))
    exists = cursor.fetchone()
    if exists:
        cursor.execute("DELETE from products where name=?", (product_name,))
        bot.send_message(message.chat.id, f"Товар {product_name} удален!", reply_markup=finance_management_keyboard())
        conn.commit()
    else:
        bot.send_message(message.chat.id, "Такого товара не существует!", reply_markup=finance_management_keyboard())

@bot.message_handler(func=lambda message: message.text == "Добавить товар" and message.from_user.id in admins)
def start_adding_product(message):
    bot.send_message(message.chat.id, "Введите название товара или слово 'Отмена':")
    bot.register_next_step_handler(message, get_product_name)

def get_product_name(message):
    if message.text=="Отмена":
        handle_finance_management(message)
        return
    current_product_data['name'] = message.text
    bot.send_message(message.chat.id, "Загрузите фото товара или отправьте /skip, если фото нет.")
    bot.register_next_step_handler(message, get_product_photo)

def get_product_photo(message):
    if message.text == '/skip':
        current_product_data['photo'] = None
    else:
        current_product_data['photo'] = message.photo[-1].file_id
    bot.send_message(message.chat.id, "Введите описание товара:")
    bot.register_next_step_handler(message, get_product_description)

def get_product_description(message):
    current_product_data['description'] = message.text
    request_price_for_interval(message)


price_intervals = ['1 месяц', '2 месяца', '3 месяца', '6 месяцев']
current_interval_index = 0
def request_price_for_interval(message):
    global current_interval_index
    if current_interval_index < len(price_intervals):
        interval = price_intervals[current_interval_index]
        markup = ReplyKeyboardMarkup("Пропустить")
        bot.send_message(message.chat.id, f"Введите цену за {interval} или введите 'Пропустить':", reply_markup=markup)
        bot.register_next_step_handler(message, set_product_price)
    else:
        finish_adding_product(message)

def set_product_price(message):
    global current_interval_index
    price_key = f"price_{current_interval_index + 1}"
    
    if message.text.isdigit():
        current_product_data[price_key] = float(message.text)
    else:
        current_product_data[price_key] = 0.0

    current_interval_index += 1
    request_price_for_interval(message)

@bot.callback_query_handler(func=lambda call: call.data == "skip_price")
def skip_price(call):
    global current_interval_index
    price_key = f"price_{current_interval_index + 1}"
    current_product_data[price_key] = 0.0
    current_interval_index += 1
    request_price_for_interval(call.message)


def finish_adding_product(message):
    cursor.execute("INSERT INTO products (name, photo_path, description, price_1_month, price_2_month, price_3_month, price_6_month) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                   (current_product_data['name'], current_product_data['photo'], current_product_data['description'], current_product_data['price_1'], current_product_data['price_2'], current_product_data['price_3'], current_product_data['price_4']))
    global current_interval_index
    current_interval_index=0
    current_product_data.clear()
    conn.commit()
    bot.send_message(message.chat.id, "Товар успешно добавлен!", reply_markup=finance_management_keyboard())


@bot.message_handler(func=lambda m: m.text == "Сервисы🛍️")
def handle_product(message):
    cursor.execute("SELECT name FROM products WHERE price_1_month > 0 OR price_2_month > 0 OR price_3_month > 0 OR price_6_month > 0")
    products = cursor.fetchall()
    
    
    media_folder = "./assets/welcome_media/"
    media_file_path = None
    for filename in os.listdir(media_folder):
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".mp4")):
            media_file_path = os.path.join(media_folder, filename)
            
    
    if products:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for product in products:
            product_name = product[0]
            markup.add(types.InlineKeyboardButton(text=product_name, callback_data=f"product_{product_name}"))
        markup.add(types.InlineKeyboardButton(text="На главную", callback_data=f"back_to_user_menu"))

        if media_file_path:
            if media_file_path.lower().endswith((".jpg", ".jpeg", ".png")):
                with open(media_file_path, 'rb') as media:
                    bot.send_photo(message.chat.id, media, caption="Выберите товар:", reply_markup=markup)
            elif media_file_path.lower().endswith(".mp4"):
                with open(media_file_path, 'rb') as media:
                    bot.send_video(message.chat.id, media, caption="Выберите товар:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Выберите товар:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "К сожалению, товаров сейчас нет в наличии.", reply_markup=generate_user_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_user_menu"))
def go_back_user(call):
    delete_last_two_messages(call.message)
    bot.send_message(call.message.chat.id, "Выберите действие", reply_markup=generate_user_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def handle_product_choice(call):
    product_name = call.data.split("_")[1]
    delete_last_two_messages(call.message)
    cursor.execute("SELECT id, name, photo_path, description, price_1_month, price_2_month, price_3_month, price_6_month FROM products WHERE name=?", (product_name,))
    product = cursor.fetchone()

    if product:
        id, name, photo_path, description, price_1_month, price_2_month, price_3_month, price_6_month = product

        if photo_path:
            bot.send_photo(call.message.chat.id, photo_path, caption=f"{name}\n{description}")
        else:
            bot.send_message(call.message.chat.id, f"{name}\n{description}")

        markup = InlineKeyboardMarkup(row_width=1)
        if price_1_month > 0:
            period = 1
            markup.add(InlineKeyboardButton(f"1 месяц - {price_1_month} Руб.", callback_data=f"price_{name}_{period}_{price_1_month}"))
        if price_2_month > 0:
            period = 2
            markup.add(InlineKeyboardButton(f"2 месяца - {price_2_month} Руб.", callback_data=f"price_{name}_{period}_{price_2_month}"))
        if price_3_month > 0:
            period = 3
            markup.add(InlineKeyboardButton(f"3 месяца - {price_3_month} Руб.", callback_data=f"price_{name}_{period}_{price_3_month}"))
        if price_6_month > 0:
            period = 6
            markup.add(InlineKeyboardButton(f"6 месяцев - {price_6_month} Руб.", callback_data=f"price_{name}_{period}_{price_6_month}"))

        markup.add(InlineKeyboardButton(text="На главную", callback_data=f"back_to_user_menu"))
        bot.send_message(call.message.chat.id, "Выберите период:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "Ошибка выбора товара.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("price_"))
def handle_period_choice(call):
    idd, period, price = call.data.split("_")[1], call.data.split("_")[2], call.data.split("_")[3]

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text="Купить", callback_data=f"ПокаКупить_{idd}_{price}"))
    markup.add(InlineKeyboardButton(text="Купить за реф.деньги", callback_data=f"Купить за реф. деньги_{idd}_{price}"))
    markup.add(InlineKeyboardButton(text="Назад", callback_data="back_to_user_menu"))
    bot.send_message(call.message.chat.id, f"Вы выбрали {period} месяц(а) за {price} Руб. Как вы хотели бы произвести оплату?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ПокаКупить_"))
def handle_middle_buy(call):
    idd, price = call.data.split("_")[1], call.data.split("_")[2]
    delete_last_two_messages(call.message)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text="СБП", callback_data=f"Купить_{idd}_{price}_42"))
    markup.add(InlineKeyboardButton(text="Иностранные платежи", callback_data=f"ИноКупить_{idd}_{price}"))
    markup.add(types.InlineKeyboardButton(text="Ввести промокод", callback_data=f"Промокод_{idd}_{price}"))
    markup.add(InlineKeyboardButton(text="Назад", callback_data="back_to_user_menu"))
    bot.send_message(call.message.chat.id, f"Выберите способ оплаты:", reply_markup=markup)

def check_promocode(user_input_code):
    cursor.execute("SELECT * FROM promocodes WHERE code = ? AND is_active = 1", (user_input_code,))
    promo = cursor.fetchone()

    if promo:
        return True, promo[2]  # Если промокод найден, возвращается True и процент скидки
    else:
        return False, 0  # Если промокод не найден, возвращается False и 0

@bot.callback_query_handler(func=lambda call: call.data.startswith("ПромоКод"))
def handle_promocode_entry(call):
    msg = bot.send_message(call.message.chat.id, "Пожалуйста, введите ваш промокод:")
    bot.register_next_step_handler(msg, apply_promocode)



@bot.callback_query_handler(func=lambda call: call.data.startswith("Промокод_"))
def handle_promocode(call):
    idd, price = call.data.split("_")[1], call.data.split("_")[2]
    msg = bot.send_message(call.message.chat.id, "Введите промокод:")
    bot.register_next_step_handler(msg, apply_promocode, idd, price)

def apply_promocode(message, idd, price):    
    user_input_code = message.text
    is_valid, discount = check_promocode(user_input_code)
    
    if is_valid:
        new_price = float(price) * (1 - (discount / 100))  # Применяем скидку
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(text="СБП", callback_data=f"Купить_{idd}_{new_price}_42"))
        markup.add(types.InlineKeyboardButton(text="Иностранные платежи", callback_data=f"ИноКупить_{idd}_{new_price}"))
        markup.add(types.InlineKeyboardButton(text="Назад", callback_data="back_to_user_menu"))
        bot.send_message(message.chat.id, f"Промокод применен! Ваша скидка составляет {discount}%. Новая цена: {new_price:.2f}", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Промокод недействителен или неактивен. Пожалуйста, попробуйте еще раз.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("ИноКупить_"))
def handle_foreign_middle_buy(call):
    idd, price = call.data.split("_")[1], call.data.split("_")[2]
    delete_last_two_messages(call.message)
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(text="MASTERCARD RUB", callback_data=f"Купить_{idd}_{price}_8"))
    markup.add(InlineKeyboardButton(text="VISA RUB", callback_data=f"Купить_{idd}_{price}_4"))
    markup.add(InlineKeyboardButton(text="Назад", callback_data="back_to_user_menu"))
    bot.send_message(call.message.chat.id, f"Выберите способ оплаты:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("Купить_"))
def handle_buy(call):
    delete_last_two_messages(call.message)
    prod_name, price, i = call.data.split("_")[1], call.data.split("_")[2], call.data.split("_")[3]
    price = float(price)  
    order_id = str(int(time.time()))  
    payment_link = generate_payment_link(price, order_id, i)
    cursor.execute("SELECT id FROM products WHERE name=?", (prod_name,))
    prod_id = cursor.fetchone()
    add_order_to_db(call.message.chat.id, prod_id[0], price, order_id)
    bot.send_message(call.message.chat.id, f"Произведите оплату в течение 10 минут!\nПосле оплаты получите данные для входа. Есть вопросы пишите @TEXPOD_MPHelp\nВаша ссылка на оплату:{payment_link}", reply_markup=generate_user_markup())
    is_order_paid(order_id)

def handle_pay_type_keyboard():
    markup = ReplyKeyboardMarkup(row_width=1,resize_keyboard=True)
    markup.add("Иностранные платежи")
    markup.add("СБП")
    return markup

def handle_foreign_pay_keyboard():
    markup = ReplyKeyboardMarkup(row_width=1,resize_keyboard=True)
    markup.add("VISA RUB")
    markup.add("MASTERCARD RUB")
    return markup

def get_user_balance(user_id):
    try:
        cursor.execute("SELECT referral_balance FROM users WHERE tg_id=?", (user_id,))
        balance = cursor.fetchone()
        #print(balance)
        #print(user_id)
        if balance:
            return balance[0]
        else:
            return 0
    except Exception as e:
        print(e)
        return 0


def generate_order_id(user_id):
    timestamp = int(time.time())
    user_suffix = int(str(user_id)[-4:])
    return timestamp * 10000 + user_suffix

def add_order_to_db(user_id, product_id, price, order_id):
    status = "Не оплачен"  
    cursor.execute("INSERT INTO orders (order_id, user_id, product_id, price, status) VALUES (?, ?, ?, ?, ?)", 
                   (order_id, user_id, product_id, price, status))
    conn.commit()
    return order_id


def generate_payment_link(amount, order_id, i):
    nonce = int(time.time())

    api_url = "https://api.freekassa.ru/v1/orders/create"

    data = {
        'shopId': MERCHANT_ID,
        'nonce': nonce,
        'paymentId': order_id,
        'i': i,
        'email': 'no_email@mail.ru',
        'ip': '85.8.8.8',
        'amount': str(amount),
        'currency': 'RUB',
        'success': 'https://mpkey.org/successful_payment'
    }

    sorted_data = sorted(data.items())
    sign_string = "|".join(str(item[1]) for item in sorted_data)
    signature = hmac.new(api_key.encode('utf-8'), sign_string.encode('utf-8'), hashlib.sha256).hexdigest()

    response = requests.post(api_url, json={
            "nonce": nonce,
            "shopId": MERCHANT_ID,
            "paymentId": order_id,
            "i": i,
            "email": "no_email@mail.ru",
            "ip": "85.8.8.8",
            "amount": str(amount),
            "currency": "RUB",
            'success': 'https://mpkey.org/successful_payment',
            "signature":signature         
        })
    print(response.json())
    if response.status_code == 200:
        response_data = response.json()
        if 'location' in response_data:
            return response_data['location']
    
    return None

'''
def generate_payment_link(order_amount, order_info):
    base_url = "https://pay.freekassa.ru/"
    
    # Сгенерируем строку для подписи
    sign_string = f"{MERCHANT_ID}:{order_amount}:{SECRET_KEY}:RUB:{order_info}"
    sign_hash = hashlib.md5(sign_string.encode()).hexdigest()

    # Собираем все параметры в одну ссылку
    link = f"{base_url}?m={MERCHANT_ID}&oa={order_amount}&currency=RUB&o={order_info}&s={sign_hash}"

    return link
'''




@bot.callback_query_handler(func=lambda call: call.data.startswith("Купить за реф. деньги_"))
def handle_referral_buy(call):
    idd, price = call.data.split("_")[1], call.data.split("_")[2]
    price = float(price)
    user_tg_id = call.message.chat.id

    user_balance = get_user_balance(user_tg_id)

    if user_balance >= price:
        new_balance = user_balance - price


        cursor.execute("UPDATE users SET referral_balance=? WHERE tg_id=?", (new_balance, user_tg_id))

        #cursor.execute("SELECT name from products where id=?", (idd,))
        product = idd
        contact = send_contact_info(user_tg_id)
        end_date = get_end_date_of_product_price(idd,price)

        cursor.execute("SELECT tg_id from managers WHERE contacts=?", (contact,))
        manager_id = cursor.fetchone()[0]

        user_info = bot.get_chat(user_tg_id)
        to_name = user_info.username
        amount = price
        bot.send_message(user_tg_id, f"Благодарим Вас за доверие и приобретение ({product})❗️ Ваши реферальные деньги были списаны. Напишите вашему менеджеру {contact} плюс (+) в личные сообщения для получения доступа.", reply_markup=generate_user_markup())
        send_message_to_admins(f"РЕФ-ПОКУПКА\nПользователь с ID {user_tg_id} (@{to_name}) купил товар {product} за {amount} РЕФЕРАЛЬНЫХ рублей до {end_date}")
        bot.send_message(manager_id, f"РЕФ-ПОКУПКА\nСовершена покупка {product}, пользователем @{to_name} за {amount} РЕФЕРАЛЬНЫХ рублей до {end_date}")

        cursor.execute("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)", (user_tg_id, 1111111111))
        cursor.execute("UPDATE users SET total_purchases = total_purchases + 1 WHERE tg_id=?", (user_tg_id,))
        
        cursor.execute("SELECT referral_id FROM referrals WHERE user_id=?", (user_tg_id,))
        referral = cursor.fetchone()
        
        if referral:
            referral_id = referral[0]
            cursor.execute("SELECT * FROM managers WHERE tg_id=?", (referral_id,))
            manager = cursor.fetchone()
            
            if manager:
                cursor.execute("UPDATE managers SET total_purchases = total_purchases + 1, total_amount = total_amount + ?, all_total_amount = all_total_amount + ? WHERE tg_id=?", (amount, amount, referral_id))
            else:
                cursor.execute("UPDATE managers SET total_purchases = total_purchases + 1, total_amount = total_amount + ?, all_total_amount = all_total_amount + ? WHERE contacts=?", (amount, amount, contact))
        else:
            cursor.execute("UPDATE managers SET total_purchases = total_purchases + 1, total_amount = total_amount + ?, all_total_amount = all_total_amount + ? WHERE contacts=?", (amount, amount, contact))
        conn.commit()
    else:
        bot.send_message(call.message.chat.id, "У вас недостаточно реферальных денег для покупки этого товара.", reply_markup=generate_user_markup())




@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def handle_product_query(call):
    product_name = call.data.split("_")[1]
    cursor.execute("SELECT photo_path, description FROM products WHERE name=?", (product_name,))
    product = cursor.fetchone()

    if product:
        product_photo, product_description = product
        bot.send_photo(call.message.chat.id, photo=product_photo, caption=product_description)
    else:
        bot.answer_callback_query(call.id, text="Произошла ошибка. Пожалуйста, попробуйте позже.")



@bot.message_handler(func=lambda m: m.text == "Тех. поддержка💬")
def handle_contacts(message):
    bot.send_message(message.chat.id, "💭Если у Вас остались вопросы обращайтесь, будем рады: @TEXPOD_MPHelp", reply_markup=generate_user_markup())


@bot.message_handler(func=lambda m: m.text =="Рефералка👨‍👨‍👧‍👦")
def handle_referrals(message):
    send_referral_message(message.chat.id)


def get_manager_contact(user_id):
    cursor.execute("SELECT referral_id FROM referrals WHERE user_id = ?", (user_id,))
    referral = cursor.fetchone()
    
    if referral:
        referral_id = referral[0]
        
        cursor.execute("SELECT contacts FROM managers WHERE tg_id = ?", (referral_id,))
        manager = cursor.fetchone()
        
        if manager:  
            return manager[0] 
        else:
            cursor.execute("SELECT username FROM default_manager")
            default = cursor.fetchone()
            return default[0]
    else:
        cursor.execute("SELECT username FROM default_manager")
        default = cursor.fetchone()
        return default[0]


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "ref_link":
        user_id = call.message.chat.id
        name = bot.get_me().username
        referral_link = f'https://t.me/{name}?start={user_id}'
        delete_last_two_messages(call.message)
        bot.send_message(user_id, f"В боте включена реферальная система. приглашайте друзей и зарабатывайте на этом!\nВы будете получать: {BONUS_REFERRAL} от каждой покупки вашего реферала\nВаша реферальная ссылка: {referral_link}", reply_markup=generate_user_markup())
    elif call.data == "ref_balance":
        user_id = call.message.chat.id
        delete_last_two_messages(call.message)

        balance = get_user_balance(user_id)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM referrals WHERE referral_id = ?", (user_id,))
        referrals_from_bd = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM referrals WHERE referral_id = ? AND user_id IN (SELECT user_id FROM purchases)", (user_id,))
        real_referrals_from_bd = cursor.fetchone()[0]
        bot.send_message(user_id, f"Ваш реферальный баланс: {balance}\nКол-во переходов по ссылке: {referrals_from_bd}\nИз них оплатили: {real_referrals_from_bd}", reply_markup=generate_user_markup())
        
        balance_manager = get_manager_contact(user_id)
        bot.send_message(user_id, f"Ваш Телеграмм ID: {user_id}.\nДля списания баланса отправьте его менеджеру {balance_manager}")

    elif call.data == "my_referrals":
        user_id = call.message.chat.id
        delete_last_two_messages(call.message)

        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM referrals WHERE referral_id=?", (user_id,))
        referrals = cursor.fetchall()

        
        
        if referrals:
            referred_users_names = []
            for ref in referrals:
                try:
                    user_info = bot.get_chat(ref[0])
                    referred_users_names.append("@" + user_info.username if user_info.username else user_info.first_name)
                except Exception as e:
                    print(f"Unable to fetch info for user {ref[0]}: {e}")
                    referred_users_names.append(str(ref[0]))  
            referred_users = "\n".join(referred_users_names)
            bot.send_message(user_id, f"Ваши рефералы:\n{referred_users}", reply_markup=generate_user_markup())
        else:
            bot.send_message(user_id, "У вас пока нет рефералов.", reply_markup=generate_user_markup())
    elif call.data == "ref_mes_link":
        user_id = call.message.chat.id
        name = bot.get_me().username
        referral_link = f'https://t.me/{name}?start={call.message.chat.id}'
        bot.send_message(call.message.chat.id, f"Лучший доступ к сервисам аналитики можете приобрести здесь 🔥👇🏼\n{referral_link}\nПереходи по ссылке👆🏻 и следуй инструкции бота", reply_markup=generate_user_markup())
    elif call.data == "go_back_user":
        bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=generate_user_markup())


@bot.message_handler(func=lambda m: m.text == "Назад")
def main_user_keyboard(message):
    delete_last_two_messages(message)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=generate_user_markup())

@bot.callback_query_handler(func=lambda call: call.data == "Назад_user")
def main_user_keyboard_callback(call):
    delete_last_two_messages(call.message)
    bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=generate_user_markup())


def send_contact_info(user_id):
    while True:
        cursor.execute("SELECT referral_id FROM referrals WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.execute("SELECT username FROM default_manager LIMIT 1")
            default_manager_contact = cursor.fetchone()[0]
            return default_manager_contact
        
        # Обновляем user_id для следующей итерации
        user_id = result[0]
        
        # Проверяем, является ли найденный referral_id менеджером
        cursor.execute("SELECT contacts FROM managers WHERE tg_id = ?", (user_id,))
        manager_info = cursor.fetchone()
        if manager_info:
            return manager_info[0]  # Нашли менеджера, возвращаем его контакты
    
def get_product_name_by_order(order_id):
    try:
        cursor.execute("""
            SELECT p.name
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.order_id = ?
        """, (order_id,))
        
        result = cursor.fetchone()
        if result:
            return result[0]  
        else:
            return None  
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_end_date_of_product(order_id):
   
    cursor.execute("""
    SELECT price, price_1_month, price_2_month, price_3_month, price_6_month 
    FROM orders 
    INNER JOIN products ON orders.product_id = products.id 
    WHERE orders.order_id = ?
    """, (order_id,))
    
    order_info = cursor.fetchone()
        
    if order_info:
        price, price_1_month, price_2_month, price_3_month, price_6_month = order_info
        now = datetime.now()

        # Определяем срок действия продукта
        if price == price_1_month:
            end_date = now + timedelta(days=30)
        elif price == price_2_month:
            end_date = now + timedelta(days=60)
        elif price == price_3_month:
            end_date = now + timedelta(days=90)
        elif price == price_6_month:
            end_date = now + timedelta(days=180)
        else:
            # Если цена не соответствует ни одному из заранее определенных значений,
            return None 

        return end_date.strftime("%Y-%m-%d")

    else:
        return None 

def get_end_date_of_product_price(product_id, product_price):
       
    cursor.execute("""
    SELECT price_1_month, price_2_month, price_3_month, price_6_month 
    FROM products 
    WHERE name = ?
    """, (product_id,))
    
    product_info = cursor.fetchone()
    #print(product_info)
    if product_info:
        price_1_month, price_2_month, price_3_month, price_6_month = product_info
        now = datetime.now()

        # Определяем срок действия продукта на основе цены
        if product_price == price_1_month:
            end_date = now + timedelta(days=30)
        elif product_price == price_2_month:
            end_date = now + timedelta(days=60)
        elif product_price == price_3_month:
            end_date = now + timedelta(days=90)
        elif product_price == price_6_month:
            end_date = now + timedelta(days=180)
        else:
            # Если цена не соответствует ни одному из заранее определенных значений,
            return None 

        return end_date.strftime("%Y-%m-%d")

    else:
        return None 



def handle_order_status(order_info):
    
    order = order_info['orders'][0]
    status = order['status']
    merchant_order_id = order['merchant_order_id']
    amount = order['amount']

    cursor.execute("SELECT user_id FROM orders WHERE order_id=?", (merchant_order_id,))
    user_tg_id = cursor.fetchone()[0]    
    if status == 0:
        send_message(user_tg_id, "Срок ссылки истек, пожалуйста повторите операцию оплаты.")
    
    elif status == 1:
        cursor.execute("UPDATE orders SET status='Оплачен' WHERE order_id=?", (merchant_order_id,))

        product = get_product_name_by_order(merchant_order_id)
        contact = send_contact_info(user_tg_id)
        end_date = get_end_date_of_product(merchant_order_id)

        cursor.execute("SELECT tg_id from managers WHERE contacts=?", (contact,))
        manager_id = cursor.fetchone()[0]

        user_info = bot.get_chat(user_tg_id)
        to_name = user_info.username

        send_message(user_tg_id, f"Благодарим Вас за доверие и приобретение ({product})❗️Напишите вашему менеджеру {contact} плюс (+) в личные сообщения для получения доступа.")
        send_message_to_admins(f"Пользователь с ID {user_tg_id} (@{to_name}) купил товар {product} с ID {merchant_order_id} за {amount} рублей до {end_date}")
        bot.send_message(manager_id, f"Совершена покупка {product}, пользователем @{to_name} за {amount} рублей до {end_date}")

        cursor.execute("INSERT INTO purchases (user_id, product_id) VALUES (?, ?)", (user_tg_id, merchant_order_id))
        
        cursor.execute("SELECT total_purchases FROM users WHERE tg_id=?", (user_tg_id,))
        is_not_first_purchase = cursor.fetchone()[0]

        cursor.execute("UPDATE users SET total_purchases = total_purchases + 1 WHERE tg_id=?", (user_tg_id,))
        
        cursor.execute("SELECT referral_id FROM referrals WHERE user_id=?", (user_tg_id,))
        referral = cursor.fetchone()
        
        if referral:
            referral_id = referral[0]
            if is_not_first_purchase == 0:
                cursor.execute("UPDATE users SET referral_balance = referral_balance + ? WHERE tg_id=?", (BONUS_REFERRAL, referral_id))
            cursor.execute("SELECT * FROM managers WHERE tg_id=?", (referral_id,))
            manager = cursor.fetchone()
            
            if manager:
                cursor.execute("UPDATE managers SET total_purchases = total_purchases + 1, total_amount = total_amount + ?, all_total_amount = all_total_amount + ? WHERE tg_id=?", (amount, amount, referral_id))
            else:
                cursor.execute("UPDATE managers SET total_purchases = total_purchases + 1, total_amount = total_amount + ?, all_total_amount = all_total_amount + ? WHERE contacts=?", (amount, amount, contact))
        else:
            cursor.execute("UPDATE managers SET total_purchases = total_purchases + 1, total_amount = total_amount + ?, all_total_amount = all_total_amount + ? WHERE contacts=?", (amount, amount, contact))

    
    elif status == 8:
        cursor.execute("UPDATE orders SET status='Ошибка' WHERE order_id=?", (merchant_order_id,))
        send_message(user_tg_id, "Произошла ошибка, обратитесь в поддержку.")
    
    elif status == 9:
        cursor.execute("UPDATE orders SET status='Отменен' WHERE order_id=?", (merchant_order_id,))
        send_message(user_tg_id, "Операция отменена.")
    
    conn.commit()


def send_message(user_id, message):
    bot.send_message(chat_id=user_id, text=message, reply_markup=generate_user_markup())


def send_message_to_admins(message):
    for admin_id in admins:
        bot.send_message(chat_id=admin_id, text=message)

def is_order_paid(order_id):
    nonce = int(time.time())
    
    for i in range(20):
        time.sleep(30)
        nonce +=1
        data = {
            'shopId': MERCHANT_ID,
            'nonce': nonce,
            'paymentId': order_id,
            'page':0

        }
        sorted_data = sorted(data.items())
        sign_string = "|".join(str(item[1]) for item in sorted_data)
        signature = hmac.new(api_key.encode('utf-8'), sign_string.encode('utf-8'), hashlib.sha256).hexdigest()

    
        response = requests.post("https://api.freekassa.ru/v1/orders", json={
            "nonce": nonce,
            "shopId": MERCHANT_ID,
            'paymentId': order_id,
            'page':0,
            "signature": signature            
        })
        
        if response.status_code == 200:
            order_status = response.json()
            print(order_status)
            order = order_status['orders'][0]
            status = order['status']
            if status != 0:
                break
        else:
            print("Error: Failed to check order status", response.text)

    handle_order_status(order_status)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id in admins:
        root = message.from_user.first_name or message.from_user.username  
        keyboard_admin = admin_main_keyboard()
        bot.send_photo(message.chat.id, photo=open("./assets/hello_message/start.jpg", 'rb'), caption=f"""Приветствуем, администратор {root}""", reply_markup=keyboard_admin)
        return
    if is_manager(user_id):
        root = message.from_user.first_name or message.from_user.username  
        bot.send_photo(message.chat.id, photo=open("./assets/hello_message/start.jpg", 'rb'), caption=f"""Приветствуем, менеджер {root}""", reply_markup=generate_manager_keyboard(message))
        return
    if len(message.text.split()) > 1:
        referrer_id = message.text.split()[1]
        if referrer_id.isdigit():
            try:
                cursor.execute("SELECT * FROM users WHERE tg_id=?", (message.from_user.id,))
                user = cursor.fetchone()
                if not user:
                    cursor.execute("INSERT INTO users (tg_id, referrer_id) VALUES (?, ?)", (message.from_user.id, referrer_id))
                    add_referral(message.from_user.id, referrer_id)
                    conn.commit()
            except Exception as e:
                print(e)
    # Если нет referrer_id в сообщении, используем менеджера по умолчанию как referrer
    else:
        cursor.execute("SELECT username FROM default_manager")
        default_manager_username = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM managers WHERE contacts=?", (default_manager_username,))
        default_manager = cursor.fetchone()
        referrer_id = default_manager[0]
        try:
            cursor.execute("SELECT * FROM users WHERE tg_id=?", (message.from_user.id,))
            user = cursor.fetchone()
            if not user:
                cursor.execute("INSERT INTO users (tg_id, referrer_id) VALUES (?, ?)", (message.from_user.id, referrer_id))
                cursor.execute("UPDATE managers SET link_clicks=link_clicks + 1 WHERE tg_id=?", (referrer_id,))
                add_referral(message.from_user.id, referrer_id)
                conn.commit()
        except Exception as e:
            print(e)
    username = message.from_user.first_name or message.from_user.username  
    cursor.execute("SELECT message, image_path FROM welcome")
    data = cursor.fetchone()
    default_message = f"""Привет {username} ✌️\n"""
    if data:
        welcome_message, image_path = data
        if image_path:
            with open(image_path, 'rb') as image_file:
                bot.send_photo(message.chat.id, image_file, caption=default_message+welcome_message,reply_markup=generate_user_markup())
        elif welcome_message:
            bot.send_message(message.chat.id, default_message+welcome_message)
    else:
        bot.send_message(message.chat.id, default_message)

@bot.message_handler(commands=['add_manager'])
def add_manager(message):
    user_id = message.from_user.id
    if user_id not in admins:
        bot.send_message(message.chat.id, "Вы не администратор!")
        return

    try:
        manager_id = int(message.text.split()[1])
        
        user_info = bot.get_chat(manager_id)
        
        manager_name = user_info.first_name or user_info.username
        add_manager_to_db(manager_id, manager_name, "")
        
        bot.send_message(message.chat.id, f"Менеджер {manager_name} ({manager_id}) добавлен!")
        
    except IndexError:
        bot.send_message(message.chat.id, "Укажите ID менеджера для добавления!")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID!")


@bot.message_handler(commands=['remove_manager'])
def remove_manager(message):
    user_id = message.from_user.id
    if user_id not in admins:
        bot.send_message(message.chat.id, "Вы не администратор!")
        return

    try:
        manager_id = int(message.text.split()[1])
        if is_manager(manager_id):
            remove_manager_from_db(manager_id)
            bot.send_message(message.chat.id, f"Пользователь {manager_id} удален из менеджеров!")
        else:
            bot.send_message(message.chat.id, "Этот пользователь не является менеджером!")

    except IndexError:
        bot.send_message(message.chat.id, "Укажите ID менеджера для удаления!")
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат ID!")

if __name__ == "__main__":
    bot.polling(none_stop=True)
