from qtools.brush import Brush
from qtools.eraser import Eraser
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

        if self.active_tool == self.FILL:
            self.fill_at(e.position().toPoint())
            return

        if self.active_tool in (self.BRUSH, self.ERASER):
            self.last = e.position().toPoint()

    def fill_at(self, position) -> None:
        """Заливает связную область активного слоя выбранным цветом."""
        if not self.layers or not (0 <= self.active < len(self.layers)):
            return

        layer = self.layers[self.active]
        if not layer.visible:
            return

        image = layer.image
        start_x, start_y = position.x(), position.y()

        if not (0 <= start_x < image.width() and 0 <= start_y < image.height()):
            return

        target_color = image.pixel(start_x, start_y)
        replacement_color = self.color.rgba()

        # Если цвет уже совпадает, заливка ничего не изменит.
        if target_color == replacement_color:
            return

        # Scanline flood fill: обрабатываем горизонтальные отрезки,
        # добавляя в стек только начала новых отрезков сверху и снизу.
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack.pop()

            if image.pixel(x, y) != target_color:
                continue

            left = x
            while left > 0 and image.pixel(left - 1, y) == target_color:
                left -= 1

            right = x
            while (
                right + 1 < image.width()
                and image.pixel(right + 1, y) == target_color
            ):
                right += 1

            scan_above = False
            scan_below = False

            for current_x in range(left, right + 1):
                image.setPixel(current_x, y, replacement_color)

                if y > 0:
                    matches_above = (
                        image.pixel(current_x, y - 1) == target_color
                    )
                    if matches_above and not scan_above:
                        stack.append((current_x, y - 1))
                    scan_above = matches_above

                if y + 1 < image.height():
                    matches_below = (
                        image.pixel(current_x, y + 1) == target_color
                    )
                    if matches_below and not scan_below:
                        stack.append((current_x, y + 1))
                    scan_below = matches_below

        self.update()

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

        self.last = pos
        self.update()

    def mouseReleaseEvent(self, e):
        self.last = None

    def re_draw_canvas(self) -> None:
        self.update()
