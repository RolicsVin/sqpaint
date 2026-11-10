from math import cos, pi, sin

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF


class Shapes:
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    STAR = "star"

    @classmethod
    def draw(cls, painter: QPainter, rect: QRectF, shape: str,
             color: QColor, width: int) -> None:
        rect = rect.normalized()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(color, max(1, int(width)), Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if shape == cls.RECTANGLE:
            painter.drawRect(rect)
        elif shape == cls.CIRCLE:
            # Свободное соотношение сторон: фигура может быть кругом или эллипсом.
            painter.drawEllipse(rect)
        elif shape == cls.STAR:
            cls._draw_star(painter, rect)
        painter.restore()

    @staticmethod
    def _draw_star(painter: QPainter, rect: QRectF) -> None:
        center = rect.center()
        outer = min(rect.width(), rect.height()) / 2
        inner = outer * 0.42
        points = []
        for i in range(10):
            radius = outer if i % 2 == 0 else inner
            angle = -pi / 2 + i * pi / 5
            points.append(QPointF(center.x() + cos(angle) * radius,
                                  center.y() + sin(angle) * radius))
        painter.drawPolygon(QPolygonF(points))
