from keyboards import (
    kb_start,
    kb_desc_len,
    kb_tone,
    kb_back_main_menu,
    kb_instr
)
from aiogram import types, Dispatcher
from create_bot import dp, bot, database, langs, instr_count
from jmespath import search
from AI import gpt
from loguru import logger as lg
from datetime import datetime
import openai
import asyncio
from random import randint
from config import preset_assistant
from state_machine_modul import BotStatesGroup
from dependencies.support_funcs import get_text, clean, edit

from config import sub_chat_id
async def check_sub(id):
    user_channel_status = await bot.get_chat_member(chat_id=sub_chat_id, user_id=id)
    if user_channel_status["status"] != 'left':
        return True
    else:
        return False

@lg.catch()
async def main_menu(call: types.CallbackQuery) -> None:
    if not await check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id
    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    await edit(chat_id, last_msg_id, await get_text("text.start_msg", chat_id), reply_markup=kb_start(chat_id))

    await BotStatesGroup.free.set()

@lg.catch()
async def main_menu_instr(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id
    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    await bot.delete_message(chat_id=chat_id, message_id=last_msg_id)
    msg = await bot.send_message(chat_id, await get_text("text.start_msg", chat_id), reply_markup=kb_start(chat_id))
    database.update(chat_id, "users", "last_msg_id", msg.message_id)
    await BotStatesGroup.free.set()

@lg.catch()
async def send_main_menu(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id
    msg = await bot.send_message(chat_id, await get_text("text.start_msg", chat_id), reply_markup=kb_start(chat_id))
    database.update(chat_id, "users", "last_msg_id", msg.message_id)
    await BotStatesGroup.free.set()
    await bot.answer_callback_query(call.id)


@lg.catch()
async def gpt_but(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return

    chat_id = call.message.chat.id
    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    await gpt.create_file(chat_id, preset_assistant)
    await edit(chat_id, last_msg_id, await get_text("text.gpt", chat_id), reply_markup=kb_back_main_menu(chat_id))
    await BotStatesGroup.gpt.set()
    await bot.answer_callback_query(call.id)

@lg.catch()
async def instruction(call: types.CallbackQuery) -> None:
    if not await check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id
    instr_count[chat_id] = 1
    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    text = await get_text("text.instruction", chat_id)
    await bot.delete_message(chat_id=chat_id, message_id=last_msg_id)
    msg = await bot.send_photo(chat_id=chat_id,
                               photo=open(f"content/instruction/{instr_count[chat_id]}.jpg", 'rb'),
                               caption=text,
                               reply_markup=kb_instr(chat_id))
    database.update(chat_id, "users", "last_msg_id", msg.message_id)
    await BotStatesGroup.instr.set()

    await bot.answer_callback_query(call.id)

@lg.catch()
async def generate(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id
    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    await edit(chat_id, last_msg_id, await get_text("text.generate", chat_id), reply_markup=kb_back_main_menu(chat_id))
    await BotStatesGroup.choose_product_name.set()

@lg.catch()
async def contacts(call: types.CallbackQuery) -> None:
    if not await check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id
    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    await edit(chat_id, last_msg_id, await get_text("text.contacts", chat_id), reply_markup=kb_back_main_menu(chat_id))
    await bot.answer_callback_query(call.id)


# Handlers register
def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        main_menu, text=['main_menu'], state=[None, BotStatesGroup.free,
                                              BotStatesGroup.choose_product_name,
                                              BotStatesGroup.choose_keywords, BotStatesGroup.end,
                                              BotStatesGroup.end, BotStatesGroup.generate, BotStatesGroup.gpt]
    )
    dp.register_callback_query_handler(
        main_menu_instr, text=['main_menu_instr'], state=BotStatesGroup.instr
    )
    dp.register_callback_query_handler(
        send_main_menu, text=['send_main_menu'], state=[None, BotStatesGroup.free,
                                              BotStatesGroup.choose_product_name,
                                              BotStatesGroup.choose_keywords, BotStatesGroup.end, BotStatesGroup.end,
                                              BotStatesGroup.generate]
    )
    dp.register_callback_query_handler(
        instruction, text=['instruction'], state=[None, BotStatesGroup.free]
    )
    dp.register_callback_query_handler(
        generate, text=['generate'], state=[None, BotStatesGroup.free, BotStatesGroup.choose_product_name, BotStatesGroup.choose_desc_len]
    )
    dp.register_callback_query_handler(
        contacts, text=['contacts'], state=[None, BotStatesGroup.free]
    )
    dp.register_callback_query_handler(
        gpt_but, text=['gpt'], state=[None, BotStatesGroup.free]
    )
