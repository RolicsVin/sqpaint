from qtools.base import Tool
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen


class Brush(Tool):
    """Кисть для рисования"""
    def draw(self, image, pos, last_pos, color, size):
        p = QPainter(image)

        p.setPen(QPen(color, size, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        
        p.drawLine(QPoint(last_pos, pos))
        p.end()