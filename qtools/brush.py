from qtools.base import Tool
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen


class Brush(Tool):
    """Кисть для рисования"""
    def press(self, image, pos, last_pos, color, size):
        p = QPainter(image)

        p.setPen(QPen(color, size, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        
        p.drawLine(last_pos, pos)
        p.end()