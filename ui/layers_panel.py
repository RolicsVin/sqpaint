from core.models import Layer
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QCheckBox,
)


class LayerButton(QPushButton):
    def __init__(self, icon, text, parent = ...):
        super().__init__(icon, text, parent)


class LayerPanel(QWidget):
    WIDTH = 200
    COLOR = ''

    def __init__(self, parent, layers: list[Layer]):
        super().__init__(parent=parent)
        self.layers = layers
        self.main_layout = QVBoxLayout(self)

        self.header_layout = QHBoxLayout()
        self.header_layout.setGeometry(QRect(0, 0, self.WIDTH, 50))

        self.add_layer_button = QPushButton()
        self.add_layer_button.setText('+')

        self.remove_layer_button = QPushButton()
        self.remove_layer_button.setText('-')

        self.header_layout.addWidget(self.add_layer_button)
        self.header_layout.addWidget(self.remove_layer_button)

        self.Vlayout = QVBoxLayout()

        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addLayout(self.Vlayout)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Base, QColor("#5cb85c"))  # Зелёный фон
        self.setPalette(palette)

    def update_layers(self):
        """Обновляет панель слоёв."""
        self.clear_layout(self.Vlayout)

        for layer in self.layers:
            self.create_layer_button(layer)

    def delete_layer(self, layer: Layer):
        """Удаляет слой."""
        self.layers.remove(layer)
        self.update_layers()

    def change_visible_layer(self):
        """Изменяет видимость слоя на противопложную."""
        pass

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

            elif item.layout():
                self.clear_layout(item.layout())

    def create_layer_button(self, layer: Layer):
        btn = QWidget()
        btn.setFixedHeight(50)
        layout = QHBoxLayout(btn)

        visible = QCheckBox()
        label = QLabel()
        label.setText(layer.get_name())

        layout.addWidget(visible)
        layout.addWidget(label)

        self.Vlayout.addWidget(btn)

    def set_layers(self, layers: list[Layer]) -> None:
        self.clear_layout(self.Vlayout)
        self.layers = layers
        self.update_layers()