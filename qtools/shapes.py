"""Рисование геометрических фигур на изображении."""
from math import cos, pi, sin

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF


class Shapes:
    """Содержит типы фигур и методы их отрисовки."""

    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    STAR = "star"

    @classmethod
    def draw(
        cls,
        painter: QPainter,
        rect: QRectF,
        shape: str,
        color: QColor,
        width: int,
    ) -> None:
        """Рисует выбранную фигуру в заданной области холста."""
        rect = rect.normalized()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(
            QPen(
                color,
                max(1, int(width)),
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if shape == cls.RECTANGLE:
            painter.drawRect(rect)
        elif shape == cls.CIRCLE:
            # Свободное соотношение сторон позволяет рисовать эллипсы.
            painter.drawEllipse(rect)
        elif shape == cls.STAR:
            cls._draw_star(painter, rect)

        painter.restore()

    @staticmethod
    def _draw_star(painter: QPainter, rect: QRectF) -> None:
        """Строит и рисует пятиконечную звезду внутри заданной области."""
        center = rect.center()
        outer_radius = min(rect.width(), rect.height()) / 2
        inner_radius = outer_radius * 0.42
        points = []

        for index in range(10):
            radius = outer_radius if index % 2 == 0 else inner_radius
            angle = -pi / 2 + index * pi / 5
            points.append(
                QPointF(
                    center.x() + cos(angle) * radius,
                    center.y() + sin(angle) * radius,
                )
            )

        painter.drawPolygon(QPolygonF(points))
