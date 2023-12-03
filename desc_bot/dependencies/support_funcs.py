from aiogram import types, Dispatcher
from create_bot import dp, bot, database, langs, users_langs
from jmespath import search
from random import randint


async def get_text(code, id):

    return search(code, langs['rus'])

# Очистить строку для записи в файл ChatGPT
async def clean(string):
    return (
        string.replace("'", "")
        .replace('"', "")
        .replace("\n", "")
        .replace("/", "//")
    )

# Изменить текст
async def edit(chat_id, message_id, text, reply_markup=None, parse_mode=None):
    msg = await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
        disable_web_page_preview=True,
    )
    database.update(chat_id, "users", "last_msg_id", msg.message_id)