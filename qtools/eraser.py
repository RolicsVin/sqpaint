"""Инструмент удаления пикселей с активного слоя."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen

from qtools.base import Tool


class Eraser(Tool):
    """Стирает пиксели, заменяя их прозрачностью."""

    def move(self, image, pos, last_pos, color, size) -> None:
        """Стирает линию между предыдущей и текущей позициями курсора."""
        painter = QPainter(image)
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_Clear
        )
        painter.setPen(
            QPen(
                QColor(0, 0, 0, 0),
                size,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.drawLine(last_pos, pos)
        painter.end()
