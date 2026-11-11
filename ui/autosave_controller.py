"""Периодическое создание резервных копий изменённых проектов."""
import sqlite3

from PyQt6.QtCore import QObject, QTimer

from services import autosave


class AutoSaveController(QObject):
    """Оркестратор автосохранения; управление копиями делегирует services.autosave."""

    DEFAULT_INTERVAL_MINUTES = 5

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.timer = QTimer(self)
        saved_interval = window.settings_data.get("autosave", {}).get(
            "interval_minutes", self.DEFAULT_INTERVAL_MINUTES
        )
        try:
            self.interval_minutes = min(120, max(1, int(saved_interval)))
        except (TypeError, ValueError):
            self.interval_minutes = self.DEFAULT_INTERVAL_MINUTES
        self.timer.setInterval(self.interval_minutes * 60 * 1000)
        self.timer.timeout.connect(self.create_backup)

    def set_interval(self, minutes: int) -> None:
        """Обновляет период таймера без вмешательства в логику резервных копий."""
        self.interval_minutes = min(120, max(1, int(minutes)))
        self.timer.setInterval(self.interval_minutes * 60 * 1000)

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
            window.logger.log("Создана резервная копия проекта", project.get_path())
            window.history_controller.mark_saved()
        except (OSError, sqlite3.Error, RuntimeError, ValueError, MemoryError):
            # Ошибка автосохранения не должна прерывать работу редактора.
            return
