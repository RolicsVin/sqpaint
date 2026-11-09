from qtools.base import Tool
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QImage


class Fill(Tool):
    """Кисть для рисования"""
    def press(self, image: QImage, pos, last_pos, color, size):
        print('Заливка')
        p = QPainter(image)

        p.setPen(QPen(color, size, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        
        p.drawRect(0, 0, image.width(), image.height())

        p.end()