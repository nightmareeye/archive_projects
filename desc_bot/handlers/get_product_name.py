from keyboards import (
    kb_start,
    kb_confirm_product_name
)
from aiogram import types, Dispatcher
from create_bot import dp, bot, database, langs
from jmespath import search
from AI import gpt
from loguru import logger as lg
from datetime import datetime
import openai
import asyncio
import requests
from random import randint

from state_machine_modul import BotStatesGroup
from dependencies.support_funcs import get_text, clean, edit


def extract_product_name(json_str):
    key = '"imt_name":"'
    start_index = json_str.find(key) + len(key)
    end_index = json_str.find('"', start_index)
    if start_index != -1 and end_index != -1:
        product_name = json_str[start_index:end_index]
        return product_name
    else:
        print('Key not found')
        return None

def extract_product_description(json_str):
    key = '"description":"'
    start_index = json_str.find(key) + len(key)
    end_index = json_str.find('"', start_index)
    if start_index != -1 and end_index != -1:
        product_name = json_str[start_index:end_index]
        return product_name
    else:
        print('Key not found')
        return None

def link_handler(url):
    def extract_number(url):
        # Разделение строки по '/'
        parts = url.split('/')
        for part in parts:
            # Проверка, является ли часть строки числом
            if part.isdigit():
                return int(part)
        print('No number found in the URL')
        return None
    def get_basket_number(sku):
        intval = int(int(sku) / 1e5)
        if 0 <= intval <= 143:
            return 1
        if 144 <= intval <= 287:
            return 2
        if 288 <= intval <= 431:
            return 3
        if 432 <= intval <= 719:
            return 4
        if 720 <= intval <= 1007:
            return 5
        if 1008 <= intval <= 1061:
            return 6
        if 1062 <= intval <= 1115:
            return 7
        if 1116 <= intval <= 1169:
            return 8
        if 1170 <= intval <= 1313:
            return 9
        if 1314 <= intval <= 1601:
            return 10
        if 1602 <= intval <= 1655:
            return 11
        return 12  # Значение по умолчанию, если ни одно условие не выполняется

    def get_basket_vol(sku):
        limits = [0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]
        return int(sku[:limits[len(sku)]])

    def get_basket_part(sku):
        limits = [0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]
        return int(sku[:limits[len(sku) + 2]])

    sku = extract_number(url)
    basket_number = get_basket_number(sku)
    return f'https://basket-{basket_number:02d}.wb.ru/vol{get_basket_vol(sku)}/part{get_basket_part(sku)}/{sku}/info/ru/card.json'

@lg.catch()
async def get_product_name(message: types.Message):
    chat_id = message.chat.id
    product_data = link_handler(message.text)
    out = requests.request("GET",product_data)
    product_name = out.json()["imt_name"] + "\n" + out.json()["description"]
    await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    text = f"Ссылка на товар: {message.text}\nВсе верно?"
    database.update(chat_id, "users", "product_name", product_name)
    await edit(chat_id, last_msg_id, text, reply_markup=kb_confirm_product_name(chat_id))
    await BotStatesGroup.choose_desc_len.set()



# Handlers register
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(get_product_name, state=[BotStatesGroup.choose_product_name])