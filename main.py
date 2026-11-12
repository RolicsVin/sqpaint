"""Точка входа в приложение SQPaint.

Модуль инициализирует Qt-приложение, базу данных и главное окно.
"""
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from core.database import ProjectDatabase
from core.path_tool import ensure_app_dirs, get_resource_path
from services import settings
from ui.main_window import DomainWindow


def main() -> int:
    """Создаёт приложение, запускает главный цикл и закрывает базу данных."""
    ensure_app_dirs()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(get_resource_path("icon.ico"))))

    database = ProjectDatabase()
    window = DomainWindow(None, database, settings.load_data())

    try:
        return app.exec()
    finally:
        database.close()


if __name__ == "__main__":
    sys.exit(main())
