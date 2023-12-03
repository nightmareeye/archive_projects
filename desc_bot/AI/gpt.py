import openai
from config import config
from create_bot import database
import json, ast
import asyncio


# Создание файла диалога
async def create_file(id, gpt_preset):
    d = [{'role': 'system', 'content': gpt_preset}]
    with open(f'{config["DialogsDir"]}{id}.json', "w", encoding="utf-8") as f:
        json.dump(d, f)


# Обновление файла диалога, сообщение от юзера
async def update_user_file(id, message):
    with open(f'{config["DialogsDir"]}{id}.json', "r", encoding="utf-8") as f:
        d = json.load(f)
        data = {"role": "user", "content": message}
        d.append(data)
    with open(f'{config["DialogsDir"]}{id}.json', "w", encoding="utf-8") as f:
        json.dump(d, f)



# Обновление файла диалога, ответ от GPT
async def update_assistant_file(id, message):
    with open(f'{config["DialogsDir"]}{id}.json', "r", encoding="utf-8") as f:
        d = json.load(f)
        data = {"role": "assistant", "content": message}
        d.append(data)
    with open(f'{config["DialogsDir"]}{id}.json', "w", encoding="utf-8") as f:
        json.dump(d, f)


# Получить файл диалога
async def get_content(id):
    openai.api_key = config["APIToken"]  # Init OpenAI API Key

    with open(f'{config["DialogsDir"]}{id}.json', "r", encoding="utf-8") as f:
        d = json.load(f)

        return d


# Получить ответ на вопрос от GPT
async def get_response_gpt_3_5(id):
    openai.api_key = config["APIToken"]  # Init OpenAI API Key
    content = await get_content(id)
    def response(content):
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=content)

        tokens_today = int(database.read_admin('tokens_today')) + int(response['usage']['total_tokens'])
        database.update_tokens_today(tokens_today)
        tokens_all = int(database.read_admin('tokens_all')) + int(response['usage']['total_tokens'])
        database.update_tokens_all(tokens_all)

        reqs_today = int(database.read_admin('requests_today'))
        database.update_requests_today(reqs_today + 1)
        reqs_all = int(database.read_admin('requests_all'))
        database.update_requests_all(reqs_all + 1)

        return response


    coro = asyncio.to_thread(response, content)
    result = await coro

    await update_assistant_file(
        id,
        result["choices"][0]["message"]["content"]
        .replace("\n", "")
        .replace("'", "")
        .replace('"', ""),
    )

    return result["choices"][0]["message"]["content"]