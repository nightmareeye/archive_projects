from keyboards import (
    kb_start,
    kb_confirm_prod_plus
)
from aiogram import types, Dispatcher
from create_bot import dp, bot, database, langs
from jmespath import search
from AI import gpt
from loguru import logger as lg
from datetime import datetime
import openai
import asyncio
from random import randint

from state_machine_modul import BotStatesGroup
from dependencies.support_funcs import get_text, clean, edit


@lg.catch()
async def get_prod_plus(message: types.Message):
    chat_id = message.chat.id
    prod_plus = message.text
    await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    text = f"Преимущества: {prod_plus}\n\nВсе верно?"
    database.update(chat_id, "users", "prod_plus", prod_plus)
    await edit(chat_id, last_msg_id, text, reply_markup=kb_confirm_prod_plus(chat_id))
    await BotStatesGroup.choose_prod_plus.set()



# Handlers register
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(get_prod_plus, state=[BotStatesGroup.choose_prod_plus])