from keyboards import (
    kb_sub,
    kb_start

)

from config import preset, lens, tones, sub_chat_id

from aiogram import types, Dispatcher
from create_bot import dp, bot, database, langs
from jmespath import search
from loguru import logger as lg

from state_machine_modul import BotStatesGroup
from dependencies.support_funcs import get_text, clean, edit


async def check_suba(call: types.CallbackQuery) -> None:
    chat_id = call.message.chat.id
    user_channel_status = await bot.get_chat_member(chat_id=sub_chat_id, user_id=call.message.chat.id)
    if user_channel_status["status"] != 'left':
        if not database.isReg(chat_id):
            database.recording(id=chat_id, name=message.from_user.first_name)

        last_msg = database.read(chat_id, "users", "last_msg_id")
        await edit(chat_id, last_msg, await get_text("text.start_msg", chat_id), reply_markup=kb_start(chat_id))
        await BotStatesGroup.free.set()
    else:
        await bot.answer_callback_query(call.id, text="Подписка не оформлена!")




# Handlers register
def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        check_suba, text='check_sub', state=[None, BotStatesGroup.free]
    )