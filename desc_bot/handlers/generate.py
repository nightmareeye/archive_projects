from keyboards import (
    kb_start,
    kb_desc_len,
    kb_tone,
    kb_confirm_keywords,
    kb_back_to_tone,
    kb_back_to_keywords,
    kb_generate,
    kb_back_to_prod_plus,
    kb_back_main_menu,
    kb_back_to_main_menu,
    kb_need_stop_words

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
from config import sub_chat_id
async def check_sub(id):
    user_channel_status = await bot.get_chat_member(chat_id=sub_chat_id, user_id=id)
    if user_channel_status["status"] != 'left':
        return True
    else:
        return False

@lg.catch()
async def desc_len(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id

    if call.data != "choose_tone":
        database.update(chat_id, "users", "desc_len", call.data)

    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    await edit(chat_id, last_msg_id, await get_text("text.tone", chat_id), reply_markup=kb_tone(chat_id))
    await BotStatesGroup.choose_tone.set()

@lg.catch()
async def tone(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id
    if call.data != "choose_keywords":
        database.update(chat_id, "users", "tone", call.data)

    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    await edit(chat_id, last_msg_id, await get_text("text.keywords", chat_id), reply_markup=kb_back_to_tone(chat_id))
    await BotStatesGroup.choose_keywords.set()

@lg.catch()
async def confirm_product_name(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id

    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    await edit(chat_id, last_msg_id, await get_text("text.desc_len", chat_id), reply_markup=kb_desc_len(chat_id))
    await BotStatesGroup.choose_desc_len.set()


@lg.catch()
async def confirm_keywords(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id

    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    await edit(chat_id, last_msg_id, await get_text("text.choose_prod_plus", chat_id), reply_markup=kb_back_to_keywords(chat_id))
    await BotStatesGroup.choose_prod_plus.set()

@lg.catch()
async def confirm_prod_plus(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id

    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    await edit(chat_id, last_msg_id, await get_text("text.need_stop_words", chat_id), reply_markup=kb_need_stop_words(chat_id))
    await BotStatesGroup.need_stop_words.set()

@lg.catch()
async def choose_need_stop_words(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id

    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    await edit(chat_id, last_msg_id, await get_text("text.choose_stop_words", chat_id), reply_markup=kb_back_to_prod_plus(chat_id))
    await BotStatesGroup.choose_stop_words.set()


async def end(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id

    last_msg_id = database.read(chat_id, "users", "last_msg_id")
    text = f"Название товара: {database.read(chat_id, 'users', 'product_name')}\n\n" \
           f"Длина описания: {lens[database.read(chat_id, 'users', 'desc_len')]}\n\n" \
           f"Тональность: {tones[database.read(chat_id, 'users', 'tone')]}\n\n" \
           f"Ключевые слова: {database.read(chat_id, 'users', 'keywords')}\n\n" \
           f"Стоп слова: {database.read(chat_id, 'users', 'stop_words')}\n\n" \
           f"Преимущества: {database.read(chat_id, 'users', 'prod_plus')}\n\n" \
           f"Для генерации описания используйте соотвествующую кнопку"
    await edit(chat_id, last_msg_id, text, reply_markup=kb_generate(chat_id))
    await BotStatesGroup.end.set()

async def generate(call: types.CallbackQuery) -> None:
    if not await  check_sub(call.message.chat.id):
        await bot.answer_callback_query(call.id, "Вы не подписаны на канал!", show_alert=True)
        return
    chat_id = call.message.chat.id
    try:
        await BotStatesGroup.in_progress.set()
        await edit(
            chat_id,
            database.read(chat_id, "users", "last_msg_id"),
            "⌛️",
        )
        request = f"""name: {database.read(chat_id, 'users', 'product_name')}
           description length: {lens[database.read(chat_id, 'users', 'desc_len')]}
           text tone: {tones[database.read(chat_id, 'users', 'tone')]}
           keywords: {database.read(chat_id, 'users', 'keywords')}
           negative keywords: {database.read(chat_id, 'users', 'stop_words')}
           product benefits: {database.read(chat_id, 'users', 'prod_plus')}
           generate a description in the query language"""
        await gpt.create_file(chat_id, preset)
        await gpt.update_user_file(chat_id, await clean(request))
        answer = await gpt.get_response_gpt_3_5(chat_id)
        await edit(
            chat_id,
            database.read(chat_id, "users", "last_msg_id"),
            answer,
            reply_markup=kb_back_to_main_menu(chat_id)
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

    await BotStatesGroup.free.set()



# Handlers register
def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(
        desc_len, text=['short_paragraph', 'middle_paragraph', 'big_paragraph', 'choose_tone'], state=[BotStatesGroup.choose_desc_len, BotStatesGroup.choose_keywords]
    )
    dp.register_callback_query_handler(
        tone, text=['neutral_tone', 'optimistic_tone', 'friendly_tone',
                    'playful_tone', 'sympathetic_tone', 'assertive_tone', 'formal_tone', 'choose_keywords'], state=[BotStatesGroup.choose_desc_len,BotStatesGroup.choose_tone, BotStatesGroup.choose_keywords]
    )
    dp.register_callback_query_handler(
        confirm_product_name, text=['choose_desc'], state=[BotStatesGroup.choose_desc_len, BotStatesGroup.choose_tone]
    )

    dp.register_callback_query_handler(
        confirm_keywords, text=['choose_prod_plus'], state=[BotStatesGroup.choose_prod_plus, BotStatesGroup.choose_keywords, BotStatesGroup.choose_stop_words]
    )
    dp.register_callback_query_handler(
        confirm_prod_plus, text=['need_stop_words'],
        state=[BotStatesGroup.choose_prod_plus, BotStatesGroup.choose_keywords, BotStatesGroup.need_stop_words, BotStatesGroup.end]
    )
    dp.register_callback_query_handler(
        choose_need_stop_words, text=['choose_stop_words'],
        state=[BotStatesGroup.choose_prod_plus, BotStatesGroup.choose_keywords, BotStatesGroup.need_stop_words, BotStatesGroup.choose_stop_words, BotStatesGroup.end]
    )
    dp.register_callback_query_handler(
        end, text=['end'],
        state=[BotStatesGroup.choose_prod_plus, BotStatesGroup.choose_keywords, BotStatesGroup.end, BotStatesGroup.need_stop_words, BotStatesGroup.choose_stop_words]
    )

    dp.register_callback_query_handler(
        generate, text=['generate'],
        state=[BotStatesGroup.end, BotStatesGroup.generate]
    )