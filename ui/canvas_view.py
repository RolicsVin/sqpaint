from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QScrollArea


class CanvasView(QScrollArea):
    """Область просмотра: прокрутка и масштабирование Canvas."""

    zoom_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
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

        # mapTo() уже учитывает текущую прокрутку, поэтому добавлять
        # значение scrollbar к координате документа нельзя.
        old_origin = self.canvas.mapTo(viewport, self.canvas.rect().topLeft())
        document_x = (anchor.x() - old_origin.x()) / self._zoom
        document_y = (anchor.y() - old_origin.y()) / self._zoom

        self._zoom = new_zoom
        self.canvas.set_zoom(new_zoom)

        new_origin = self.canvas.mapTo(viewport, self.canvas.rect().topLeft())
        target_origin_x = anchor.x() - document_x * new_zoom
        target_origin_y = anchor.y() - document_y * new_zoom

        # Сдвигаем полосы прокрутки так, чтобы прежняя точка документа
        # осталась под курсором (если диапазон прокрутки это позволяет).
        hbar = self.horizontalScrollBar()
        vbar = self.verticalScrollBar()
        hbar.setValue(round(hbar.value() + new_origin.x() - target_origin_x))
        vbar.setValue(round(vbar.value() + new_origin.y() - target_origin_y))
        self.zoom_changed.emit(percent)

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y()
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if delta:
                factor = 1.15 ** (delta / 120.0)
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
