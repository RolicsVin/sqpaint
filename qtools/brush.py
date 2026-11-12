"""Инструмент рисования кистью."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen

from qtools.base import Tool


class Brush(Tool):
    """Рисует непрерывную линию между последовательными позициями курсора."""

    def move(self, image, pos, last_pos, color, size) -> None:
        """Продолжает штрих кисти от предыдущей позиции курсора к текущей."""
        painter = QPainter(image)
        painter.setPen(
            QPen(
                color,
                size,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.drawLine(last_pos, pos)
        painter.end()
