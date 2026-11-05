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
        super().__init__(parent)

        self._color = QColor(color)
        self._radius = max(0, radius)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_color(self, color: QColor | str) -> None:
        """Устанавливает цвет фона."""
        new_color = QColor(color)
        if not new_color.isValid():
            return

        self._color = new_color
        self.update()

    def get_color(self) -> QColor:
        """Возвращает текущий цвет фона."""
        return QColor(self._color)

    def set_radius(self, radius: int) -> None:
        """Устанавливает радиус скругления углов в пикселях."""
        self._radius = max(0, radius)
        self.update()

    def get_radius(self) -> int:
        return self._radius

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        painter.drawRoundedRect(self.rect(), self._radius, self._radius)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()

        super().mouseDoubleClickEvent(event)
