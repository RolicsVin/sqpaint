from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QLabel, QHBoxLayout, QColorDialog,
    QComboBox, QSlider,
)
from ui.zoom_control import ZoomControl


class ToolBar(QWidget):
    HEIGHT = 50
    color_selected = pyqtSignal(QColor)
    tool_selected = pyqtSignal(str)
    width_changed = pyqtSignal(int)
    zoom_changed = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setFixedHeight(self.HEIGHT)
        self.current_color = QColor("black")
        self.Hlayout = QHBoxLayout(self)

        self.color_btn = QPushButton(self)
        self.color_btn.setFixedSize(44, 28)
        self.color_btn.setToolTip("Выбрать цвет")
        self.update_color_button()
        self.color_btn.clicked.connect(self.choose_color)

        self.tools_combo = QComboBox(self)
        self.tools_combo.addItem("🖌", "brush")
        self.tools_combo.addItem("🧽", "eraser")
        self.tools_combo.addItem("🪣", "fill")
        for index, name in enumerate(("Кисть", "Ластик", "Заливка")):
            self.tools_combo.setItemData(index, name, Qt.ItemDataRole.ToolTipRole)
        self.tools_combo.currentIndexChanged.connect(self.on_tool_changed)

        self.size_label = QLabel("Размер:")
        self.size_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.size_slider.setRange(1, 100)
        self.size_slider.setValue(4)
        self.size_slider.setFixedWidth(125)
        self.size_slider.setToolTip("Толщина кисти и ластика")
        self.size_value_label = QLabel("4 px")
        self.size_slider.valueChanged.connect(self.on_size_changed)

        self.zoom_control = ZoomControl(self)
        self.zoom_control.zoom_changed.connect(self.zoom_changed)

        self.Hlayout.addWidget(self.color_btn)
        self.Hlayout.addWidget(self.tools_combo)
        self.Hlayout.addWidget(self.size_label)
        self.Hlayout.addWidget(self.size_slider)
        self.Hlayout.addWidget(self.size_value_label)
        self.Hlayout.addStretch()
        self.Hlayout.addWidget(QLabel("Масштаб:"))
        self.Hlayout.addWidget(self.zoom_control)

    def on_tool_changed(self, index: int) -> None:
        self.tool_selected.emit(self.tools_combo.itemData(index))

    def on_size_changed(self, value: int) -> None:
        self.size_value_label.setText(f"{value} px")
        self.width_changed.emit(value)

    def set_zoom(self, value: int) -> None:
        self.zoom_control.set_zoom(value)

    def update_color_button(self) -> None:
        self.color_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {self.current_color.name()};
                border: 1px solid #666666;
                border-radius: 3px;
            }}
            QPushButton:hover {{ border: 1px solid #222222; }}
            """
        )

    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self, "Выбор цвета")
        if color.isValid():
            self.current_color = color
            self.update_color_button()
            self.color_selected.emit(color)

    def get_height(self) -> int:
        return self.HEIGHT
