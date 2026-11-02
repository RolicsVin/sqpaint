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
    COLOR = "#e3e3e3"

    add_layer_requested = pyqtSignal()
    remove_layer_requested = pyqtSignal(object)
    layer_selected = pyqtSignal(int)

    def __init__(self, parent, layers: list[Layer]):
        super().__init__(parent=parent)
        self.layers = layers
        self.selected_layer: Layer | None = None

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

        self.setStyleSheet(f"LayerPanel {{ background-color: {self.COLOR}; }}")

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
        row.setFixedHeight(36)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(2, 2, 2, 2)

        visible = QCheckBox()
        visible.setChecked(layer.is_visible())
        visible.setToolTip("Видимость слоя")
        visible.toggled.connect(layer.set_visible)

        name_edit = LayerNameEdit(layer.get_name())
        name_edit.setPlaceholderText("Название слоя")
        name_edit.focused.connect(lambda i=index: self._select_layer(i))
        name_edit.editingFinished.connect(
            lambda item=layer, edit=name_edit: self._commit_layer_name(item, edit)
        )

        layout.addWidget(visible)
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
