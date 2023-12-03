from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from create_bot import langs, database
from jmespath import search
from config import channel_url

def get_text(code, id):

    return search(code, langs['rus'])

# Start Keyboard
def kb_start(id):
    kb_start_b1 = InlineKeyboardButton(get_text('buts.instruction', id), callback_data="instruction")
    kb_start_b2 = InlineKeyboardButton(get_text('buts.generate', id), callback_data="generate")
    kb_start_b3 = InlineKeyboardButton(get_text('buts.contacts', id), callback_data="contacts")
    kb_start_b4 = InlineKeyboardButton(get_text('buts.gpt', id), callback_data="gpt")

    kb_start = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_start.insert(kb_start_b1).insert(kb_start_b2).insert(kb_start_b3).insert(kb_start_b4)

    return kb_start


# Desc Length Keyboard
def kb_desc_len(id):
    kb_desc_len_b1 = InlineKeyboardButton(get_text('buts.short_paragraph', id), callback_data="short_paragraph")
    kb_desc_len_b2 = InlineKeyboardButton(get_text('buts.middle_paragraph', id), callback_data="middle_paragraph")
    kb_desc_len_b3 = InlineKeyboardButton(get_text('buts.big_paragraph', id), callback_data="big_paragraph")
    kb_desc_len_b4 = InlineKeyboardButton(get_text('buts.back', id), callback_data="generate")

    kb_desc_len = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_desc_len.insert(kb_desc_len_b1).insert(kb_desc_len_b2).insert(kb_desc_len_b3).insert(kb_desc_len_b4)

    return kb_desc_len


# Desc Length Keyboard
def kb_tone(id):
    kb_tone_b1 = InlineKeyboardButton(get_text('buts.neutral_tone', id), callback_data="neutral_tone")
    kb_tone_b2 = InlineKeyboardButton(get_text('buts.optimistic_tone', id), callback_data="optimistic_tone")
    kb_tone_b3 = InlineKeyboardButton(get_text('buts.friendly_tone', id), callback_data="friendly_tone")
    kb_tone_b4 = InlineKeyboardButton(get_text('buts.playful_tone', id), callback_data="playful_tone")
    kb_tone_b5 = InlineKeyboardButton(get_text('buts.sympathetic_tone', id), callback_data="sympathetic_tone")
    kb_tone_b6 = InlineKeyboardButton(get_text('buts.assertive_tone', id), callback_data="assertive_tone")
    kb_tone_b7 = InlineKeyboardButton(get_text('buts.formal_tone', id), callback_data="formal_tone")
    kb_tone_b8 = InlineKeyboardButton(get_text('buts.back', id), callback_data="choose_desc")

    kb_tone = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_tone.insert(kb_tone_b1).insert(kb_tone_b2).insert(kb_tone_b3).insert(kb_tone_b4).insert(kb_tone_b5).insert(kb_tone_b6).insert(kb_tone_b7).insert(kb_tone_b8)

    return kb_tone


def kb_back_main_menu(id):
    kb_back_main_menu_b1 = InlineKeyboardButton(get_text('buts.back', id), callback_data="main_menu")

    kb_back_main_menu = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_back_main_menu.insert(kb_back_main_menu_b1)
    return kb_back_main_menu

def kb_confirm_product_name(id):
    kb_confirm_product_name_b1 = InlineKeyboardButton(get_text('buts.yes', id), callback_data="choose_desc")
    kb_confirm_product_name_b2 = InlineKeyboardButton(get_text('buts.no', id), callback_data="generate")

    kb_confirm_product_name = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_confirm_product_name.insert(kb_confirm_product_name_b1).insert(kb_confirm_product_name_b2)
    return kb_confirm_product_name

def kb_back_to_tone(id):
    kb_confirm_keywords_b1 = InlineKeyboardButton(get_text('buts.back', id), callback_data="choose_tone")

    kb_back_to_tone = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_back_to_tone.insert(kb_confirm_keywords_b1)
    return kb_back_to_tone

def kb_confirm_keywords(id):
    kb_confirm_keywords_b1 = InlineKeyboardButton(get_text('buts.yes', id), callback_data="choose_prod_plus")
    kb_confirm_keywords_b2 = InlineKeyboardButton(get_text('buts.no', id), callback_data="choose_keywords")

    kb_confirm_keywords = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_confirm_keywords.insert(kb_confirm_keywords_b1).insert(kb_confirm_keywords_b2)
    return kb_confirm_keywords

def kb_back_to_keywords(id):
    kb_back_to_keywords_b1 = InlineKeyboardButton(get_text('buts.back', id), callback_data="choose_keywords")

    kb_back_to_keywords = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_back_to_keywords.insert(kb_back_to_keywords_b1)
    return kb_back_to_keywords


def kb_confirm_prod_plus(id):
    kb_confirm_prod_plus_b1 = InlineKeyboardButton(get_text('buts.yes', id), callback_data="choose_stop_words")
    kb_confirm_prod_plus_b2 = InlineKeyboardButton(get_text('buts.no', id), callback_data="choose_prod_plus")

    kb_confirm_prod_plus = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_confirm_prod_plus.insert(kb_confirm_prod_plus_b1).insert(kb_confirm_prod_plus_b2)
    return kb_confirm_prod_plus

def kb_back_to_prod_plus(id):
    kb_back_to_prod_plus_b1 = InlineKeyboardButton(get_text('buts.back', id), callback_data="choose_prod_plus")

    kb_back_to_prod_plus = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_back_to_prod_plus.insert(kb_back_to_prod_plus_b1)
    return kb_back_to_prod_plus

def kb_need_stop_words(id):
    kb_confirm_stop_words_b1 = InlineKeyboardButton(get_text('buts.yes', id), callback_data="need_end")
    kb_confirm_stop_words_b2 = InlineKeyboardButton(get_text('buts.no', id), callback_data="need_stop_words")

    kb_confirm_stop_words = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_confirm_stop_words.insert(kb_confirm_stop_words_b1).insert(kb_confirm_stop_words_b2)
    return kb_confirm_stop_words


def kb_confirm_stop_words(id):
    kb_confirm_stop_words_b1 = InlineKeyboardButton(get_text('buts.yes', id), callback_data="end")
    kb_confirm_stop_words_b2 = InlineKeyboardButton(get_text('buts.no', id), callback_data="choose_stop_words")

    kb_confirm_stop_words = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_confirm_stop_words.insert(kb_confirm_stop_words_b1).insert(kb_confirm_stop_words_b2)
    return kb_confirm_stop_words

def kb_generate(id):
    kb_generate_b1 = InlineKeyboardButton(get_text('buts.main_menu', id), callback_data="main_menu")
    kb_generate_b2 = InlineKeyboardButton(get_text('buts.generate', id), callback_data="generate")

    kb_generate = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_generate.insert(kb_generate_b1).insert(kb_generate_b2)
    return kb_generate

def kb_back_to_main_menu(id):
    kb_back_to_main_menu_b1 = InlineKeyboardButton(get_text('buts.main_menu', id), callback_data="send_main_menu")

    kb_back_to_main_menu = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb_back_to_main_menu.insert(kb_back_to_main_menu_b1)
    return kb_back_to_main_menu


def kb_instr(id):
    kb_instr_b1 = InlineKeyboardButton(get_text('buts.instr_left', id), callback_data="instr_left")
    kb_instr_b2 = InlineKeyboardButton(get_text('buts.main_menu', id), callback_data="main_menu_instr")
    kb_instr_b3 = InlineKeyboardButton(get_text('buts.instr_right', id), callback_data="instr_right")

    kb_instr = InlineKeyboardMarkup(row_width=3, resize_keyboard=True)
    kb_instr.insert(kb_instr_b1).insert(kb_instr_b2).insert(kb_instr_b3)
    return kb_instr


def kb_sub(id):
    kb_sub_b1 = InlineKeyboardButton(get_text('buts.subscribe', id), url=channel_url)
    kb_sub_b2 = InlineKeyboardButton(get_text('buts.check_sub', id), callback_data="check_sub")

    kb_sub = InlineKeyboardMarkup(row_width=1, resize_keyboard=True)
    kb_sub.insert(kb_sub_b1).insert(kb_sub_b2)
    return kb_sub






