from keyboards import (
    kb_start,
    kb_desc_len,
    kb_tone
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

# Модуль с функциями для статистики
"""from dependencies.statistic import update_requests_count
from dependencies.support_funcs import inProgress, get_text, \
    editclean"""


# Прием сообщений
@lg.catch()
async def get_message_trash(message: types.Message):
    chat_id = message.chat.id
    await bot.delete_message(chat_id=chat_id, message_id=message.message_id)


# Handlers register
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        get_message_trash, state=[BotStatesGroup.in_progress, BotStatesGroup.free, None, BotStatesGroup.choose_desc_len,
                                  BotStatesGroup.choose_tone, BotStatesGroup.end, BotStatesGroup.generate]
    )  # Receiving messages handler
