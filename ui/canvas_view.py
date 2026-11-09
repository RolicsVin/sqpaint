from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QScrollArea


class CanvasView(QScrollArea):
    """Область просмотра: прокрутка и масштабирование Canvas."""

    zoom_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.canvas = None
        self._zoom = 1.0

    @property
    def zoom(self) -> float:
        return self._zoom

    def set_canvas(self, canvas) -> None:
        old_canvas = self.takeWidget()
        if old_canvas is not None:
            old_canvas.hide()
            old_canvas.deleteLater()

        self.canvas = canvas
        self._zoom = 1.0
        if canvas is not None:
            canvas.set_zoom(self._zoom)
            self.setWidget(canvas)
            canvas.show()

    def set_zoom(self, percent: int, anchor=None) -> None:
        if self.canvas is None:
            return

        percent = max(10, min(400, int(percent)))
        new_zoom = percent / 100.0
        if abs(new_zoom - self._zoom) < 0.0001:
            self.zoom_changed.emit(percent)
            return

        viewport = self.viewport()
        if anchor is None:
            anchor = viewport.rect().center()

        # Запоминаем координату документа под точкой масштабирования.
        old_origin = self.canvas.mapTo(viewport, self.canvas.rect().topLeft())
        document_x = (
            self.horizontalScrollBar().value() + anchor.x() - old_origin.x()
        ) / self._zoom
        document_y = (
            self.verticalScrollBar().value() + anchor.y() - old_origin.y()
        ) / self._zoom

        self._zoom = new_zoom
        self.canvas.set_zoom(new_zoom)

        # После изменения размера QScrollArea обновляет диапазоны прокрутки.
        new_origin = self.canvas.mapTo(viewport, self.canvas.rect().topLeft())
        self.horizontalScrollBar().setValue(round(
            document_x * new_zoom - anchor.x() + new_origin.x()
        ))
        self.verticalScrollBar().setValue(round(
            document_y * new_zoom - anchor.y() + new_origin.y()
        ))
        self.zoom_changed.emit(percent)

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y()
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if delta:
                steps = delta / 120.0
                factor = 1.15 ** steps
                percent = round(self._zoom * factor * 100)
                anchor = self.viewport().mapFrom(
                    self, event.position().toPoint()
                )
                self.set_zoom(percent, anchor)
            event.accept()
            return

        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta
            )
            event.accept()
            return

        super().wheelEvent(event)
