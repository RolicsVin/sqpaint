'''
============================================

                 SQPaint
     Автор: Овечкин Ратмир Михайлович

  Растровый редактор, основанный на sqlite

============================================

Это главный модуль, запускающий программу.
'''
import sys

from core.database import ProjectDatabase
from services import settings
from ui.main_window import DomainWindow

from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication


def resource_path(relative_path: str) -> str:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_path / relative_path)


app = QApplication(sys.argv)
app.setWindowIcon(QIcon(resource_path("icon.ico")))

database = ProjectDatabase()
window = DomainWindow(None, database, settings.load_data())

exit_code = app.exec()
database.close()
sys.exit(exit_code)