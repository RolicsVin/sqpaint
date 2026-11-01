from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout


class ToolBar(QWidget):
    HEIGHT = 100

    def __init__(self):
        super().__init__()

        self.setFixedHeight(self.HEIGHT)

        self.Hlayout = QHBoxLayout(self)

        self.color_btn = QPushButton(self)
        self.color_btn.setText('Цвет')

        self.Hlayout.addWidget(self.color_btn)

    def get_height(self) -> int:
        return self.HEIGHT