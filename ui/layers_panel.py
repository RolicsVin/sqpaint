from core.models import Layer
from ui.rounded_widget import RoundedWidget

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QLineEdit,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QCheckBox,
)


class LayerPanel(QWidget):
    WIDTH = 200

    COLOR = "#161616"
    LAYER_COLOR = QColor("#1f1f1f")
    SELECTED_LAYER_COLOR = QColor("#394b63")

    add_layer_requested = pyqtSignal()
    remove_layer_requested = pyqtSignal(object)
    layer_selected = pyqtSignal(int)
    layer_visible_change = pyqtSignal(Layer, bool)
    layer_change = pyqtSignal()

    def __init__(self, parent, layers: list[Layer]):
        super().__init__(parent=parent)
        self.layers = layers
        self.selected_layer: Layer | None = None
        self.layer_rows: dict[Layer, RoundedWidget] = {}

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

        self.layers_layout = QVBoxLayout()
        self.layers_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layers_layout.setSpacing(5)

        self.main_layout.addLayout(self.header_layout)
        self.main_layout.addLayout(self.layers_layout)

        self.setStyleSheet(f"""
            QWidget#layerPanel {{
                background-color: {self.COLOR};
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
            QWidget#layerPanel QLabel {{
                color: #e5e7eb;
                background: transparent;
            }}
            QWidget#layerPanel QLineEdit {{
                background-color: #252a31;
                color: #e5e7eb;
                border: 1px solid #aebdca;
                border-radius: 3px;
                padding: 3px;
            }}
            QWidget#layerPanel QLineEdit:focus {{
                border: 1px solid #7898bd;
                background-color: #20252b;
            }}
        """)

    def change_visible_layer(self, layer: Layer, visible: bool) -> None:
        """Изменяет видимость слоя и уведомляет холст."""
        layer.set_visible(visible)
        self.layer_visible_change.emit(layer, visible)
        self.layer_change.emit()

    def _request_remove_layer(self) -> None:
        if self.selected_layer is not None:
            self.remove_layer_requested.emit(self.selected_layer)

    def update_layers(self) -> None:
        """Перестраивает список виджетов слоёв."""
        self.clear_layout(self.layers_layout)
        self.layer_rows.clear()

        if self.selected_layer not in self.layers:
            self.selected_layer = self.layers[0] if self.layers else None

        for index, layer in enumerate(self.layers):
            self.create_layer_row(layer, index)

        self._update_selection_colors()

    def create_layer_row(self, layer: Layer, index: int) -> None:
        row = RoundedWidget(
            self,
            color=self.LAYER_COLOR,
            radius=6,
        )
        row.setObjectName("layerRow")
        row.setFixedHeight(38)
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.clicked.connect(lambda i=index: self._select_layer(i))
        row.double_clicked.connect(lambda item=layer: self._begin_rename(item))

        layout = QHBoxLayout(row)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(6)

        box_visible = QCheckBox()
        box_visible.setChecked(layer.is_visible())
        box_visible.setToolTip("Видимость слоя")
        box_visible.toggled.connect(
            lambda visible, item=layer: self.change_visible_layer(item, visible)
        )

        name_label = QLabel(layer.get_name())
        name_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )

        name_edit = QLineEdit(layer.get_name())
        name_edit.setPlaceholderText("Название слоя")
        name_edit.hide()
        name_edit.editingFinished.connect(
            lambda item=layer, editor=name_edit, label=name_label:
                self._commit_layer_name(item, editor, label)
        )

        layout.addWidget(box_visible)
        layout.addWidget(name_label, 1)
        layout.addWidget(name_edit, 1)

        row.name_label = name_label
        row.name_edit = name_edit
        row.layer = layer

        self.layer_rows[layer] = row
        self.layers_layout.addWidget(row)

    def _select_layer(self, index: int) -> None:
        if not 0 <= index < len(self.layers):
            return

        self.selected_layer = self.layers[index]
        self._update_selection_colors()
        self.layer_selected.emit(index)

    def _update_selection_colors(self) -> None:
        """Подсвечивает выбранный слой и сбрасывает цвет остальных."""
        for layer, row in self.layer_rows.items():
            color = (
                self.SELECTED_LAYER_COLOR
                if layer is self.selected_layer
                else self.LAYER_COLOR
            )
            row.set_color(color)

    def _begin_rename(self, layer: Layer) -> None:
        row = self.layer_rows.get(layer)
        if row is None:
            return

        self._select_layer(self.layers.index(layer))
        row.name_edit.setText(layer.get_name())
        row.name_label.hide()
        row.name_edit.show()
        row.name_edit.setFocus()
        row.name_edit.selectAll()

    def _commit_layer_name(
        self,
        layer: Layer,
        editor: QLineEdit,
        label: QLabel,
    ) -> None:
        new_name = editor.text().strip()

        if not new_name:
            new_name = layer.get_name()
        else:
            duplicate = any(
                other is not layer and other.get_name() == new_name
                for other in self.layers
            )
            if duplicate:
                new_name = layer.get_name()

        layer.set_name(new_name)
        label.setText(new_name)
        editor.setText(new_name)
        editor.hide()
        label.show()

    def clear_layout(self, layout) -> None:
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
