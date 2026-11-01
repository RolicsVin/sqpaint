from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtWidgets import QWidget


class Canvas(QWidget):
    def __init__(self, layers, w, h):
        super().__init__()
        self.setFixedSize(w, h)
        self.layers = layers
        self.active = 0
        self.last = None
        self.color = QColor("black")
        self.width_px = 4

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), Qt.GlobalColor.white)  # подложка
        for layer in self.layers:
            if layer.visible:
                p.drawImage(0, 0, layer.image)

    def mousePressEvent(self, e):
        self.last = e.position().toPoint()

    def mouseMoveEvent(self, e):
        if self.last is None:
            return
        pos = e.position().toPoint()
        p = QPainter(self.layers[self.active].image)  # рисуем в активный слой
        p.setPen(QPen(self.color, self.width_px, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        p.drawLine(self.last, pos)
        p.end()
        self.last = pos
        self.update()

    def mouseReleaseEvent(self, e):
        self.last = None