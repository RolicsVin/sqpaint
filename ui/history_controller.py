"""UI-контроллер истории действий документа."""
from PyQt6.QtWidgets import QMessageBox

from core.history import HistoryManager


class HistoryController:
    """Связывает HistoryManager с холстом, меню и состоянием главного окна."""

    def __init__(self, window):
        """Создаёт менеджер истории и подключает команды отмены и повтора."""
        self.window = window
        self.history = HistoryManager(window.database)
        self._pending = None
        window.undo_action.triggered.connect(self.undo)
        window.redo_action.triggered.connect(self.redo)
        self._refresh_actions()

    def set_project(self, project) -> None:
        """Загружает историю проекта и подключает сигналы его холста."""
        self.history.set_project(project, self.window.database.load_history())
        self._pending = None
        canvas = self.window.canvas
        canvas.history_started.connect(self._begin_canvas_action)
        canvas.history_finished.connect(self._finish_canvas_action)
        self._refresh_actions()
        self._refresh_title()

    def set_limit(self, limit: int) -> None:
        """Обновляет лимит истории в менеджере и модели проекта."""
        self.history.set_limit(limit)
        if self.window.project is not None:
            self.window.project.max_undo_steps = self.history.limit
        self._refresh_actions()
        self._refresh_title()

    def begin(self):
        """Создаёт снимок текущего документа перед изменением."""
        if self.history.project is None:
            return None
        return self.history.capture()

    def export_for_save(self) -> dict:
        """Подготавливает историю для записи при явном сохранении проекта."""
        return self.history.export_for_save()

    def mark_saved(self) -> None:
        """Отмечает текущее состояние истории как сохранённое."""
        self.history.mark_saved()
        self._refresh_title()

    def is_dirty(self) -> bool:
        """Возвращает признак наличия несохранённых изменений."""
        return self.history.is_dirty()

    def _refresh_title(self) -> None:
        """Обновляет заголовок окна с учётом состояния документа."""
        project = self.window.project
        if project is None:
            self.window.setWindowTitle("SQPaint")
            return

        suffix = " *" if self.is_dirty() else ""
        self.window.setWindowTitle(f"SQPaint — {project.get_name()}{suffix}")

    def commit(self, before, label: str) -> bool:
        """Фиксирует действие в истории и обновляет связанные элементы интерфейса."""
        if before is None:
            return False

        try:
            changed = self.history.commit(before, label)
        except (RuntimeError, ValueError, MemoryError) as error:
            self._refresh_document()
            self._show_error("История действий", "Action history", error)
            return False

        self._refresh_actions()
        self._refresh_title()
        return changed

    def _begin_canvas_action(self, label: str) -> None:
        """Сохраняет снимок до начала рисования или другого действия на холсте."""
        if self._pending is None:
            self._pending = (label, self.begin())

    def _finish_canvas_action(self, label: str) -> None:
        """Фиксирует завершённое действие холста и записывает его в журнал."""
        if self._pending is None:
            return

        pending_label, before = self._pending
        self._pending = None
        action_label = pending_label or label

        if self.commit(before, action_label):
            descriptions = {
                "PaintStroke": "Закрашена область кистью",
                "EraseStroke": "Выполнено стирание",
                "FillArea": "Выполнена заливка",
                "DrawShape": "Нарисована фигура",
                "TransformImage": "Изображение размещено на холсте",
            }
            canvas = self.window.canvas
            layer_name = (
                canvas.layers[canvas.active].get_name()
                if canvas is not None and 0 <= canvas.active < len(canvas.layers)
                else "неизвестный слой"
            )
            self.window.logger.log(
                descriptions.get(action_label, "Изменение изображения"),
                f"Слой: {layer_name}; действие: {action_label}",
            )

    def flush_pending(self) -> None:
        """Завершает отложенное действие перед сохранением или закрытием."""
        if self._pending is not None:
            self._finish_canvas_action("")

    def _refresh_actions(self) -> None:
        """Обновляет доступность команд отмены и повтора."""
        try:
            can_undo, can_redo = (
                self.history.status() if self.history.project else (False, False)
            )
        except (RuntimeError, ValueError):
            can_undo, can_redo = False, False

        self.window.undo_action.setEnabled(can_undo)
        self.window.redo_action.setEnabled(can_redo)

    def _refresh_document(self) -> None:
        """Синхронизирует холст, панель слоёв и заголовок с моделью проекта."""
        window = self.window
        project, canvas = window.project, window.canvas

        if project is None or canvas is None:
            self._refresh_actions()
            return

        active = min(canvas.active, max(0, len(project.layers) - 1))
        canvas.set_layers(project.get_layers(), active=active)
        canvas.set_document_size(project.get_width(), project.get_height())
        canvas.supports_transparency = project.supports_transparency
        window.layer_panel.set_layers(project.get_layers())

        if project.layers:
            window.layer_panel.select_layer(active)

        window.canvas_view.viewport().update()
        window.canvas_view.zoom_changed.emit(round(window.canvas_view.zoom * 100))
        self._refresh_title()
        self._refresh_actions()

    def undo(self) -> None:
        """Отменяет последнее действие и обновляет отображение документа."""
        if self.history.project is None:
            return

        if (
            self.window.canvas is not None
            and self.window.canvas.transform_image is not None
        ):
            self.window.canvas.commit_image_transform()

        if self._pending is not None:
            self._finish_canvas_action("")

        try:
            if self.history.undo():
                self._refresh_document()
                self.window.logger.log("Отмена действия")
        except (RuntimeError, ValueError, MemoryError) as error:
            self._show_error("Отмена действия", "Undo action", error)

    def redo(self) -> None:
        """Повторяет отменённое действие и обновляет отображение документа."""
        if self.history.project is None:
            return

        if (
            self.window.canvas is not None
            and self.window.canvas.transform_image is not None
        ):
            self.window.canvas.commit_image_transform()

        if self._pending is not None:
            self._finish_canvas_action("")

        try:
            if self.history.redo():
                self._refresh_document()
                self.window.logger.log("Повтор действия")
        except (RuntimeError, ValueError, MemoryError) as error:
            self._show_error("Повтор действия", "Redo action", error)

    def _show_error(self, ru: str, en: str, error) -> None:
        """Показывает сообщение об ошибке на текущем языке интерфейса."""
        window = self.window
        QMessageBox.warning(window, window._tr(ru, en), str(error))
