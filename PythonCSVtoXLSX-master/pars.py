import csv
from openpyxl import Workbook

# Открываем файл csv и читаем его содержимое
with open('csv.fixed.csv', 'r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='|')
    rows = list(csv_reader)

# Создаем новый файл Excel и добавляем заголовки столбцов
wb = Workbook()
ws = wb.active
ws.append(['ID', 'Name', 'FName', 'Phone', 'uid', 'nik', 'wo'])

# Добавляем данные из файла csv в таблицу Excel
for row in rows:
    # Удаляем пустые значения из строки
    row = [value.strip() for value in row if value.strip()]

    # Если строка не пустая, добавляем ее в таблицу
    if row:
        ws.append([row[0], row[1], row[3], row[4], row[5]])

# Сохраняем файл Excel
wb.save('output.xlsx')