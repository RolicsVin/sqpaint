from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QColorDialog


class ToolBar(QWidget):
    HEIGHT = 50
    color_selected = pyqtSignal(QColor)

    def __init__(self, parent):
        super().__init__(parent=parent)

        self.setFixedHeight(self.HEIGHT)
        self.current_color = QColor("black")

        self.Hlayout = QHBoxLayout(self)

        self.color_btn = QPushButton(self)
        self.color_btn.setText('Цвет')
        self.color_btn.clicked.connect(self.choose_color)

        self.brush_tool = QPushButton(self)
        self.brush_tool.setText('Кисть')

        self.eraser_tool = QPushButton(self)
        self.eraser_tool.setText('Ластик')

        self.fill_tool = QPushButton(self)
        self.fill_tool.setText('Заливка')

        self.Hlayout.addWidget(self.color_btn)
        self.Hlayout.addWidget(self.brush_tool)
        self.Hlayout.addWidget(self.eraser_tool)
        self.Hlayout.addWidget(self.fill_tool)

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
