'''
============================================

                 SQPaint
     Автор: Овечин Ратмир Михайлович

  Растровый редактор, основанный на sqlite

============================================

Это главный модуль, запускающий программу.

'''
import sys
from core.database import *
from ui.main_window import *
from ui.canvas import *
from PyQt6.QtWidgets import QApplication

database = ProjectDatabase()
# project = database.create('D:/Python/sqpaint/test_base.sqlite', 'my_project', 700, 700)
project = database.load('D:/Python/sqpaint/test_base.sqlite')
#project.add_layer(Layer('Слой 1', 0, True, QImage("C:/Users/Пользователь/Pictures/ENDFIELD/ENDFIELD_SHARE_1771734146.png")))
#database.save(project)

app = QApplication([])
window = DomainWindow(project)
sys.exit(app.exec())