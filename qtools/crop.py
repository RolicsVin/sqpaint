"""Инструмент интерактивного выделения области кадрирования."""
from PyQt6.QtCore import QPointF, QRect, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen


class Crop:
    """Хранит выделенную область и отображает её поверх холста."""

    def __init__(self):
        """Инициализирует пустое выделение."""
        self.start = None
        self.rect = None

    @staticmethod
    def _clamp_point(point: QPointF, width: int, height: int) -> QPointF:
        """Ограничивает координаты точки размерами документа."""
        return QPointF(
            max(0.0, min(float(width), point.x())),
            max(0.0, min(float(height), point.y())),
        )

    def press(self, point: QPointF, width: int, height: int) -> None:
        """Начинает выделение области с позиции нажатия мыши."""
        point = self._clamp_point(point, width, height)
        self.start = point
        self.rect = QRectF(point, point)

    def move(self, point: QPointF, width: int, height: int) -> bool:
        """Обновляет выделение при перемещении мыши."""
        if self.start is None:
            return False

        point = self._clamp_point(point, width, height)
        self.rect = QRectF(self.start, point).normalized()
        return True

    def release(self) -> None:
        """Завершает изменение выделения, сохраняя его область."""
        self.start = None

    def cancel(self) -> None:
        """Сбрасывает текущее выделение."""
        self.start = None
        self.rect = None

    def key_press(self, key: int, width: int, height: int):
        """Обрабатывает Enter для подтверждения и Escape для отмены выделения.
        """
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
        self,
        painter: QPainter,
        zoom: float,
        width: int,
        height: int,
    ) -> None:
        """Рисует затемнение за пределами выделенной области и её границу."""
        if self.rect is None:
            return

        rect = self.rect.normalized()
        shade = QColor(0, 0, 0, 95)
        full = QRectF(0, 0, width, height)

        painter.fillRect(
            QRectF(0, 0, full.width(), max(0, rect.top())),
            shade,
        )
        painter.fillRect(
            QRectF(
                0,
                rect.bottom(),
                full.width(),
                max(0, full.bottom() - rect.bottom()),
            ),
            shade,
        )
        painter.fillRect(
            QRectF(0, rect.top(), max(0, rect.left()), rect.height()),
            shade,
        )
        painter.fillRect(
            QRectF(
                rect.right(),
                rect.top(),
                max(0, full.right() - rect.right()),
                rect.height(),
            ),
            shade,
        )

        painter.setPen(
            QPen(QColor("#ffb74d"), 1.5 / zoom, Qt.PenStyle.DashLine)
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)
