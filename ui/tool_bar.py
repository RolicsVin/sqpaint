from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QColorDialog,
    QToolButton,
    QMenu,
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

        # Один выпадающий список вместо трёх отдельных кнопок.
        self.tools_btn = QToolButton(self)
        self.tools_btn.setText("Кисть")
        self.tools_btn.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )

        self.tools_menu = QMenu(self.tools_btn)
        self.tools_group = QActionGroup(self)
        self.tools_group.setExclusive(True)

        self.brush_action = QAction("Кисть", self)
        self.brush_action.setCheckable(True)
        self.brush_action.setChecked(True)
        self.brush_action.triggered.connect(
            lambda checked=False: self.select_tool("brush", "Кисть")
        )

        self.eraser_action = QAction("Ластик", self)
        self.eraser_action.setEnabled(False)
        self.eraser_action.setToolTip("Инструмент пока не реализован")

        self.fill_action = QAction("Заливка", self)
        self.fill_action.setEnabled(False)
        self.fill_action.setToolTip("Инструмент пока не реализован")

        for action in (
            self.brush_action,
            self.eraser_action,
            self.fill_action,
        ):
            self.tools_group.addAction(action)
            self.tools_menu.addAction(action)

        self.tools_btn.setMenu(self.tools_menu)

        self.Hlayout.addWidget(self.color_btn)
        self.Hlayout.addWidget(self.tools_btn)

        screen = QApplication.primaryScreen()
        if screen is not None:
            self.airlabel = QLabel()
            self.airlabel.setFixedWidth(
                int(screen.size().width() * 0.8)
            )
            self.Hlayout.addWidget(self.airlabel)

    def select_tool(self, tool_name: str, display_name: str) -> None:
        self.tools_btn.setText(display_name)
        self.tool_selected.emit(tool_name)

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
