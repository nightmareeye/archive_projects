from keyboards import (
    kb_start,
    kb_confirm_stop_words
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
async def get_stop_words(message: types.Message):
    chat_id = message.chat.id
    stop_words = message.text
    await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    text = f"Стоп слова: {stop_words}\n\nВсе верно?"
    database.update(chat_id, "users", "stop_words", stop_words)
    await edit(chat_id, last_msg_id, text, reply_markup=kb_confirm_stop_words(chat_id))
    await BotStatesGroup.choose_stop_words.set()



# Handlers register
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(get_stop_words, state=[BotStatesGroup.choose_stop_words, BotStatesGroup.choose_prod_plus])