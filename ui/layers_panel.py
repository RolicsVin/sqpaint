"""Панель управления слоями документа."""
from PyQt6.QtCore import QMimeData, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QDrag
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.models import Layer
from ui.rounded_widget import RoundedWidget


class LayerNameEdit(QLineEdit):
    """QLineEdit, который отдельно сообщает о потере фокуса."""

    focus_lost = pyqtSignal()

    def focusOutEvent(self, event) -> None:
        """Передаёт событие потери фокуса после стандартной обработки Qt."""
        super().focusOutEvent(event)
        self.focus_lost.emit()


class LayerRow(RoundedWidget):
    """Строка слоя с поддержкой перетаскивания."""

    def __init__(self, panel, layer, parent=None):
        """Создаёт строку слоя и сохраняет ссылки на панель и модель слоя."""
        super().__init__(parent, color=panel.LAYER_COLOR, radius=6)
        self.panel = panel
        self.layer = layer
        self._drag_start = None
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mousePressEvent(self, event) -> None:
        """Запоминает позицию нажатия для определения начала перетаскивания."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Начинает drag-and-drop, если курсор сместился дальше системного
        порога.
        """
        if self._drag_start is None or not (
            event.buttons() & Qt.MouseButton.LeftButton
        ):
            return

        distance = (
            event.position().toPoint() - self._drag_start
        ).manhattanLength()
        if distance < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(str(id(self.layer)))
        drag.setMimeData(mime)

        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        drag.exec(Qt.DropAction.MoveAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_start = None

    def dragEnterEvent(self, event) -> None:
        """Принимает перетаскивание строк, содержащих идентификатор слоя."""
        if event.mimeData().hasText():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        """Подтверждает допустимое перемещение слоя над строкой."""
        if event.mimeData().hasText():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """Передаёт панели запрос на перемещение слоя относительно текущей
        строки.
        """
        try:
            source_id = int(event.mimeData().text())
        except ValueError:
            event.ignore()
            return

        source = next(
            (layer for layer in self.panel.layers if id(layer) == source_id),
            None,
        )
        if source is None:
            event.ignore()
            return

        insert_before = event.position().y() < self.height() / 2
        self.panel.layer_move_requested.emit(
            source,
            self.layer,
            insert_before,
        )
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()


class LayerPanel(QWidget):
    """Отображает слои и отправляет запросы на изменение их состояния."""

    WIDTH = 200

    COLOR = "#161616"
    LAYER_COLOR = QColor("#1f1f1f")
    SELECTED_LAYER_COLOR = QColor("#394b63")

    add_layer_requested = pyqtSignal()
    remove_layer_requested = pyqtSignal(object)
    layer_selected = pyqtSignal(int)
    layer_visibility_requested = pyqtSignal(object, bool)
    layer_rename_requested = pyqtSignal(object, str)
    layer_move_requested = pyqtSignal(object, object, bool)

    def __init__(self, parent, layers: list[Layer]):
        """Создаёт панель, кнопки управления и контейнер строк слоёв."""
        super().__init__(parent=parent)
        self.layers = layers
        self.selected_layer: Layer | None = None
        self.layer_rows: dict[int, RoundedWidget] = {}

        self.setObjectName("layerPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(6)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.add_layer_button = QPushButton("➕")
        self.add_layer_button.setToolTip("Добавить слой")
        self.add_layer_button.clicked.connect(self.add_layer_requested.emit)

        self.layers_layout = QVBoxLayout()
        self.layers_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layers_layout.setSpacing(5)

        self.main_layout.addLayout(self.layers_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self.add_layer_button)

        self.apply_theme("dark")

    def apply_theme(self, theme: str) -> None:
        """Применяет палитру панели слоёв для выбранной темы."""
        dark = theme != "light"
        self.COLOR = "#161616" if dark else "#eeeeee"
        self.LAYER_COLOR = QColor("#1f1f1f" if dark else "#ffffff")
        self.SELECTED_LAYER_COLOR = QColor("#394b63" if dark else "#c9def5")
        text = "#e5e7eb" if dark else "#202020"
        edit_bg = "#252a31" if dark else "#ffffff"
        button_bg = "#3a414b" if dark else "#e0e0e0"
        button_hover = "#485362" if dark else "#d0d0d0"
        button_pressed = "#29313b" if dark else "#c0c0c0"
        border = "#505966" if dark else "#b8b8b8"

        self.setStyleSheet(
            f"""
            QWidget#layerPanel {{ background-color: {self.COLOR}; }}
            QWidget#layerPanel QPushButton {{
                background-color: {button_bg}; color: {text};
                border: 1px solid {border}; border-radius: 4px;
                padding: 4px 8px;
            }}
            QWidget#layerPanel QPushButton:hover {{
                background-color: {button_hover};
            }}
            QWidget#layerPanel QPushButton:pressed {{
                background-color: {button_pressed};
            }}
            QWidget#layerPanel QCheckBox,
            QWidget#layerPanel QLabel {{ color: {text}; }}
            QWidget#layerPanel QLabel {{ background: transparent; }}
            QWidget#layerPanel QLineEdit {{
                background-color: {edit_bg}; color: {text};
                border: 1px solid {border}; border-radius: 3px; padding: 3px;
            }}
            QWidget#layerPanel QLineEdit:focus {{ border: 1px solid #7898bd; }}
            """
        )
        self._update_selection_colors()

    def change_visible_layer(self, layer: Layer, visible: bool) -> None:
        """Передаёт запрос на изменение видимости владельцу документа."""
        self.layer_visibility_requested.emit(layer, visible)

    def update_layers(self) -> None:
        """Перестраивает список виджетов в соответствии с текущей коллекцией
        слоёв.
        """
        self.clear_layout(self.layers_layout)
        self.layer_rows.clear()

        if self.selected_layer not in self.layers:
            self.selected_layer = self.layers[0] if self.layers else None

        for index, layer in enumerate(self.layers):
            self.create_layer_row(layer, index)

        self._update_selection_colors()

    def create_layer_row(self, layer: Layer, index: int) -> None:
        """Создаёт строку слоя с переключателем видимости и кнопкой удаления.
        """
        row = LayerRow(self, layer, self)
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
            lambda visible, item=layer: self.change_visible_layer(
                item, visible
            )
        )

        name_label = QLabel(layer.get_name())
        name_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )

        name_edit = LayerNameEdit(layer.get_name())
        name_edit.setPlaceholderText("Название слоя")
        name_edit.hide()

        def commit_name(item=layer, editor=name_edit, label=name_label):
            self._commit_layer_name(item, editor, label)

        name_edit.focus_lost.connect(commit_name)
        name_edit.returnPressed.connect(commit_name)

        remove_button = QPushButton("🗑")
        remove_button.setFixedSize(26, 26)
        remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_button.setToolTip("Удалить слой")
        remove_button.clicked.connect(
            lambda checked=False, item=layer: (
                self.remove_layer_requested.emit(item)
            )
        )

        layout.addWidget(box_visible)
        layout.addWidget(name_label, 1)
        layout.addWidget(name_edit, 1)
        layout.addWidget(remove_button)

        row.name_label = name_label
        row.name_edit = name_edit
        row.layer = layer

        self.layer_rows[id(layer)] = row
        self.layers_layout.addWidget(row)

    def select_layer(self, index: int) -> None:
        """Публичный интерфейс выбора слоя по индексу."""
        self._select_layer(index)

    def _select_layer(self, index: int) -> None:
        """Выбирает слой, обновляет подсветку и отправляет сигнал выбора."""
        if not 0 <= index < len(self.layers):
            return

        self.selected_layer = self.layers[index]
        self._update_selection_colors()
        self.layer_selected.emit(index)

    def _update_selection_colors(self) -> None:
        """Подсвечивает выбранный слой и сбрасывает цвет остальных строк."""
        for layer in self.layers:
            row = self.layer_rows.get(id(layer))
            if row is None:
                continue

            color = (
                self.SELECTED_LAYER_COLOR
                if layer is self.selected_layer
                else self.LAYER_COLOR
            )
            row.set_color(color)

    def _begin_rename(self, layer: Layer) -> None:
        """Переключает подпись слоя в режим редактирования."""
        row = self.layer_rows.get(id(layer))
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
        """Отправляет новое название владельцу модели и возвращает обычную
        подпись.
        """
        new_name = editor.text().strip() or layer.get_name()
        self.layer_rename_requested.emit(layer, new_name)
        editor.hide()
        label.show()

    def refresh_layer_name(self, layer: Layer) -> None:
        """Обновляет текстовые элементы строки после переименования слоя."""
        row = self.layer_rows.get(id(layer))
        if row is None:
            return

        name = layer.get_name()
        row.name_label.setText(name)
        row.name_edit.setText(name)

    def clear_layout(self, layout) -> None:
        """Рекурсивно удаляет дочерние виджеты и вложенные компоновки."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def set_layers(self, layers: list[Layer]) -> None:
        """Заменяет коллекцию слоёв и перестраивает панель."""
        self.layers = layers

        if self.selected_layer not in layers:
            self.selected_layer = layers[0] if layers else None

        self.update_layers()
