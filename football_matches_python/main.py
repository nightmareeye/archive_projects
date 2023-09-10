from sys import argv, exit
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QTableWidget, \
    QPushButton, QComboBox, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import QSize, pyqtSlot
from DataParser import DataParser
import models
from database import init_db, get_db, SESSIONLOCAL

init_db()

Database = SESSIONLOCAL
database = Database()

class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.scene = None
        self.table = None
        self.dump1 = None
        self.dump2 = None
        self.dump3 = []
        self.data = None
        self.show_scene('Команды', 8, ["Команда", "Дивизион", "Формат", "Тренер",
                                       "Дата", "Стадион", "Время", "Желаемое Время"], self.enter2)
        #self.scene3()

    def show_scene(self, title, cols, headers, func):
        self.setWindowTitle(title)
        self.setMinimumSize(QSize(1080, 800))
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        grid_layout = QGridLayout(self)
        central_widget.setLayout(grid_layout)

        self.table = QTableWidget(self)
        self.table.setColumnCount(cols)
        self.table.setRowCount(1)
        self.table.setHorizontalHeaderLabels(headers)
        for i in range(cols):
            self.table.setItem(0, i, QTableWidgetItem(''))

        button_enter = QPushButton('Ввод', self)
        button_enter.clicked.connect(func)

        button_clear = QPushButton('Добавить команду', self)
        button_clear.clicked.connect(self.insert)

        grid_layout.addWidget(self.table, 0, 0)
        inner_grid = QGridLayout(self)
        grid_layout.addLayout(inner_grid, 0, 1)
        inner_grid.addWidget(button_clear, 0, 0)
        inner_grid.addWidget(button_enter, 1, 0)

    def scene3(self):
        self.setWindowTitle("Предыдущие игры")
        self.setMinimumSize(QSize(1080, 800))
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(self)
        central_widget.setLayout(grid_layout)

        self.cb = QComboBox()

        self.cb.addItem("Дивизион")
        for i in list(self.data.keys()):
            self.cb.addItem(i)

        self.cb.currentIndexChanged.connect(self.selection_change)
        self.table = QTableWidget(self)

        button_enter = QPushButton('Ввод', self)
        button_enter.clicked.connect(self.get_games)
        button_save = QPushButton('Сохранить', self)
        button_save.clicked.connect(self.save)

        grid_layout.addWidget(self.table, 0, 0)
        inner_grid = QGridLayout(self)
        grid_layout.addLayout(inner_grid, 0, 1)
        inner_grid.addWidget(self.cb, 0, 0)
        inner_grid.addWidget(button_enter, 1, 0)
        inner_grid.addWidget(button_save, 2, 0)

    def selection_change(self):
        if "Дивизион" in [self.cb.itemText(i) for i in range(self.cb.count())]:
            self.cb.removeItem(0)
        key = self.cb.currentText()
        commands = self.data[key]
        commands *= (len(commands))
        tmp = []
        for i, j in zip(commands, sorted(commands)):
            tmp.append([i, j])
        res = sorted(set([tuple(sorted(i)) for i in tmp if i[0] != i[1]]))
        self.table.setRowCount(len(res))
        self.table.setColumnCount(3)
        for i in res:
            self.table.setItem(res.index(i), 2, QTableWidgetItem('-'))
            self.table.setItem(res.index(i), 1, QTableWidgetItem(i[1]))
            self.table.setItem(res.index(i), 0, QTableWidgetItem(i[0]))

    def remove_current_item(self):
        current_index = self.cb.currentIndex()
        if current_index != -1:
            self.cb.removeItem(current_index)

    @pyqtSlot()
    def save(self):
        QMessageBox.warning(self, "Данные сохранены!", "Ожидайте составления результата")
        self.dump3 = sorted(set([tuple(i) for i in self.dump3]))
        for i in self.dump1:
            print(i)
        print('--------------------------------')
        for i in self.dump2:
            print(i)
        print('--------------------------------')
        for i in self.dump3:
            print(i)

    @pyqtSlot()
    def get_games(self):
        if self.cb.currentText() == "Дивизион":
            return
        res = []
        for i in range(0, self.table.rowCount()):
            res.append([])
            for j in range(0, self.table.columnCount()):
                res[i].append(self.table.item(i, j).text())
        self.dump3 += res
        if self.cb.count() <= 1:
            return
        else:
            self.remove_current_item()

    def to_db1(self):
        for row in self.dump1:
            team = models.Team(name = row[0],
                               division = row[1], 
                               format = row[2],  
                               coach = row[3], 
                               date = row[4],  
                               stadium_wish = row[5], 
                               time_wish = row[6], 
                               time_wish2 = row[7])
            database.add(team)
        database.commit()
    
    def to_db2(self):
        for row in self.dump1:
            field = models.Field(format = row[0],
                               date = row[1], 
                               stadium = row[2],  
                               name = row[3], 
                               start_time = row[4],  
                               duration = row[5], 
                               plays_amount = row[6])
            database.add(field)
        database.commit()
        

    def read(self, flag):
        dump = []
        check = False
        for i in range(0, self.table.rowCount()):
            dump.append([])
            for j in range(0, self.table.columnCount()):
                item = self.table.item(i, j)
                if flag == 1 and (j==7 or j==6) and item.text() == '':
                    dump[i].append(None)
                else:
                    dump[i].append(item.text())
            if '' in dump[i]:
                check = True
                break

        if check:
            QMessageBox.warning(self, "ВНИМАНИЕ!", "Заполните таблицу, перед тем как продолжить работу")
        else:
            if flag == 1:
                self.dump1 = dump
                self.data = DataParser.form_divs(self.dump1)
                self.to_db1()
                self.show_scene('Данные по туру', 7, ["Формат", "Дата", "Стадион", "Поле",
                                                      "Время", "Время игры", "Количество игр"], self.enter3)
            elif flag == 2:
                self.dump2 = dump
                self.to_db2()
                self.scene3()

        print(self.dump1)
        print(self.dump2)
        print(self.dump2)
        #self.to_db()

    @pyqtSlot()
    def insert(self):
        self.table.setRowCount(self.table.rowCount() + 1)
        for i in range(self.table.columnCount()):
            self.table.setItem(self.table.rowCount()-1, i, QTableWidgetItem(''))

    @pyqtSlot()
    def enter1(self):
        self.show_scene('Команды', 8, ["Команда", "Дивизион", "Формат", "Тренер",
                                       "Дата", "Стадион", "Время", "Доп. Время"], self.enter2)

    @pyqtSlot()
    def enter2(self):
        self.read(1)

    @pyqtSlot()
    def enter3(self):
        self.read(2)

    def get_data(self):
        return [self.dump1, self.dump2, self.dump3]
        

if __name__ == "__main__":
    app = QApplication(argv)
    mw = MainWindow()
    mw.showMaximized()
    exit(app.exec())
  

