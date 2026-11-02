from qtools.brush import Brush
from qtools.eraser import Eraser
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QWidget


class Canvas(QWidget):
    BRUSH = "brush"
    ERASER = "eraser" 

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
        self.active_tool = self.BRUSH

    def set_tool(self, tool_name: str) -> None:
        """Меняет активный инструмент и сбрасывает текущий штрих."""
        self.active_tool = tool_name
        print(self.active_tool)
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
        if self.last is None:
            return

        if not self.layers or not (0 <= self.active < len(self.layers)):
            return

        layer = self.layers[self.active]

        if not layer.visible:
            return

        pos = e.position().toPoint()

        if self.active_tool == self.BRUSH:
            self.eraser.move(
                layer.image,
                pos,
                self.last,
                self.color,
                self.width_px,
            )
        if self.active_tool == self.ERASER:
            self.eraser.move(
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
