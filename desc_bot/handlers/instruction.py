from keyboards import (
    kb_instr

)

from config import preset, lens, tones

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
from create_bot import instr_count

async def instruction(call: types.CallbackQuery) -> None:

    chat_id = call.message.chat.id

    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    text = await get_text("text.instruction", chat_id)
    await bot.delete_message(chat_id=chat_id, message_id=last_msg_id)

    if call.data == "instr_right":
        instr_count[chat_id] += 1
        if instr_count[chat_id] > 7:
            instr_count[chat_id] = 1
    else:
        instr_count[chat_id] -= 1
        if instr_count[chat_id] < 1:
            instr_count[chat_id] = 7

    msg = await bot.send_photo(chat_id=call.message.chat.id,
                               photo=open(f"content/instruction/{instr_count[chat_id]}.jpg", 'rb'),
                               caption=text,
                               reply_markup=kb_instr(chat_id))
    database.update(chat_id, "users", "last_msg_id", msg.message_id)




# Handlers register
def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        instruction, text=['instr_left', 'instr_right'], state=[BotStatesGroup.instr]
    )
