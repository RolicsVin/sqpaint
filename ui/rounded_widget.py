"""Переиспользуемый виджет с цветным фоном, скруглением и сигналами мыши."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget


class RoundedWidget(QWidget):
    """Виджет с настраиваемым цветом фона и скруглением углов.

    Сигналы:
        clicked: испускается после обычного нажатия левой кнопкой мыши.
        double_clicked: испускается при двойном нажатии левой кнопкой мыши.
    """

    clicked = pyqtSignal()
    double_clicked = pyqtSignal()

    def __init__(
        self,
        parent: QWidget | None = None,
        color: QColor | str = QColor("#2b2b2b"),
        radius: int = 8,
    ):
        """Создаёт виджет с заданными цветом фона и радиусом скругления."""
        super().__init__(parent)
        self._color = QColor(color)
        self._radius = max(0, radius)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_color(self, color: QColor | str) -> None:
        """Устанавливает новый цвет фона, если он корректен."""
        new_color = QColor(color)
        if not new_color.isValid():
            return

        self._color = new_color
        self.update()

    def get_color(self) -> QColor:
        """Возвращает копию текущего цвета фона."""
        return QColor(self._color)

    def set_radius(self, radius: int) -> None:
        """Устанавливает радиус скругления углов в пикселях."""
        self._radius = max(0, radius)
        self.update()

    def get_radius(self) -> int:
        """Возвращает текущий радиус скругления углов."""
        return self._radius

    def paintEvent(self, event) -> None:
        """Отрисовывает фон виджета с заданным цветом и скруглением."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        painter.drawRoundedRect(self.rect(), self._radius, self._radius)

    def mouseReleaseEvent(self, event) -> None:
        """Испускает clicked при отпускании левой кнопки внутри виджета."""
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.rect().contains(event.position().toPoint())
        ):
            self.clicked.emit()

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        """Испускает double_clicked при двойном нажатии левой кнопкой мыши."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()

        super().mouseDoubleClickEvent(event)
