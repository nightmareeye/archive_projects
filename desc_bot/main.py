from aiogram.utils import executor
from create_bot import dp, bot
from loguru import logger as lg
from handlers import get_msg_text, commands, generate, main_menu, get_product_name, \
    get_keywords, get_prod_plus, get_stop_words, instruction, get_text_gpt, check_sub
from config import config
import asyncio
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz  # Для работы с часовыми поясами

from create_bot import database

async def today_updates() -> None:
    lg.info("EVERY DAY TASKS")
    database.update_requests_today(0)
    database.update_tokens_today(0)

async def on_startup(_) -> None:
    lg.info(f"Bot start polling")
    lg.info("SYSTEM - AioScheduler start")

async def on_shutdown(_) -> None:
    lg.info(f"Bot stop polling")

# Создаем объект scheduler
scheduler = AsyncIOScheduler(timezone=pytz.timezone('Europe/Moscow'))

# Регистрация всех хэндлеров
commands.register_handlers(dp)
get_msg_text.register_handlers(dp)
generate.register_handlers(dp)
main_menu.register_handlers(dp)
get_product_name.register_handlers(dp)
get_keywords.register_handlers(dp)
get_prod_plus.register_handlers(dp)
get_stop_words.register_handlers(dp)
instruction.register_handlers(dp)
get_text_gpt.register_handlers(dp)
check_sub.register_handlers(dp)

if __name__ == "__main__":
    lg.info(f"SYSTEM - Try to start Bot")

    # Задаем ежедневную задачу с учетом времени в часовом поясе Москвы
    scheduler.add_job(today_updates, 'cron', day_of_week='mon-sun', hour=config["UpdateTime"], minute=0, timezone=pytz.timezone('Europe/Moscow'))

    # Запускаем scheduler
    scheduler.start()

    # Запуск бота
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)