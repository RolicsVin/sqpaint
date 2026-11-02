from qtools.brush import Brush
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QWidget


class Canvas(QWidget):
    def __init__(self, parent, layers, w, h):
        super().__init__(parent=parent)
        self.setFixedSize(w, h)
        self.layers = layers
        self.active = 0
        self.last = None
        self.color = QColor("black")
        self.width_px = 4

        self.brush = Brush()
        self.qtools = self.brush
        self.active_tool = "brush"

    def set_tool(self, tool_name: str) -> None:
        """Меняет активный инструмент и сбрасывает текущий штрих."""
        self.active_tool = tool_name
        self.last = None

    def paintEvent(self, event):
        p = QPainter(self)
        for layer in self.layers:
            if layer.visible:
                p.drawImage(0, 0, layer.image)

    def mousePressEvent(self, e):
        if self.active_tool == "brush":
            self.last = e.position().toPoint()

    def mouseMoveEvent(self, e):
        if self.active_tool != "brush" or self.last is None:
            return

        if not self.layers or not (0 <= self.active < len(self.layers)):
            return

        layer = self.layers[self.active]
        if not layer.visible:
            return

        pos = e.position().toPoint()

        # Существующая реализация кисти сохранена.
        self.brush.move(
            layer.image,
            pos,
            self.last,
            self.color,
            self.width_px,
        )

        self.last = pos
        self.update()

    def mouseReleaseEvent(self, e):
        self.last = None

    def re_draw_canvas(self) -> None:
        self.update()
