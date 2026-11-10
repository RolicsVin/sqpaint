from PyQt6.QtCore import Qt, QPointF, QRect, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen


class Crop:
    """Инструмент выделения области кадрирования."""

    def __init__(self):
        self.start = None
        self.rect = None

    @staticmethod
    def _clamp_point(point: QPointF, width: int, height: int) -> QPointF:
        return QPointF(
            max(0.0, min(float(width), point.x())),
            max(0.0, min(float(height), point.y())),
        )

    def press(self, point: QPointF, width: int, height: int) -> None:
        point = self._clamp_point(point, width, height)
        self.start = point
        self.rect = QRectF(point, point)

    def move(self, point: QPointF, width: int, height: int) -> bool:
        if self.start is None:
            return False
        point = self._clamp_point(point, width, height)
        self.rect = QRectF(self.start, point).normalized()
        return True

    def release(self) -> None:
        self.start = None

    def cancel(self) -> None:
        self.start = None
        self.rect = None

    def key_press(self, key: int, width: int, height: int):
        if self.rect is None:
            return None, False

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            rect = self.rect.normalized().toAlignedRect()
            rect = rect.intersected(QRect(0, 0, width, height))
            self.cancel()
            if rect.width() > 0 and rect.height() > 0:
                return rect, True
            return None, True

        if key == Qt.Key.Key_Escape:
            self.cancel()
            return None, True

        return None, False

    def paint(
        self, painter: QPainter, zoom: float, width: int, height: int
    ) -> None:
        if self.rect is None:
            return

        rect = self.rect.normalized()
        shade = QColor(0, 0, 0, 95)
        full = QRectF(0, 0, width, height)

        painter.fillRect(
            QRectF(0, 0, full.width(), max(0, rect.top())), shade
        )
        painter.fillRect(
            QRectF(0, rect.bottom(), full.width(),
                   max(0, full.bottom() - rect.bottom())), shade
        )
        painter.fillRect(
            QRectF(0, rect.top(), max(0, rect.left()), rect.height()), shade
        )
        painter.fillRect(
            QRectF(rect.right(), rect.top(),
                   max(0, full.right() - rect.right()), rect.height()), shade
        )

        painter.setPen(
            QPen(QColor("#ffb74d"), 1.5 / zoom, Qt.PenStyle.DashLine)
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)
