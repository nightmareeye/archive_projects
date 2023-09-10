"""Парсинг телеграмм каналов"""
import json
from xlwt import Workbook
import xlwt
import click
import asyncio
from sentiment_analysis import Sentiment_textblob, take_text, save_in_json
from my_functions import check_chat, check_link, os, config, inv_chat, logger, dump_messages, dump_messages_to_json

api_id = config.api_id
api_hash = config.api_hash
session = 'session.session'
loop = asyncio.new_event_loop()

logger = logger.opt(colors=True)

global admins, members, users


@click.command()
@click.option('--link', default="https://t.me/BinanceRussian",
              help='Введите ссылку на чат/канал либо id чата/канала, в которых состоит пользователь, под чьим именем '
                   'используется скрипт. Обратите внимание, что некоторые TG-клиенты показывают ID чатов/каналов, '
                   'убирая значение -100 от начала ID')
@click.option(
    '--save_data', default=1, help='Введите "1" если нужно сохранить данные')
@click.option(
    '--time', default="2020-01-01", help='Введите дату в следующем формате год-месяц-день. Например "2023-05-02"')
def main(link, save_data, time):
    """Main"""
    global admins, members, users
    logger.debug("Запуск main")
    logger.info(f"Введёные параметры {link=}, {save_data=}, {time=} ")
    logger.info("Получаем чат пользователя, проверяем, что за ссылку он отправил и ожидаем правильной ссылки")
    while True:
        res = check_link(link)
        if not res:
            logger.warning('Неверная ссылка. Попробуйте другую.')
            return 0
        elif res == 'url' or res == 'id':
            if res == 'id':
                res = loop.run_until_complete(check_chat(link, 'id'))
            else:
                res = loop.run_until_complete(check_chat(link, 'url'))
            if res is not False and res['status'] == 'ok':
                logger.debug('res is not False and res["status"] == "ok"')
                members = res['members']
                admins = res['admins']
                chat = res['ch']
                users = res['users']
                channel_type = res['channel_type']
                channel_title = res['channel_title']
                break
            elif res is not False and res['status'] == 'error' and res['error_type'] == 'too_many_users':
                logger.debug("res is not False and res['status'] == 'error' and res['error_type'] == 'too_many_users'")
                chat = res['ch']
                channel_type = res['channel_type']
                channel_title = res['channel_title']
                break
            elif res is not False and res['status'] == 'no_comments':
                chat = res['ch']
                channel_type = res['channel_type']
                channel_title = res['channel_title']
                break
        elif res == 'close':
            logger.debug("res == 'close'")
            chat = loop.run_until_complete(inv_chat(link))
            res = loop.run_until_complete(check_chat(chat, 'url'))
            if res is not False and res['status'] == 'ok':
                logger.debug("res is not False and res['status'] == 'ok'")
                members = res['members']
                admins = res['admins']
                chat = res['ch']
                users = res['users']
                channel_type = 'чаты'
                channel_title = chat.title
                break
            elif res is not False and res['status'] == 'error' and res['error_type'] == 'too_many_users':
                logger.debug("res is not False and res['status'] == 'error' and res['error_type'] == 'too_many_users'")
                chat = res['ch']
                channel_type = 'чаты'
                channel_title = chat.title
                break
            elif res is not False and res['status'] == 'no_comments':
                channel_type = 'чаты'
                channel_title = chat.title
                break
    logger.debug(f"Создание папок канала {channel_title}")
    for x in ['\\', '|', '"', '/', ':',
              '?', '*', '<', '>']:
        channel_title = channel_title.replace(x, ' ')
    if os.path.exists(f'../data/чаты') is False:
        os.mkdir(f'../data/чаты')
    if os.path.exists(f'../data/каналы') is False:
        os.mkdir(f'../data/каналы')
    if os.path.exists(f'../data/{channel_type}/{channel_title}') is False:
        os.mkdir(f'../data/{channel_type}/{channel_title}')
    if res['status'] == 'ok':
        with open(f'../data/{channel_type}/{channel_title}/Участники {channel_title}.json', 'w', encoding='utf8') as f:
            with open(f'../data/{channel_type}/{channel_title}/Участники {channel_title}.txt', 'w',
                      encoding='utf8') as file:
                logger.debug(f"Запись доступных данных участников канала {channel_title}")

                all_users = {
                    'admins': admins,
                    'users': members
                }
                f.write(json.dumps(all_users, indent=4, ensure_ascii=False, ))
                if admins is not None:
                    file.write('Администраторы:\n')
                    for x in admins:
                        file.write(f'{str(admins[x])}\n')
                if len(members) > 0:
                    file.write('Пользователи:\n')
                    for x in members:
                        file.write(f'{str(members[x])}\n')
        wb = Workbook()
        style = xlwt.easyxf('pattern: pattern solid, fore_colour light_blue;'
                            'font: colour white, bold True;')
        n_list = 1
        sheet1 = wb.add_sheet(f'Users_{n_list}')
        sheet1.write(0, 0, 'Администраторы', style)
        sheet1.write(0, 1, 'ID', style)
        sheet1.write(0, 2, 'First Name', style)
        sheet1.write(0, 3, 'Last Name', style)
        sheet1.write(0, 4, 'Username', style)
        sheet1.write(0, 5, 'Телефон', style)
        sheet1.write(0, 6, 'Бот', style)
        sheet1.write(0, 7, 'Удалён', style)
        sheet1.write(0, 8, 'Скам', style)
        n = 1
        q = 1
        for x in users:
            sheet1.col(0).width = 256 * 17
            sheet1.col(1).width = 256 * 17
            sheet1.col(2).width = 256 * 25
            sheet1.col(3).width = 256 * 25
            sheet1.col(4).width = 256 * 25
            sheet1.col(5).width = 256 * 17
            sheet1.col(6).width = 256 * 7
            sheet1.col(7).width = 256 * 7
            sheet1.col(8).width = 256 * 7
            sheet1.write(n, 0, x['admin'])
            sheet1.write(n, 1, x['id'])
            sheet1.write(n, 2, x['first_name'])
            sheet1.write(n, 3, x['last_name'])
            sheet1.write(n, 4, x['username'])
            sheet1.write(n, 5, x['phone'])
            sheet1.write(n, 6, x['bot'])
            sheet1.write(n, 7, x['deleted'])
            sheet1.write(n, 8, x['scam'])
            n += 1
            q += 1
            if n == 30000:
                n_list += 1
                sheet1 = wb.add_sheet(f'Users_{n_list}"')
                n = 1
        wb.save(f'../data/{channel_type}/{channel_title}/Участники {channel_title}.xls')

    if str(save_data) == '1':
        logger.info(f"Сохранение сообщений канала {channel_title}")
        if os.path.exists(f'../data/чаты/{channel_title}') is False:
            os.mkdir(f'../data/чаты/{channel_title}')
        loop.run_until_complete(dump_messages(chat, channel_title))
        loop.run_until_complete(dump_messages_to_json(chat, channel_title, time))
        print(channel_title)
        sentiment_analyzer = Sentiment_textblob()
        data_channel = take_text(channel_title)
        save_in_json(channel_title, sentiment_analyzer.write_sentiment(data_channel))
    logger.info('\nСканирование закончено.')


if __name__ == "__main__":
    main()
