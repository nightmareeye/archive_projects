from config import config
from loguru import logger as lg
import psycopg2
from psycopg2 import pool
import os
import csv


# Класс БД
class Database:
    # Инициализация
    def __init__(self):
        try:
            # Пытаемся подключиться к базе данных
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=os.environ["POSTGRES_HOST"],
                user=os.environ["POSTGRES_USER"],
                password=os.environ["POSTGRES_PASSWORD"],
                database=os.environ["POSTGRES_DB"],
                port=os.environ["POSTGRES_PORT"],
            )
            lg.info("SYSTEM - Connection to database complete")

        except Exception as e:
            # В случае сбоя подключения будет выведено сообщение в STDOUT
            lg.error(e)
            lg.error("ERROR - Can`t establish connection to database")
            return

        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                                CREATE TABLE IF NOT EXISTS users (id VARCHAR(255),name VARCHAR(255),last_msg_id  VARCHAR(255),lang VARCHAR(255),product_name VARCHAR(255),desc_len VARCHAR(255),tone VARCHAR(255),keywords VARCHAR(2048),stop_words VARCHAR(255),prod_plus VARCHAR(255),num_of_text VARCHAR(255),)"""
                    )
                    lg.info("DB CREATED")
                    cursor.execute(
                        f"""
                                CREATE TABLE IF NOT EXISTS admin (tokens_all VARCHAR(255),tokens_today VARCHAR(255),users_count VARCHAR(255),requests_today VARCHAR(255),requests_all VARCHAR(255))"""
                    )
                    cursor.execute(f"SELECT FROM admin")
                    if cursor.fetchone() is None:
                        cursor.execute(
                            "INSERT INTO admin VALUES (%s, %s, %s, %s, %s)",
                            ("0", "0", "0", "0", "0"),
                        )

        except Exception as e:
            print(e)

        finally:
            self.release_connection(connection)

    def get_connection(self):
        return self.connection_pool.getconn()

    def release_connection(self, connection):
        self.connection_pool.putconn(connection)

    # Запись нового пользователя -> users
    def recording(self, id, name):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT id FROM users WHERE id = '{id}'")
                    if cursor.fetchone() is None:
                        cursor.execute(
                            "INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (str(id), name, "0", "rus", "0", "0", "0", "0", "0", "0"),
                        )
        finally:
            self.release_connection(connection)

    # Проверка на нового пользователя
    def isReg(self, id):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT id FROM users WHERE id = %s", (str(id),))
                    if cursor.fetchone() is None:
                        return False
                    else:
                        return True
        finally:
            self.release_connection(connection)

    # Обновить запись
    def update(self, id, table, object, value):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE {table} SET {object} = %s WHERE id = %s",
                        (
                            value,
                            str(id),
                        ),
                    )
        finally:
            self.release_connection(connection)

    # Получить запись
    def read(self, id, table, object):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT {object} FROM {table} WHERE id = %s", (str(id),))
                    result = cursor.fetchall()
                    return result[0][0]
        finally:
            self.release_connection(connection)

    # Обновить запись
    def update_tokens_all(self, value):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE admin SET tokens_all = %s",
                        (value,),
                    )
        finally:
            self.release_connection(connection)

    def update_tokens_today(self, value):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE admin SET tokens_today = %s",
                        (value,),
                    )
        finally:
            self.release_connection(connection)

    def update_users_count(self, value):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE admin SET users_count = %s",
                        (value,),
                    )
        finally:
            self.release_connection(connection)

    def update_requests_today(self, value):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE admin SET requests_today = %s",
                        (value,),
                    )
        finally:
            self.release_connection(connection)

    def update_requests_all(self, value):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE admin SET requests_all = %s",
                        (value,),
                    )
        finally:
            self.release_connection(connection)

    def get_users_count(self):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT id FROM users")
                    result = cursor.fetchall()
                    return len(result)
        finally:
            self.release_connection(connection)


    def get_users(self):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT id FROM users")
                    result = cursor.fetchall()
                    return len(result)
        finally:
            self.release_connection(connection)

    def read_admin(self, value):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT {value} FROM admin")
                    result = cursor.fetchall()
                    return result[0][0]
        finally:
            self.release_connection(connection)


    def excel_export(self):
            connection = self.get_connection()
            try:
                with connection:
                    with connection.cursor() as cursor:
                        copy_sql = f"COPY users TO STDOUT WITH CSV HEADER"
                        with open('users.csv', 'w', encoding='utf-8') as csv_file:
                            cursor.copy_expert(sql=copy_sql, file=csv_file)

                        return 1
            finally:
                self.release_connection(connection)


"""    def excel_export(self):
        connection = self.get_connection()
        try:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM users")
                    results = cursor.fetchall()
                    with open("users.csv", 'w', newline='', encoding='utf-8') as csv_file:
                        csv_writer = csv.writer(csv_file)
                        # Записываем заголовки столбцов (если нужно)
                        column_names = [desc[0] for desc in cursor.description]
                        csv_writer.writerow(column_names)
                        # Записываем данные
                        csv_writer.writerows(results)

                    return 1
        finally:
            self.release_connection(connection)"""