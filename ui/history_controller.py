"""UI-адаптер постоянной истории: сигналы холста, команды меню и синхронизация."""
import sqlite3

from PyQt6.QtWidgets import QMessageBox

from core.history import HistoryManager


class HistoryController:
    """Связывает HistoryManager с виджетами, не помещая историю в DomainWindow."""

    def __init__(self, window):
        self.window = window
        self.history = HistoryManager(window.database)
        self._pending = None
        window.undo_action.triggered.connect(self.undo)
        window.redo_action.triggered.connect(self.redo)
        self._refresh_actions()

    def set_project(self, project) -> None:
        self.history.set_project(project)
        self._pending = None
        canvas = self.window.canvas
        canvas.history_started.connect(self._begin_canvas_action)
        canvas.history_finished.connect(self._finish_canvas_action)
        self._refresh_actions()

    def begin(self):
        if self.history.project is None:
            return None
        return self.history.capture()

    def commit(self, before, label: str) -> bool:
        if before is None:
            return False
        try:
            changed = self.history.commit(before, label)
        except (OSError, sqlite3.Error, RuntimeError, ValueError) as error:
            self._show_error("История действий", "Action history", error)
            return False
        self._refresh_actions()
        return changed

    def _begin_canvas_action(self, label: str) -> None:
        if self._pending is None:
            self._pending = (label, self.begin())

    def _finish_canvas_action(self, label: str) -> None:
        if self._pending is None:
            return
        pending_label, before = self._pending
        self._pending = None
        self.commit(before, pending_label or label)

    def _refresh_actions(self) -> None:
        try:
            can_undo, can_redo = self.history.status() if self.history.project else (False, False)
        except (sqlite3.Error, RuntimeError):
            can_undo, can_redo = False, False
        self.window.undo_action.setEnabled(can_undo)
        self.window.redo_action.setEnabled(can_redo)

    def _refresh_document(self) -> None:
        w = self.window
        project, canvas = w.project, w.canvas
        if project is None or canvas is None:
            self._refresh_actions()
            return
        active = min(canvas.active, max(0, len(project.layers) - 1))
        canvas.set_layers(project.get_layers(), active=active)
        canvas.set_document_size(project.get_width(), project.get_height())
        w.layer_panel.set_layers(project.get_layers())
        if project.layers:
            w.layer_panel.select_layer(active)
        w.canvas_view.viewport().update()
        w.canvas_view.zoom_changed.emit(round(w.canvas_view.zoom * 100))
        w.setWindowTitle(f"SQPaint — {project.get_name()}")
        self._refresh_actions()

    def undo(self) -> None:
        if self.history.project is None:
            return
        if self._pending is not None:
            self._finish_canvas_action("")
        try:
            if self.history.undo():
                self._refresh_document()
        except (OSError, sqlite3.Error, RuntimeError, ValueError) as error:
            self._show_error("Отмена действия", "Undo action", error)

    def redo(self) -> None:
        if self.history.project is None:
            return
        if self._pending is not None:
            self._finish_canvas_action("")
        try:
            if self.history.redo():
                self._refresh_document()
        except (OSError, sqlite3.Error, RuntimeError, ValueError) as error:
            self._show_error("Повтор действия", "Redo action", error)

    def _show_error(self, ru: str, en: str, error) -> None:
        w = self.window
        QMessageBox.warning(w, w._tr(ru, en), str(error))
