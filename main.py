'''
============================================

                 SQPaint
     Автор: Овечкин Ратмир Михайлович

  Растровый редактор, основанный на sqlite

============================================

Это главный модуль, запускающий программу.
'''
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from core.database import ProjectDatabase
from ui.main_window import DomainWindow


app = QApplication(sys.argv)
app.setStyle("Fusion")

database = ProjectDatabase()
window = DomainWindow(None, database)
window.show()

exit_code = app.exec()
database.close()
sys.exit(exit_code)