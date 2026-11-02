from core.models import Layer
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QCheckBox,
)


class LayerNameEdit(QLineEdit):
    focused = pyqtSignal()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused.emit()


class LayerPanel(QWidget):
    WIDTH = 200
    COLOR = "#161616"
    LAYER_COLOR = "#1f1f1f"
    LAYER_COLOR2 = "#292929"

    add_layer_requested = pyqtSignal()
    remove_layer_requested = pyqtSignal(object)
    layer_selected = pyqtSignal(int)
    layer_visible_change = pyqtSignal(Layer, bool)
    layer_change = pyqtSignal()

    def __init__(self, parent, layers: list[Layer]):
        super().__init__(parent=parent)
        self.layers = layers
        self.selected_layer: Layer | None = None

        self.setObjectName("layerPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(6)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.header_layout = QHBoxLayout()

        self.add_layer_button = QPushButton("+")
        self.add_layer_button.setToolTip("Добавить слой")
        self.remove_layer_button = QPushButton("-")
        self.remove_layer_button.setToolTip("Удалить выбранный слой")

        self.add_layer_button.clicked.connect(self.add_layer_requested.emit)
        self.remove_layer_button.clicked.connect(self._request_remove_layer)

        self.header_layout.addWidget(self.add_layer_button)
        self.header_layout.addWidget(self.remove_layer_button)

        self.Vlayout = QVBoxLayout()
        self.Vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addLayout(self.Vlayout)

        self.setStyleSheet(f"""
            QWidget#layerPanel {{
                background-color: {self.COLOR};
            }}
            QWidget#layerRow {{
                background-color: {self.LAYER_COLOR};
                border: 1px solid #454c56;
                border-radius: 5px;
            }}
            QWidget#layerRow QLineEdit {{
                background-color: #252a31;
                color: #e5e7eb;
                border: 1px solid #aebdca;
                border-radius: 3px;
                padding: 3px;
            }}
            QWidget#layerRow QLineEdit:focus {{
                border: 1px solid #7898bd;
                background-color: #20252b;
            }}
            QWidget#layerPanel QPushButton {{
                background-color: #3a414b;
                color: #f1f3f5;
                border: 1px solid #505966;
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QWidget#layerPanel QPushButton:hover {{
                background-color: #485362;
            }}
            QWidget#layerPanel QPushButton:pressed {{
                background-color: #29313b;
            }}
            QWidget#layerPanel QCheckBox {{
                color: #e5e7eb;
            }}
        """)

    def change_visible_layer(self, layer: Layer, box: QCheckBox) -> None:
        visible = box
        self.layers[self.layers.index(layer)].set_visible(visible)
        self.layer_visible_change.emit(layer, visible)
        self.layer_change.emit()

    def _request_remove_layer(self):
        if self.selected_layer is not None:
            self.remove_layer_requested.emit(self.selected_layer)

    def update_layers(self):
        """Перестраивает список слоёв."""
        self.clear_layout(self.Vlayout)

        if self.selected_layer not in self.layers:
            self.selected_layer = self.layers[0] if self.layers else None

        for index, layer in enumerate(self.layers):
            self.create_layer_row(layer, index)

    def create_layer_row(self, layer: Layer, index: int):
        row = QWidget()
        row.setObjectName("layerRow")
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row.setFixedHeight(36)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(2, 2, 2, 2)

        box_visible = QCheckBox()
        box_visible.setChecked(layer.is_visible())
        box_visible.setToolTip("Видимость слоя")
        box_visible.toggled.connect(layer.set_visible)
        box_visible.clicked.connect(lambda box=box_visible, item=layer: self.change_visible_layer(item, box))

        name_edit = LayerNameEdit(layer.get_name())
        name_edit.setPlaceholderText("Название слоя")
        name_edit.focused.connect(lambda i=index: self._select_layer(i))
        name_edit.editingFinished.connect(
            lambda item=layer, edit=name_edit: self._commit_layer_name(item, edit)
        )

        layout.addWidget(box_visible)
        layout.addWidget(name_edit, 1)
        self.Vlayout.addWidget(row)

    def _select_layer(self, index: int):
        if 0 <= index < len(self.layers):
            self.selected_layer = self.layers[index]
            self.layer_selected.emit(index)

    def _commit_layer_name(self, layer: Layer, editor: LayerNameEdit):
        new_name = editor.text().strip()
        if not new_name:
            editor.setText(layer.get_name())
            return

        duplicate = any(
            other is not layer and other.get_name() == new_name
            for other in self.layers
        )
        if duplicate:
            editor.setText(layer.get_name())
            return

        layer.set_name(new_name)
        editor.setText(new_name)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def set_layers(self, layers: list[Layer]) -> None:
        self.layers = layers
        if self.selected_layer not in layers:
            self.selected_layer = layers[0] if layers else None
        self.update_layers()
