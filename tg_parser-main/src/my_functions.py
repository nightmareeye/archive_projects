import os
import re
import time
import string
import json
import sys

from telegram import Telegram
import plotly.graph_objects as go
# для корректного переноса времени сообщений в json
from datetime import date, datetime

from telethon.tl.functions.messages import GetHistoryRequest

import config

from telethon import TelegramClient, events, sync
from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantsSearch, Message, PeerUser, PeerChannel
from telethon import functions, errors
from loguru import logger

logger = logger.opt(colors=True)

api_id = config.api_id
api_hash = config.api_hash
session = 'session.session'


async def inv_chat(link):
    logger.debug("inv_chat")
    hash = link.rsplit('/', 1)[1]
    async with TelegramClient(session, api_id, api_hash) as client:
        try:
            await client(functions.messages.ImportChatInviteRequest(
                hash=hash))
            res = await client(functions.messages.CheckChatInviteRequest(
                hash=hash
            ))
            if res.chat.megagroup is False:
                logger.warning(
                    'Похоже, вы отправили ссылку на закрытый канал. Уьедитесь, что вы собираете информацию из группы.')
                exit()
        except errors.ChannelsTooMuchError:
            logger.warning('Вы вступили в слишком большое количество чатов')
            exit()
        except errors.InviteHashEmptyError:
            logger.warning('Хеш приглашения пуст.')
            exit()
        except errors.InviteHashExpiredError:
            logger.warning(
                'Срок действия чата, к которому пользователь пытался присоединиться, истек, и он больше не '
                'действителен.')
            exit()
        except errors.InviteHashInvalidError:
            logger.warning('Недействительная ссылка.')
            exit()
        except errors.SessionPasswordNeededError:
            logger.warning('Включена двухэтапная проверка, требуется пароль.')
            exit()
        except errors.UsersTooMuchError:
            logger.warning('Превышено максимальное количество пользователей (например, для создания чата).')
            exit()
        except errors.UserAlreadyParticipantError:
            res = await client(functions.messages.CheckChatInviteRequest(
                hash=hash
            ))
        return res.chat


async def check_chat(chat, type_link):
    # Проверка на то, является ли ссылка на чат чатом с последующей выгрузкой участников
    async with TelegramClient('session', api_id, api_hash) as client:
        try:
            logger.debug("Получаем сущность")
            if type_link == 'id':
                ch = await client.get_entity(int(chat))
            else:
                ch = await client.get_entity(chat)
            channel_type = 'чаты'
            if ch.__class__.__name__ == 'Channel':
                logger.debug("Передан telegram канал")
                if ch.megagroup is False:
                    logger.debug("Канал не megagroup ")
                    res = await client(functions.channels.GetFullChannelRequest(
                        channel=ch
                    ))
                    channel_type = 'каналы'
                    channel_title = ch.title
                    if len(res.chats) != 2:
                        logger.info("Канал не имеет закреплённого чата для комментариев")
                        return {'status': 'no_comments', 'ch': ch,
                                'channel_type': channel_type,
                                'channel_title': channel_title}
                    else:
                        logger.info("Канал имеет закреплённый чат для комментариев")
                        ch = await client.get_entity(res.chats[1])

                count_members = await client(functions.channels.GetFullChannelRequest(channel=ch))
                logger.debug("Полая информация о канале, включая список участников.")
                count_members = count_members.full_chat.participants_count
                logger.debug("Получения колличества участников")
                aggressive = False
                if count_members > 5000:
                    aggressive = True
                admins = []
                titles = {}
                async for user in client.iter_participants(ch, filter=ChannelParticipantsAdmins):
                    admins.append(user)
                    title = await client.get_permissions(ch, user)
                    titles[f'{title.participant.user_id}'] = title.participant.rank
                if len(admins) == 0:
                    admins = None
                else:
                    admins = list_users(admins, titles)
                logger.debug("Получили список админов")
                m = 1
                logger.info('Выполняется стандартный парсинг...')
                members = []
                if not aggressive:
                    logger.debug("Колличество участников < 5000")
                    async for user in client.iter_participants(ch):
                        members.append(user)
                else:
                    logger.debug("Колличество участников > 5000")
                    ids = []
                    try:
                        async for user in client.iter_participants(ch):
                            if m % 200 == 0:
                                time.sleep(1)
                            members.append(user)
                            ids.append(user.id)
                            m += 1
                    except Exception as e:
                        if str(e) == "'ChannelParticipants' object is not subscriptable":
                            pass
                    logger.info(
                        'Внимание! Следующая операция занимает продолжительное время: 15 минут для чата в 100 тысяч '
                        'пользователей.'
                        'Мы в процессе оптимизации.')

                    for num, x in enumerate(string.ascii_lowercase):
                        logger.info(
                            f'\rВыполняется расширенный поиск по алфавиту... {num}/{len(string.ascii_lowercase)} ',
                            end='')
                        m = 1
                        try:
                            async for user in client.iter_participants(ch, filter=ChannelParticipantsSearch(x)):
                                if m % 200 == 0:
                                    time.sleep(1)
                                if user.id in ids:
                                    continue
                                members.append(user)
                                ids.append(user.id)
                                m += 1
                        except Exception as e:
                            if str(e) == "'ChannelParticipants' object is not subscriptable":
                                continue
                if len(members) == 0:
                    members = None
                else:
                    members = list_users(members)
                if channel_type == 'каналы':
                    limit = 800
                    logger.info(
                        f'Собираем сообщения. В зависимости от ваших прошлый запросов, действие может занять '
                        f'продолжительное время.\n'
                        f'Лимит - {limit}')
                    mess = await client(functions.messages.GetHistoryRequest(
                        peer=ch,
                        offset_id=0,
                        offset_date=None,
                        add_offset=0,
                        limit=limit,
                        max_id=0,
                        min_id=0,
                        hash=0
                    ))
                    print()
                    mess_user = list_users(mess.users)
                    members = {**members, **mess_user}
                users = []
                logger.debug("Заполнение полей пользователей")
                for x in members:
                    user = {}
                    if admins is not None:
                        if str(members[x]['id']) in admins:
                            user['admin'] = admins[str(members[x]['id'])]['title']
                        else:
                            user['admin'] = ''
                    else:
                        user['admin'] = ''
                    user['id'] = members[x]['id']
                    user['first_name'] = members[x]['first_name']
                    if members[x]['last_name'] is None:
                        user['last_name'] = ''
                    else:
                        user['last_name'] = members[x]['last_name']
                    if members[x]['username'] is None:
                        user['username'] = ''
                    else:
                        user['username'] = members[x]['username']
                    if members[x]['phone'] is None:
                        user['phone'] = ''
                    else:
                        user['phone'] = members[x]['phone']
                    if members[x]['bot'] is False:
                        user['bot'] = ''
                    else:
                        user['bot'] = 'True'
                    if members[x]['deleted'] is False:
                        user['deleted'] = ''
                    else:
                        user['deleted'] = 'True'
                    if members[x]['scam'] is False:
                        user['scam'] = ''
                    else:
                        user['scam'] = 'True'
                    users.append(user)
                if channel_type != 'каналы':
                    channel_title = ch.title
                return {'status': 'ok', 'members': members, 'admins': admins,
                        'ch': ch, 'users': users, 'channel_type': channel_type,
                        'channel_title': channel_title}
            else:
                logger.warning('Вы ввели ссылку, которая не ведёт на открытую группу. Попробуйте другую.')
                return False
        except ValueError as e:
            logger.error(f"Необработанная ошибка {e}")
            return False


async def dump_messages(chat, title):
    """Выгружаем сообщения"""
    logger.debug("Функция dump_messages создаёт txt и html файлы с выводом всех постов и комментариев при наличии")
    async with TelegramClient(session, api_id, api_hash) as client:
        with open(f'../data/чаты/{title}/Сообщения {title}.txt', 'w', encoding='utf8') as file:
            with open(f'../data/чаты/{title}/Сообщения {title}.html', 'w', encoding='utf8') as f:
                f.write(f'<!DOCTYPE html>\n<html>\n    <head>\n        <meta charset="utf-8">\n    </head>\n    <body>')
                n = 0
                print(f'\n')
                async for message in client.iter_messages(chat):
                    n += 1
                    if n == 100:
                        logger.info(f'\rID текущего сообщения: {message.id} ', end='')
                        n = 0
                    file.write(f'{message}\n')
                    try:
                        if message.media is not None:
                            f.write(
                                f'<fieldset><legend>{message.from_id} | {message.date} </legend>'
                                f'Image. <br>{message.message}<br><br><small>'
                                f'Message id:{message.id}</small></fieldset>\n')
                        else:
                            f.write(
                                f'<fieldset><legend>{message.from_id} | {message.date} </legend>'
                                f'{message.message}<br><br><small>{message}</small></fieldset>\n')
                        f.write(f'    </body>\n</html>')
                    except Exception as e:
                        logger.error(e)


def check_link(link):
    logger.debug("Функция check_link определяет является параметр link - id или url телеграм канала")
    try:
        if int(link):
            logger.debug("Это id")
            return 'id'
    except Exception:
        logger.debug("--link не является типом int")
    logger.debug("Проверяем ссылку регулярной моделью и определяем, что хочет пользователь")
    if re.match(r'https://t.me/joinchat/[a-z-_0-9]{1}[a-z-_0-9]{4,}$', link.lower()) or re.match(
                r'https://t.me/joinchat/[a-z-_A-Z0-9]{1}[a-z-_0-9]{4,}$', link.lower()):
        logger.debug("res = 'close'")
        return 'close'
    elif re.match(r'https://t.me/[a-z]{1}[a-z_0-9]{4,31}$', link.lower()) or re.match(
            r'@[a-z]{1}[a-z_0-9]{4,31}$', link.lower()) or re.match(
            r'[a-z]{1}[a-z_0-9]{4,31}$', link.lower()):
        logger.debug("Это 'url'")
        return 'url'
    else:
        logger.warning('Не корректная ссылка ')
        return False


def list_users(*args):
    """Функция инициализатор"""
    logger.debug("Функция list_users возвращает поля пользователя")
    members = args[0]
    users = {}
    for user in members:
        users[f'{user.id}'] = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'phone': user.phone,
            'bot': user.bot,
            'deleted': user.deleted,
            'scam': user.scam,
        }
    if len(args) == 2:
        titles = args[1]
        for key, value in titles.items():
            users[key]['title'] = value
    return users


def to_json_file(channel_name):
    """Функция создаёт файл и записывает в него данные постов телеграмм канала"""
    logger.debug("Библиотека snscrape парсит соц.сети")
    post = []
    os.system(f"snscrape --max-results 10 --jsonl telegram-channel {channel_name} > text.txt")
    logger.warning("No public post list for this user")
    with open("../text.txt", "r", encoding="utf-8") as file:
        while True:
            line = file.readline()
            if not line:
                break
            data = json.loads(line)
            post.append(data)
    file.close()
    data = {"content": post}
    logger.debug("Сохранение в json формат")
    with open(f"../data/{channel_name}.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


async def dump_messages_to_json(chat, channel_title, time):
    """Выгружаем сообщения в JSON"""
    logger.debug("Функция dump_messages_to_json возвращает json файл с выводом всех постов и комментариев при наличии")
    comment_messages = []
    all_messages = []
    async with TelegramClient(session, api_id, api_hash) as client:
        class DateTimeEncoder(json.JSONEncoder):
            """Класс для сериализации записи дат в JSON"""
            logger.debug("Класс для сериализации записи дат в JSON")

            def default(self, o):
                if isinstance(o, datetime):
                    return o.isoformat()
                return json.JSONEncoder.default(self, o)

        try:
            async for message in client.iter_messages(chat):
                if message.date.strftime("%Y-%m-%d %H:%M:%S")[0:10] > time:
                    if isinstance(message, Message) and isinstance(message.from_id, PeerUser):
                        logger.debug("Сообщение написано пользователем => комментарий ")
                        if message.to_dict()["replies"]:
                            logger.debug("Существуют ответы на сообщение")
                            logger.debug("")
                            comment_dict = {
                                "from_id": message.from_id.user_id, "id": message.id,
                                "date": message.date,
                                "message": message.message,
                                "replies": message.to_dict()["replies"]["replies"],
                                "forwards": message.forwards,
                                "views": message.views}
                            comment_messages.append(comment_dict)
                        else:
                            logger.debug("Не существуют ответов на сообщение")
                            comment_dict = {
                                "from_id": message.from_id.user_id, "id": message.id,
                                "date": message.date,
                                "message": message.message,
                                "forwards": message.forwards,
                                "views": message.views}
                            comment_messages.append(comment_dict)
                    elif isinstance(message, Message) and isinstance(message.from_id, PeerChannel):
                        logger.debug("Сообщение написано каналом => пост ")
                        if message.to_dict()["replies"]:
                            logger.debug("Существуют ответы на пост")
                            info_dict = {
                                "from_id": message.from_id.channel_id, "id": message.id,
                                "date": message.date,
                                "title": message.message.split("\n")[0],
                                "hashtags": message.message.split("\n")[::-1][0],
                                "message": message.message,
                                "replies": message.to_dict()["replies"]["replies"],
                                "forwards": message.forwards,
                                "views": message.views,
                                "comments": comment_messages
                            }
                            all_messages.append(info_dict)
                            comment_messages = []
                        else:
                            logger.debug("Не существуют ответов на пост")
                            info_dict = {
                                "from_id": message.from_id.channel_id, "id": message.id,
                                "date": message.date,
                                "title": message.message.split("\n")[0],
                                "hashtags": message.message.split("\n")[::-1][0],
                                "message": message.message,
                                "forwards": message.forwards,
                                "views": message.views,
                                "comments": comment_messages
                            }
                            all_messages.append(info_dict)
                            comment_messages = []
                    else:
                        continue
        except Exception as e:
            logger.error(e)
        logger.debug("Сохранение в json формат")
        with open(f'../data/{channel_title}.json', 'w', encoding='utf8') as outfile:
            json.dump(all_messages, outfile, ensure_ascii=False, sort_keys=True, indent=4, cls=DateTimeEncoder)
