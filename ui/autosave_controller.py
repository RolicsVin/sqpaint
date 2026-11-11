"""Периодическое создание резервных копий изменённых проектов."""
import sqlite3

from PyQt6.QtCore import QObject, QTimer

from services import autosave


class AutoSaveController(QObject):
    """Оркестратор автосохранения; управление копиями делегирует services.autosave."""

    INTERVAL_MS = 5 * 60 * 1000

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.timer = QTimer(self)
        self.timer.setInterval(self.INTERVAL_MS)
        self.timer.timeout.connect(self.create_backup)

    def start(self) -> None:
        if not self.timer.isActive():
            self.timer.start()

    def stop(self) -> None:
        self.timer.stop()

    def create_backup(self) -> None:
        window = self.window
        project = window.project
        if project is None or window.database.conn is None:
            return

        # Не создаём одинаковые копии, если документ не менялся.
        window.history_controller.flush_pending()
        if not window.history_controller.is_dirty():
            return

        try:
            # Сначала фиксируем актуальное состояние документа в основном SQLite,
            # затем копируем уже согласованный файл.
            window.database.save(
                project, window.history_controller.export_for_save()
            )
            autosave.create_backup(project.get_path())
            window.history_controller.mark_saved()
        except (OSError, sqlite3.Error, RuntimeError, ValueError, MemoryError):
            # Ошибка автосохранения не должна прерывать работу редактора.
            return
