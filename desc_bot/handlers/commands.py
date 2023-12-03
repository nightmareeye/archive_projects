from keyboards import (
    kb_start,
    kb_desc_len,
    kb_tone,
    kb_sub
)

from aiogram import types, Dispatcher
from create_bot import dp, bot, database, langs
from jmespath import search
from config import config, preset_assistant, sub_chat_id
from AI import gpt
from loguru import logger as lg
from datetime import datetime
import openai
import asyncio
from random import randint

from state_machine_modul import BotStatesGroup
from dependencies.support_funcs import get_text, clean, edit

async def check_sub(id):
    user_channel_status = await bot.get_chat_member(chat_id=sub_chat_id, user_id=id)
    if user_channel_status["status"] != 'left':
        return True
    else:
        return False


# Команда /admin
@lg.catch()
async def command_stats(message: types.Message) -> None:
    chat_id = message.chat.id
    if chat_id in config["AdminList"]:
        text = (
            f"Всего пользователей: {database.get_users_count()}\n"
            f"Запросов сегодня: {database.read_admin('requests_today')}\n"
            f"Запросов за все время: {database.read_admin('requests_all')}\n"
            f"Потрачено токенов сегодня: {database.read_admin('tokens_today')}\n"
            f"Потрачено токенов за все время: {database.read_admin('tokens_all')}\n"
        )
        await bot.send_message(chat_id, text)
    else:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


@lg.catch()
async def command_excel(message: types.Message) -> None:
    database.excel_export()
    chat_id = message.chat.id
    if chat_id in config["AdminList"]:
        await message.reply_document(open('users.csv', 'rb'))
    else:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


# Команда /start
@lg.catch()
async def command_start(message: types.Message) -> None:
    chat_id = message.chat.id
    user_channel_status = await bot.get_chat_member(chat_id=sub_chat_id, user_id=message.from_user.id)
    if user_channel_status["status"] != 'left':
        if not database.isReg(chat_id):
            database.recording(id=chat_id, name=message.from_user.first_name)

        msg = await bot.send_message(chat_id, await get_text("text.start_msg", chat_id), reply_markup=kb_start(chat_id))
        database.update(chat_id, "users", "last_msg_id", msg.message_id)
        await BotStatesGroup.free.set()
    else:
        if not database.isReg(chat_id):
            database.recording(id=chat_id, name=message.from_user.first_name)
        msg = await bot.send_message(message.from_user.id, await get_text("text.no_sub", chat_id),
                                     reply_markup=kb_sub(chat_id))
        database.update(chat_id, "users", "last_msg_id", msg.message_id)



@lg.catch()
async def command_restart(message: types.Message) -> None:
    if not await check_sub(message.chat.id):
        await bot.delete_message(message.message_id)
        return
    chat_id = message.chat.id
    await gpt.create_file(chat_id, preset_assistant)  # Обновляем файл юзера

    await bot.send_message(chat_id, await get_text("text.restart", chat_id))
    await BotStatesGroup.gpt.set()
    command_start(message)





# Handlers register
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(
        command_start, commands=["start"], state=[None, BotStatesGroup.free, BotStatesGroup.gpt]
    )  # Command /start
    dp.register_message_handler(
        command_stats, commands=["stats"], state=[None, BotStatesGroup.free, BotStatesGroup.gpt]
    )  # Command /lang

    dp.register_message_handler(
        command_restart, commands=["restart"], state=[None, BotStatesGroup.free, BotStatesGroup.gpt]
    )  # Command /lang

    dp.register_message_handler(
        command_excel, commands=["excel"], state=[None, BotStatesGroup.free, BotStatesGroup.gpt]
    )  # Command /lang
