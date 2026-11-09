from qtools.brush import Brush
from qtools.eraser import Eraser
from qtools.fill import Fill
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QWidget


class Canvas(QWidget):
    BRUSH = "brush"
    ERASER = "eraser"
    FILL = "fill"

    def __init__(self, parent, layers, w, h):
        super().__init__(parent=parent)
        self.setFixedSize(w, h)
        self.layers = layers
        self.active = 0
        self.last = None
        self.color = QColor("black")
        self.width_px = 4

        self.brush = Brush()
        self.eraser = Eraser()
        self.fill = Fill()
        self.active_tool = self.BRUSH

    def set_tool(self, tool_name: str) -> None:
        """Меняет активный инструмент и сбрасывает текущий штрих."""
        if tool_name not in (self.BRUSH, self.ERASER, self.FILL):
            return

        self.active_tool = tool_name
        self.last = None

    def paintEvent(self, event):
        painter = QPainter(self)
        for layer in self.layers:
            if layer.visible:
                painter.drawImage(0, 0, layer.image)

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return

        self.last = e.position().toPoint()

    def mouseMoveEvent(self, e):
        if self.last is None:
            return

        if not self.layers or not (0 <= self.active < len(self.layers)):
            return

        layer = self.layers[self.active]

        if not layer.visible:
            return

        pos = e.position().toPoint()

        if self.active_tool == self.BRUSH:
            self.brush.move(
                layer.image,
                pos,
                self.last,
                self.color,
                self.width_px,
            )
        elif self.active_tool == self.ERASER:
            self.eraser.move(
                layer.image,
                pos,
                self.last,
                self.color,
                self.width_px,
            )
        elif self.active_tool == self.FILL:
            self.fill.press(
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
