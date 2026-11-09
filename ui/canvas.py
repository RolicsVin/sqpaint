from qtools.brush import Brush
from qtools.eraser import Eraser
from qtools.fill import Fill
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QColor, QImage
from PyQt6.QtWidgets import QWidget


class Canvas(QWidget):
    BRUSH = "brush"
    ERASER = "eraser"
    FILL = "fill"

    MIN_ZOOM = 0.1
    MAX_ZOOM = 4.0

    def __init__(self, parent, layers, w, h):
        super().__init__(parent=parent)
        self.document_width = int(w)
        self.document_height = int(h)
        self.zoom = 1.0
        self.setFixedSize(self.document_width, self.document_height)

        self.layers = layers
        self.active = 0
        self.last = None
        self.color = QColor("black")
        self.width_px = 4

        self.brush = Brush()
        self.eraser = Eraser()
        self.fill = Fill()
        self.active_tool = self.BRUSH

    def set_zoom(self, zoom: float) -> float:
        """Меняет только размер отображения, не затрагивая изображения слоёв."""
        zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, float(zoom)))
        self.zoom = zoom
        self.last = None
        self.setFixedSize(
            max(1, round(self.document_width * zoom)),
            max(1, round(self.document_height * zoom)),
        )
        self.update()
        return self.zoom

    def set_layers(self, layers, active: int | None = None) -> None:
        """Подключает актуальную коллекцию слоёв документа."""
        self.layers = layers
        if active is not None:
            self.set_active_layer(active)
        elif not self.layers:
            self.active = 0
        else:
            self.active = max(0, min(self.active, len(self.layers) - 1))
        self.last = None
        self.update()

    def set_active_layer(self, index: int) -> bool:
        """Выбирает активный слой по индексу."""
        if not 0 <= index < len(self.layers):
            return False
        self.active = index
        self.last = None
        return True

    def set_document_size(self, width: int, height: int) -> None:
        """Синхронизирует размеры отображения с уже изменённым Project."""
        width, height = int(width), int(height)
        if width <= 0 or height <= 0:
            raise ValueError("Размеры холста должны быть положительными.")
        self.document_width = width
        self.document_height = height
        self.last = None
        self.set_zoom(self.zoom)
        self.update()

    def set_tool(self, tool_name: str) -> None:
        if tool_name not in (self.BRUSH, self.ERASER, self.FILL):
            return
        self.active_tool = tool_name
        self.last = None

    def _document_pos(self, event) -> QPoint:
        """Преобразует экранную позицию мыши в координаты документа."""
        position = event.position()
        return QPoint(
            int(position.x() / self.zoom),
            int(position.y() / self.zoom),
        )

    def get_image(self):
        """Возвращает композицию в исходном разрешении документа."""
        image = QImage(
            self.document_width,
            self.document_height,
            QImage.Format.Format_ARGB32,
        )
        image.fill(0)

        painter = QPainter(image)
        for layer in self.layers:
            if layer.visible:
                painter.drawImage(0, 0, layer.image)
        painter.end()
        return image

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.scale(self.zoom, self.zoom)
        for layer in self.layers:
            if layer.visible:
                painter.drawImage(0, 0, layer.image)

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        if not self.layers or not (0 <= self.active < len(self.layers)):
            return

        layer = self.layers[self.active]
        if not layer.visible:
            return

        pos = self._document_pos(e)
        if not (0 <= pos.x() < self.document_width and
                0 <= pos.y() < self.document_height):
            return

        if self.active_tool == self.FILL:
            self.fill.press(
                layer.image, pos, None, self.color, self.width_px
            )
            self.last = None
            self.update()
            return

        self.last = pos

    def mouseMoveEvent(self, e):
        if self.last is None:
            return
        if not self.layers or not (0 <= self.active < len(self.layers)):
            return

        layer = self.layers[self.active]
        if not layer.visible:
            return

        pos = self._document_pos(e)
        if self.active_tool == self.BRUSH:
            self.brush.move(
                layer.image, pos, self.last, self.color, self.width_px
            )
        elif self.active_tool == self.ERASER:
            self.eraser.move(
                layer.image, pos, self.last, self.color, self.width_px
            )

        self.last = pos
        self.update()

    def mouseReleaseEvent(self, e):
        self.last = None

    def re_draw_canvas(self) -> None:
        self.update()
