from qtools.base import Tool
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen


class Eraser(Tool):
    """Ластик"""
    def move(self, image, pos, last_pos, color, size):
        print('Ластик')
        p = QPainter(image)

        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)

        p.setPen(QPen(QColor(0, 0, 0, 0), size, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        
        p.drawLine(last_pos, pos)
        p.end()