from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QColorDialog,
    QComboBox,
)


class ToolBar(QWidget):
    HEIGHT = 50
    color_selected = pyqtSignal(QColor)
    tool_selected = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent=parent)

        self.setFixedHeight(self.HEIGHT)
        self.current_color = QColor("black")
        self.Hlayout = QHBoxLayout(self)

        self.color_btn = QPushButton("Цвет", self)
        self.color_btn.clicked.connect(self.choose_color)

        # Выпадающий список инструментов.
        self.tools_combo = QComboBox(self)
        self.tools_combo.addItem("Кисть", "brush")
        self.tools_combo.addItem("Ластик", "eraser")
        self.tools_combo.addItem("Заливка", "fill")
        self.tools_combo.setCurrentIndex(0)
        self.tools_combo.currentIndexChanged.connect(self.on_tool_changed)

        # Пока реализована только кисть.
        self.tools_combo.setItemData(
            1, "Инструмент пока не реализован", role=3
        )
        self.tools_combo.setItemData(
            2, "Инструмент пока не реализован", role=3
        )

        self.Hlayout.addWidget(self.color_btn)
        self.Hlayout.addWidget(self.tools_combo)

        screen = QApplication.primaryScreen()
        if screen is not None:
            self.airlabel = QLabel()
            self.airlabel.setFixedWidth(int(screen.size().width() * 0.8))
            self.Hlayout.addWidget(self.airlabel)

    def on_tool_changed(self, index: int) -> None:
        tool_name = self.tools_combo.itemData(index)
        if tool_name == "brush":
            self.tool_selected.emit(tool_name)
        else:
            # Не переключаем Canvas на ещё не реализованный инструмент.
            self.tools_combo.blockSignals(True)
            self.tools_combo.setCurrentIndex(0)
            self.tools_combo.blockSignals(False)

    def choose_color(self):
        color = QColorDialog.getColor(
            self.current_color,
            self,
            "Выбор цвета",
        )

        if color.isValid():
            self.current_color = color
            self.color_selected.emit(color)

    def get_height(self) -> int:
        return self.HEIGHT
