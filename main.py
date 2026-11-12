"""Точка входа в приложение SQPaint.

Модуль инициализирует Qt-приложение, базу данных и главное окно.
"""
import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from core.database import ProjectDatabase
from services import settings
from ui.main_window import DomainWindow


def resource_path(relative_path: str) -> str:
    """Возвращает абсолютный путь к ресурсу с учётом сборки PyInstaller."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_path / relative_path)


def main() -> int:
    """Создаёт приложение, запускает главный цикл и закрывает базу данных."""
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("icon.ico")))

    database = ProjectDatabase()
    window = DomainWindow(None, database, settings.load_data())

    try:
        return app.exec()
    finally:
        database.close()


if __name__ == "__main__":
    sys.exit(main())
