from aiogram.dispatcher.filters.state import StatesGroup, State

class BotStatesGroup(StatesGroup):

    free = State()
    in_progress = State()


    choose_product_name = State()
    choose_desc_len = State()
    choose_tone = State()
    choose_keywords = State()
    choose_prod_plus = State()
    need_stop_words = State()
    choose_stop_words = State()
    end = State()
    gpt = State()
    generate = State()

    instr = State()

