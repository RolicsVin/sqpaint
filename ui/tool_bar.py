from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QColorDialog, QSlider
from core.localization import LocalizedLabel, LocalizedButton, LocalizedComboBox
from ui.zoom_control import ZoomControl


class ToolBar(QWidget):
    HEIGHT = 50
    color_selected = pyqtSignal(QColor)
    tool_selected = pyqtSignal(str)
    shape_selected = pyqtSignal(str)
    width_changed = pyqtSignal(int)
    zoom_changed = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setFixedHeight(self.HEIGHT)
        self.current_color = QColor("black")
        self._language = "ru"
        self.Hlayout = QHBoxLayout(self)

        self.color_btn = LocalizedButton(parent=self)
        self.color_btn.setFixedSize(44, 28)
        self.color_btn.setToolTip("Выбрать цвет")
        self.update_color_button()
        self.color_btn.clicked.connect(self.choose_color)

        self.tools_combo = LocalizedComboBox(self)
        self.tools_combo.add_localized_item({"ru": "🖌 Кисть", "en": "🖌 Brush"}, "brush")
        self.tools_combo.add_localized_item({"ru": "🧽 Ластик", "en": "🧽 Eraser"}, "eraser")
        self.tools_combo.add_localized_item({"ru": "🪣 Заливка", "en": "🪣 Fill"}, "fill")
        self.tools_combo.add_localized_item({"ru": "▱ Фигуры", "en": "▱ Shapes"}, "shapes")
        self.tools_combo.add_localized_item({"ru": "✂️ Кадрирование", "en": "✂️ Crop"}, "crop")
        self.tools_combo.currentIndexChanged.connect(self.on_tool_changed)

        self.shapes_combo = LocalizedComboBox(self)
        self.shapes_combo.add_localized_item({"ru": "Прямоугольник", "en": "Rectangle"}, "rectangle")
        self.shapes_combo.add_localized_item({"ru": "Круг", "en": "Circle"}, "circle")
        self.shapes_combo.add_localized_item({"ru": "Звезда", "en": "Star"}, "star")
        self.shapes_combo.setFixedWidth(125)
        self.shapes_combo.hide()
        self.shapes_combo.currentIndexChanged.connect(self.on_shape_changed)

        self.size_label = LocalizedLabel("Размер:")
        self.size_label.add_localization("en", "Size:")
        self.size_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.size_slider.setRange(1, 100)
        self.size_slider.setValue(4)
        self.size_slider.setFixedWidth(125)
        self.size_slider.setToolTip("Толщина кисти и ластика")
        self.size_value_label = LocalizedLabel("4 px")
        self.size_slider.valueChanged.connect(self.on_size_changed)

        self.zoom_label = LocalizedLabel("Масштаб:")
        self.zoom_label.add_localization("en", "Zoom:")
        self.zoom_control = ZoomControl(self)
        self.zoom_control.zoom_changed.connect(self.zoom_changed)

        self.Hlayout.addWidget(self.color_btn)
        self.Hlayout.addWidget(self.tools_combo)
        self.Hlayout.addWidget(self.shapes_combo)
        self.Hlayout.addWidget(self.size_label)
        self.Hlayout.addWidget(self.size_slider)
        self.Hlayout.addWidget(self.size_value_label)
        self.Hlayout.addStretch()
        self.Hlayout.addWidget(self.zoom_label)
        self.Hlayout.addWidget(self.zoom_control)

    def set_language(self, language: str) -> None:
        self._language = language
        self.tools_combo.set_language(language)
        self.shapes_combo.set_language(language)
        self.shapes_combo.setToolTip("Форма фигуры" if language == "ru" else "Shape type")
        self.size_label.set_language(language)
        self.zoom_label.set_language(language)
        self.color_btn.setToolTip("Выбрать цвет" if language == "ru" else "Choose color")
        self.size_slider.setToolTip(
            "Толщина кисти и ластика" if language == "ru"
            else "Brush and eraser thickness"
        )

    def on_tool_changed(self, index: int) -> None:
        tool = self.tools_combo.itemData(index)
        self.shapes_combo.setVisible(tool == "shapes")
        self.tool_selected.emit(tool)

    def on_shape_changed(self, index: int) -> None:
        shape = self.shapes_combo.itemData(index)
        if shape:
            self.shape_selected.emit(shape)

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
        title = "Выбор цвета" if self._language == "ru" else "Choose color"
        color = QColorDialog.getColor(self.current_color, self, title)
        if color.isValid():
            self.current_color = color
            self.update_color_button()
            self.color_selected.emit(color)

    def get_height(self) -> int:
        return self.HEIGHT
