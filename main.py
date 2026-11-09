'''
============================================

                 SQPaint
     Автор: Овечкин Ратмир Михайлович

  Растровый редактор, основанный на sqlite

============================================

Это главный модуль, запускающий программу.
'''
import sys

from PyQt6.QtWidgets import QApplication

from core.database import ProjectDatabase
from ui.main_window import DomainWindow

from services import settings


app = QApplication(sys.argv)

database = ProjectDatabase()
window = DomainWindow(None, database, settings.load_data())

exit_code = app.exec()
database.close()
sys.exit(exit_code)