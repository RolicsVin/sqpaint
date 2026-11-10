from qtools.brush import Brush
from qtools.eraser import Eraser
from qtools.fill import Fill
from qtools.crop import Crop
from qtools.shapes import Shapes
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QImage, QPen
from PyQt6.QtWidgets import QWidget


class Canvas(QWidget):
    crop_requested = pyqtSignal(QRect)
    history_started = pyqtSignal(str)
    history_finished = pyqtSignal(str)
    BRUSH = "brush"
    ERASER = "eraser"
    FILL = "fill"
    SHAPES = "shapes"
    CROP = "crop"

    MIN_ZOOM = 0.1
    MAX_ZOOM = 4.0

    def __init__(self, parent, layers, w, h, supports_transparency: bool = True):
        super().__init__(parent=parent)
        self.document_width = int(w)
        self.document_height = int(h)
        self.supports_transparency = bool(supports_transparency)
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
        self.shape_type = Shapes.RECTANGLE
        self.shape_start = None
        self.shape_current = None
        self.active_tool = self.BRUSH
        self.transform_image = None
        self.transform_rect = None
        self.transform_drag = None
        self.transform_start = None
        self._transform_mouse_start = None
        self.crop = Crop()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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
        if tool_name not in (self.BRUSH, self.ERASER, self.FILL, self.SHAPES, self.CROP):
            return
        if self.last is not None and self.active_tool in (self.BRUSH, self.ERASER):
            label = "PaintStroke" if self.active_tool == self.BRUSH else "EraseStroke"
            self.history_finished.emit(label)
        self.shape_start = self.shape_current = None
        self.active_tool = tool_name
        self.last = None
        if tool_name != self.CROP:
            self.crop.cancel()
        self.setCursor(Qt.CursorShape.CrossCursor if tool_name in (self.CROP, self.SHAPES)
                       else Qt.CursorShape.ArrowCursor)
        self.update()

    def set_shape(self, shape_name: str) -> None:
        if shape_name in (Shapes.RECTANGLE, Shapes.ELLIPSE, Shapes.STAR):
            self.shape_type = shape_name
            self.update()

    def _document_pos(self, event) -> QPoint:
        """Преобразует экранную позицию мыши в координаты документа."""
        position = event.position()
        return QPoint(
            int(position.x() / self.zoom),
            int(position.y() / self.zoom),
        )

    def begin_image_transform(self, image: QImage) -> None:
        """Включает режим позиционирования и масштабирования изображения."""
        if image.isNull():
            return
        self.transform_image = image.convertToFormat(QImage.Format.Format_ARGB32)
        scale = min(
            1.0,
            self.document_width / image.width(),
            self.document_height / image.height(),
        )
        width = image.width() * scale
        height = image.height() * scale
        self.transform_rect = QRectF(
            (self.document_width - width) / 2,
            (self.document_height - height) / 2, width, height,
        )
        self.transform_drag = None
        self.setFocus()
        self.update()

    def commit_image_transform(self) -> None:
        """Записывает текущее положение изображения в активный слой."""
        if self.transform_image is None or self.transform_rect is None:
            return
        self.history_started.emit("TransformImage")
        if 0 <= self.active < len(self.layers):
            result = QImage(self.document_width, self.document_height,
                            QImage.Format.Format_ARGB32)
            result.fill(0)
            painter = QPainter(result)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
            painter.drawImage(self.transform_rect, self.transform_image)
            painter.end()
            self.layers[self.active].image = result
        self.transform_image = None
        self.transform_rect = None
        self.transform_drag = None
        self.update()
        self.history_finished.emit("TransformImage")

    def _transform_handle(self, point: QPointF):
        if self.transform_rect is None:
            return None
        rect = self.transform_rect
        points = {
            "tl": rect.topLeft(), "tm": QPointF(rect.center().x(), rect.top()),
            "tr": rect.topRight(), "mr": QPointF(rect.right(), rect.center().y()),
            "br": rect.bottomRight(), "bm": QPointF(rect.center().x(), rect.bottom()),
            "bl": rect.bottomLeft(), "ml": QPointF(rect.left(), rect.center().y()),
        }
        radius = 8 / self.zoom
        for name, handle in points.items():
            if abs(point.x() - handle.x()) <= radius and abs(point.y() - handle.y()) <= radius:
                return name
        return None

    def _resize_transform(self, point: QPointF) -> None:
        rect = QRectF(self.transform_start)
        handle = self.transform_drag
        if "l" in handle:
            rect.setLeft(point.x())
        if "r" in handle:
            rect.setRight(point.x())
        if "t" in handle:
            rect.setTop(point.y())
        if "b" in handle:
            rect.setBottom(point.y())
        self.transform_rect = rect.normalized()

    def keyPressEvent(self, event) -> None:
        if self.transform_image is not None:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.commit_image_transform()
                event.accept()
                return
        if self.active_tool == self.CROP:
            rect, handled = self.crop.key_press(
                event.key(), self.document_width, self.document_height
            )
            if handled:
                if rect is not None:
                    self.crop_requested.emit(rect)
                self.update()
                event.accept()
                return
        super().keyPressEvent(event)

    def get_image(self):
        """Возвращает композицию в исходном разрешении документа."""
        image = QImage(
            self.document_width,
            self.document_height,
            QImage.Format.Format_ARGB32,
        )
        image.fill(0 if self.supports_transparency else QColor("white"))

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

        # Если прозрачность отключена, документ всегда компонуется на белом фоне.
        # Прозрачные пиксели слоёв не должны показывать содержимое окна под холстом.
        if not self.supports_transparency:
            painter.fillRect(
                QRectF(0, 0, self.document_width, self.document_height),
                QColor("white"),
            )

        for index, layer in enumerate(self.layers):
            if layer.visible and not (self.transform_image is not None and index == self.active):
                painter.drawImage(0, 0, layer.image)

        if self.active_tool == self.SHAPES and self.shape_start is not None:
            Shapes.draw(painter, QRectF(self.shape_start, self.shape_current),
                        self.shape_type, self.color, self.width_px)

        if self.active_tool == self.CROP:
            self.crop.paint(
                painter, self.zoom, self.document_width, self.document_height
            )

        if self.transform_image is not None and self.transform_rect is not None:
            painter.drawImage(self.transform_rect, self.transform_image)
            painter.setPen(QPen(QColor("#36a3ff"), 1.5 / self.zoom, Qt.PenStyle.DashLine))
            painter.drawRect(self.transform_rect)
            painter.setPen(QPen(QColor("#202020"), 1 / self.zoom))
            painter.setBrush(QColor("white"))
            radius = 4 / self.zoom
            rect = self.transform_rect
            handles = (
                rect.topLeft(), QPointF(rect.center().x(), rect.top()), rect.topRight(),
                QPointF(rect.right(), rect.center().y()), rect.bottomRight(),
                QPointF(rect.center().x(), rect.bottom()), rect.bottomLeft(),
                QPointF(rect.left(), rect.center().y()),
            )
            for point in handles:
                painter.drawRect(QRectF(point.x()-radius, point.y()-radius, radius*2, radius*2))

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        if self.transform_image is not None and self.transform_rect is not None:
            point = QPointF(e.position().x() / self.zoom, e.position().y() / self.zoom)
            handle = self._transform_handle(point)
            if handle:
                self.transform_drag = handle
                self.transform_start = QRectF(self.transform_rect)
            elif self.transform_rect.contains(point):
                self.transform_drag = "move"
                self.transform_start = QRectF(self.transform_rect)
            else:
                self.commit_image_transform()
                return
            self._transform_mouse_start = point
            e.accept()
            return
        if self.active_tool == self.CROP:
            point = QPointF(e.position().x() / self.zoom, e.position().y() / self.zoom)
            self.crop.press(point, self.document_width, self.document_height)
            self.setFocus()
            self.update()
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
            self.history_started.emit("FillArea")
            self.fill.press(
                layer.image, pos, None, self.color, self.width_px
            )
            self.history_finished.emit("FillArea")
            self.last = None
            self.update()
            return

        if self.active_tool == self.SHAPES:
            self.shape_start = QPointF(e.position().x() / self.zoom,
                                       e.position().y() / self.zoom)
            self.shape_current = QPointF(self.shape_start)
            self.history_started.emit("DrawShape")
            self.setFocus()
            self.update()
            return

        if self.active_tool in (self.BRUSH, self.ERASER):
            self.history_started.emit("PaintStroke" if self.active_tool == self.BRUSH else "EraseStroke")
        self.last = pos

    def mouseMoveEvent(self, e):
        if self.transform_image is not None and self.transform_drag is not None:
            point = QPointF(e.position().x() / self.zoom, e.position().y() / self.zoom)
            if self.transform_drag == "move":
                self.transform_rect = self.transform_start.translated(point - self._transform_mouse_start)
            else:
                self._resize_transform(point)
            self.update()
            return
        if self.transform_image is not None and self.transform_rect is not None:
            point = QPointF(e.position().x() / self.zoom, e.position().y() / self.zoom)
            self.setCursor(Qt.CursorShape.SizeAllCursor if self.transform_rect.contains(point)
                           else Qt.CursorShape.ArrowCursor)
            return
        if self.active_tool == self.CROP:
            point = QPointF(e.position().x() / self.zoom, e.position().y() / self.zoom)
            if self.crop.move(point, self.document_width, self.document_height):
                self.update()
            return
        if self.active_tool == self.SHAPES and self.shape_start is not None:
            self.shape_current = QPointF(e.position().x() / self.zoom,
                                         e.position().y() / self.zoom)
            self.update()
            return
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
        if e.button() == Qt.MouseButton.LeftButton and self.shape_start is not None:
            if self.layers and 0 <= self.active < len(self.layers):
                layer = self.layers[self.active]
                if layer.visible and self.shape_current is not None:
                    painter = QPainter(layer.image)
                    Shapes.draw(painter, QRectF(self.shape_start, self.shape_current),
                                self.shape_type, self.color, self.width_px)
                    painter.end()
            self.shape_start = self.shape_current = None
            self.history_finished.emit("DrawShape")
            self.update()
            return
        if self.last is not None and self.active_tool in (self.BRUSH, self.ERASER):
            self.history_finished.emit("PaintStroke" if self.active_tool == self.BRUSH else "EraseStroke")
        self.last = None
        if self.active_tool == self.CROP:
            self.crop.release()
        if self.transform_drag is not None:
            self.transform_drag = None
            self.transform_start = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def re_draw_canvas(self) -> None:
        self.update()
