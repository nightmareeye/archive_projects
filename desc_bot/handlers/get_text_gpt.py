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

from config import sub_chat_id
async def check_sub(id):
    user_channel_status = await bot.get_chat_member(chat_id=sub_chat_id, user_id=id)
    if user_channel_status["status"] != 'left':
        return True
    else:
        return False

@lg.catch()
async def get_text_gpt(message: types.Message):
    if not await check_sub(message.chat.id):
        await bot.delete_message(message.chat.id, message_id=message.message_id)
        return
    try:
        await BotStatesGroup.in_progress.set()
        chat_id = message.chat.id
        msg = await bot.send_message(
            chat_id, await get_text("", chat_id)
        )
        msg = await bot.send_message(
            chat_id, await get_text("text.waitAnswer", chat_id)
        )
        database.update(chat_id, "users", "last_msg_id", msg.message_id)
        request = await clean(message.text)
        await gpt.update_user_file(chat_id, request)
        answer = await gpt.get_response_gpt_3_5(chat_id)
        await edit(
            chat_id,
            database.read(chat_id, "users", "last_msg_id"),
            answer,
        )

    except openai.error.RateLimitError as e:
        lg.error(f"{e} from id: {chat_id}")
        await edit(
            chat_id,
            database.read(chat_id, "users", "last_msg_id"),
            await get_text("text.noTokens", chat_id),
        )
    except Exception as e:
        lg.error(f"{e} from id: {chat_id}")
        await edit(
            chat_id,
            database.read(chat_id, "users", "last_msg_id"),
            await get_text("text.largeContext", chat_id),
        )

    await BotStatesGroup.gpt.set()


# Handlers register
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(get_text_gpt, state=BotStatesGroup.gpt)