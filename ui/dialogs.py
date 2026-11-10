from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from core.localization import LocalizedComboBox


def _tr(parent, ru: str, en: str) -> str:
    manager = getattr(parent, "localization", None)
    return en if manager is not None and manager.language == "en" else ru


from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    """Окно настроек SQPaint. Новые разделы добавляются отдельными вкладками."""

    apply_requested = pyqtSignal(dict)

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        from copy import deepcopy
        from PyQt6.QtWidgets import (
            QCheckBox, QComboBox, QHBoxLayout, QPushButton, QTabWidget,
        )

        self.setWindowTitle("Настройки")
        self.setModal(True)
        self.resize(460, 300)
        self._settings = deepcopy(settings if isinstance(settings, dict) else {})
        view = self._settings.setdefault("view", {})
        project = getattr(parent, "project", None)
        self._project_available = project is not None

        root = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        root.addWidget(self.tabs)

        # Вкладка «Вид». При добавлении других разделов создавайте здесь
        # отдельные вкладки и сохраняйте их параметры в соответствующих ключах.
        view_page = QWidget(self)
        view_form = QFormLayout(view_page)

        self.theme_combo = LocalizedComboBox(view_page)
        self.theme_combo.add_localized_item({"ru": "Тёмная", "en": "Dark"}, "dark")
        self.theme_combo.add_localized_item({"ru": "Светлая", "en": "Light"}, "light")
        theme_index = self.theme_combo.findData(view.get("theme", "dark"))
        self.theme_combo.setCurrentIndex(max(0, theme_index))
        view_form.addRow("Тема:", self.theme_combo)

        self.layer_panel_check = QCheckBox("Показывать панель слоёв", view_page)
        self.layer_panel_check.setChecked(view.get("layer_panel_visible", True))
        view_form.addRow(self.layer_panel_check)

        self.toolbar_check = QCheckBox("Показывать панель инструментов", view_page)
        self.toolbar_check.setChecked(view.get("toolbar_visible", True))
        view_form.addRow(self.toolbar_check)

        self.zoom_check = QCheckBox("Показывать управление масштабом", view_page)
        self.zoom_check.setChecked(view.get("zoom_control_visible", True))
        view_form.addRow(self.zoom_check)

        self.welcome_check = QCheckBox(
            "Показывать окно приветствия при запуске", view_page
        )
        self.welcome_check.setChecked(view.get("show_welcome", True))
        view_form.addRow(self.welcome_check)

        self.tabs.addTab(view_page, "Вид")

        # Вкладка параметров открытого проекта.
        project_page = QWidget(self)
        project_form = QFormLayout(project_page)
        self.project_transparency_combo = LocalizedComboBox(project_page)
        self.project_transparency_combo.add_localized_item({"ru": "Да", "en": "Yes"}, True)
        self.project_transparency_combo.add_localized_item({"ru": "Нет", "en": "No"}, False)
        transparency = bool(getattr(project, "supports_transparency", True))
        self.project_transparency_combo.setCurrentIndex(max(0, self.project_transparency_combo.findData(transparency)))
        self.project_history_spin = QSpinBox(project_page)
        self.project_history_spin.setRange(1, 1000)
        self.project_history_spin.setValue(max(1, int(getattr(project, "max_undo_steps", 10))))
        project_form.addRow("Поддержка прозрачности:", self.project_transparency_combo)
        project_form.addRow("Размер истории действий:", self.project_history_spin)
        if not self._project_available:
            self.project_transparency_combo.setEnabled(False)
            self.project_history_spin.setEnabled(False)
        self.tabs.addTab(project_page, "Проект")

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        self.cancel_button = QPushButton("Отмена", self)
        self.apply_button = QPushButton("Применить", self)
        self.exit_button = QPushButton("Выход", self)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.apply_button)
        buttons_layout.addWidget(self.exit_button)
        root.addLayout(buttons_layout)

        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self._apply)
        self.exit_button.clicked.connect(self._apply_and_close)

        manager = getattr(parent, "localization", None)
        if manager is not None:
            manager.register(self, {"ru": "Настройки", "en": "Settings"})
            manager.register(view_form.itemAt(0, QFormLayout.ItemRole.LabelRole).widget(), {"ru": "Тема:", "en": "Theme:"})
            self.tabs.setTabText(0, "View" if manager.language == "en" else "Вид")
            self.tabs.setTabText(1, "Project" if manager.language == "en" else "Проект")
            manager.register(project_form.itemAt(0, QFormLayout.ItemRole.LabelRole).widget(), {"ru": "Поддержка прозрачности:", "en": "Transparency support:"})
            manager.register(project_form.itemAt(1, QFormLayout.ItemRole.LabelRole).widget(), {"ru": "Размер истории действий:", "en": "Action history size:"})
            manager.register(self.project_transparency_combo, {})
            self.project_transparency_combo.set_language(manager.language)
            manager.register(self.cancel_button, {"ru": "Отмена", "en": "Cancel"})
            manager.register(self.apply_button, {"ru": "Применить", "en": "Apply"})
            manager.register(self.exit_button, {"ru": "Выход", "en": "Close"})
            manager.register(self.layer_panel_check, {"ru": "Показывать панель слоёв", "en": "Show layers panel"})
            manager.register(self.toolbar_check, {"ru": "Показывать панель инструментов", "en": "Show tools panel"})
            manager.register(self.zoom_check, {"ru": "Показывать управление масштабом", "en": "Show zoom control"})
            manager.register(self.welcome_check, {"ru": "Показывать окно приветствия при запуске", "en": "Show welcome window on startup"})
            manager.register(self.theme_combo, {})
            self.theme_combo.set_language(manager.language)
            self.tabs.setTabText(0, "View" if manager.language == "en" else "Вид")

    def _collect_settings(self) -> dict:
        """Собирает значения всех вкладок в структуру настроек."""
        view = self._settings.setdefault("view", {})
        view.update({
            "theme": self.theme_combo.currentData(),
            "layer_panel_visible": self.layer_panel_check.isChecked(),
            "toolbar_visible": self.toolbar_check.isChecked(),
            "zoom_control_visible": self.zoom_check.isChecked(),
            "show_welcome": self.welcome_check.isChecked(),
        })
        if self._project_available:
            self._settings["project"] = {
                "supports_transparency": bool(self.project_transparency_combo.currentData()),
                "max_undo_steps": self.project_history_spin.value(),
            }
        return self._settings

    def _apply(self) -> None:
        self.apply_requested.emit(self._collect_settings())

    def _apply_and_close(self) -> None:
        self._apply()
        self.accept()


class NewProjectDialog(QDialog):
    """Диалог параметров нового проекта."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новый проект")
        self.setModal(True)

        self.name_edit = QLineEdit("Новый проект", self)

        self.width_spin = QSpinBox(self)
        self.width_spin.setRange(1, 8192)
        self.width_spin.setValue(1920)
        self.width_spin.setSuffix(" px")

        self.height_spin = QSpinBox(self)
        self.height_spin.setRange(1, 8192)
        self.height_spin.setValue(1080)
        self.height_spin.setSuffix(" px")

        self.transparency_combo = LocalizedComboBox(self)
        self.transparency_combo.add_localized_item({"ru": "Да", "en": "Yes"}, True)
        self.transparency_combo.add_localized_item({"ru": "Нет", "en": "No"}, False)
        self.transparency_combo.setCurrentIndex(0)
        self.history_spin = QSpinBox(self)
        self.history_spin.setRange(1, 1000)
        self.history_spin.setValue(10)

        form = QFormLayout(self)
        form.addRow("Название:", self.name_edit)
        form.addRow("Ширина:", self.width_spin)
        form.addRow("Высота:", self.height_spin)
        form.addRow("Поддержка прозрачности:", self.transparency_combo)
        form.addRow("Размер истории действий:", self.history_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        manager = getattr(parent, "localization", None)
        if manager is not None:
            manager.register(self, {"ru": "Новый проект", "en": "New project"})
            manager.register(self.name_edit, {"ru": "Новый проект", "en": "New project"})
            manager.register(form.itemAt(0, QFormLayout.ItemRole.LabelRole).widget(), {"ru": "Название:", "en": "Name:"})
            manager.register(form.itemAt(1, QFormLayout.ItemRole.LabelRole).widget(), {"ru": "Ширина:", "en": "Width:"})
            manager.register(form.itemAt(2, QFormLayout.ItemRole.LabelRole).widget(), {"ru": "Высота:", "en": "Height:"})
            manager.register(form.itemAt(3, QFormLayout.ItemRole.LabelRole).widget(), {"ru": "Поддержка прозрачности:", "en": "Transparency support:"})
            manager.register(form.itemAt(4, QFormLayout.ItemRole.LabelRole).widget(), {"ru": "Размер истории действий:", "en": "Action history size:"})
            manager.register(self.transparency_combo, {})
            self.transparency_combo.set_language(manager.language)
            manager.register(buttons.button(QDialogButtonBox.StandardButton.Ok), {"ru": "ОК", "en": "OK"})
            manager.register(buttons.button(QDialogButtonBox.StandardButton.Cancel), {"ru": "Отмена", "en": "Cancel"})
            manager.set_language(manager.language)

    def get_values(self) -> tuple[str, int, int, bool, int]:
        return (
            self.name_edit.text().strip(),
            self.width_spin.value(),
            self.height_spin.value(),
            bool(self.transparency_combo.currentData()),
            self.history_spin.value(),
        )


class CanvasSizeDialog(QDialog):
    """Диалог изменения размеров документа."""

    def __init__(self, width: int, height: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Размер холста")
        self.setModal(True)
        self.setMinimumWidth(300)

        self.width_spin = QSpinBox(self)
        self.width_spin.setRange(1, 8192)
        self.width_spin.setValue(width)
        self.width_spin.setSuffix(" px")

        self.height_spin = QSpinBox(self)
        self.height_spin.setRange(1, 8192)
        self.height_spin.setValue(height)
        self.height_spin.setSuffix(" px")

        form = QFormLayout(self)
        form.addRow("Ширина:", self.width_spin)
        form.addRow("Высота:", self.height_spin)
        form.addRow(QLabel(
            "При уменьшении холста содержимое за его границами будет обрезано."
        ))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Применить")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        manager = getattr(parent, "localization", None)
        if manager is not None:
            manager.register(self, {"ru": "Размер холста", "en": "Canvas size"})
            manager.register(form.itemAt(0, QFormLayout.ItemRole.LabelRole).widget(), {"ru": "Ширина:", "en": "Width:"})
            manager.register(form.itemAt(1, QFormLayout.ItemRole.LabelRole).widget(), {"ru": "Высота:", "en": "Height:"})
            manager.register(buttons.button(QDialogButtonBox.StandardButton.Ok), {"ru": "Применить", "en": "Apply"})
            manager.register(buttons.button(QDialogButtonBox.StandardButton.Cancel), {"ru": "Отмена", "en": "Cancel"})
            manager.register(form.itemAt(2, QFormLayout.ItemRole.SpanningRole).widget(), {"ru": "При уменьшении холста содержимое за его границами будет обрезано.", "en": "Content outside the canvas will be cropped when its size is reduced."})
            manager.set_language(manager.language)

    def get_size(self) -> tuple[int, int]:
        return self.width_spin.value(), self.height_spin.value()


class DeleteLayerDialog(QDialog):
    """Диалог подтверждения удаления слоя."""

    def __init__(self, layer_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Удаление слоя")
        self.setModal(True)

        layout = QFormLayout(self)
        layout.addRow(QLabel(
            f'Вы действительно хотите удалить слой «{layer_name}»?'
        ))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes
            | QDialogButtonBox.StandardButton.No,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Yes).setText("Удалить")
        buttons.button(QDialogButtonBox.StandardButton.No).setText("Отмена")
        buttons.button(QDialogButtonBox.StandardButton.No).setDefault(True)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        manager = getattr(parent, "localization", None)
        if manager is not None:
            manager.register(self, {"ru": "Удаление слоя", "en": "Delete layer"})
            manager.register(layout.itemAt(0).widget(), {
                "ru": f'Вы уверены, что хотите удалить этот слой «{layer_name}»?',
                "en": f'Are you sure you want to delete this layer “{layer_name}”?'
            })
            manager.register(buttons.button(QDialogButtonBox.StandardButton.Yes), {"ru": "Удалить", "en": "Delete"})
            manager.register(buttons.button(QDialogButtonBox.StandardButton.No), {"ru": "Отмена", "en": "Cancel"})
            manager.set_language(manager.language)

# ---------------------------------------------------------------------------
# Функции-обёртки: всё, что окно показывает пользователю, живёт здесь.
# ---------------------------------------------------------------------------

PROJECT_EXTENSION = ".sqlite"
PROJECT_FILTER = "Проекты SQPaint (*.sqlite)"


# --- Запросы данных у пользователя ---

def ask_new_project(parent: QWidget | None = None) -> tuple[str, int, int] | None:
    """Показывает диалог нового проекта.

    Возвращает (название, ширина, высота) или None, если пользователь
    отменил диалог или ввёл пустое название.
    """
    dialog = NewProjectDialog(parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None

    name, width, height, supports_transparency, max_undo_steps = dialog.get_values()
    if not name:
        QMessageBox.warning(
            parent,
            _tr(parent, "Некорректное название", "Invalid name"),
            _tr(parent, "Введите название проекта.", "Enter a project name."),
        )
        return None

    return name, width, height, supports_transparency, max_undo_steps


def ask_save_project_path(parent: QWidget | None, name: str) -> str:
    """Выбор пути для нового проекта. Пустая строка — пользователь отменил."""
    path, _ = QFileDialog.getSaveFileName(
        parent,
        _tr(parent, "Создать проект", "Create project"),
        f"{name}{PROJECT_EXTENSION}",
        PROJECT_FILTER,
    )
    if path and not path.lower().endswith(PROJECT_EXTENSION):
        path += PROJECT_EXTENSION
    return path


def ask_open_project_path(parent: QWidget | None = None) -> str:
    """Выбор существующего проекта. Пустая строка — пользователь отменил."""
    path, _ = QFileDialog.getOpenFileName(
        parent,
        _tr(parent, "Открыть проект", "Open project"),
        "",
        f"{_tr(parent, 'Проекты SQPaint (*.sqlite)', 'SQPaint projects (*.sqlite)')};;{_tr(parent, 'Все файлы (*)', 'All files (*)')}",
    )
    return path


def ask_canvas_size(
    parent: QWidget | None, width: int, height: int
) -> tuple[int, int] | None:
    """Возвращает новые размеры холста или None при отмене."""
    dialog = CanvasSizeDialog(width, height, parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialog.get_size()


def confirm_delete_layer(parent: QWidget | None, layer_name: str) -> bool:
    """Спрашивает подтверждение удаления слоя. True — удалить."""
    dialog = DeleteLayerDialog(layer_name, parent)
    return dialog.exec() == QDialog.DialogCode.Accepted


# --- Сообщения ---

def show_file_exists(parent: QWidget | None = None) -> None:
    QMessageBox.warning(
        parent,
        _tr(parent, "Файл уже существует", "File already exists"),
        _tr(parent, "Выберите другое имя или другое расположение файла. Существующие файлы не перезаписываются.", "Choose another name or location. Existing files are not overwritten."),
    )


def show_create_error(parent: QWidget | None, error: Exception) -> None:
    QMessageBox.critical(
        parent,
        _tr(parent, "Не удалось создать проект", "Could not create project"),
        _tr(parent, f"Проект не удалось создать.\n\n{error}", f"Could not create the project.\n\n{error}"),
    )


def show_open_error(parent: QWidget | None, error: Exception) -> None:
    QMessageBox.critical(
        parent,
        _tr(parent, "Не удалось открыть проект", "Could not open project"),
        _tr(parent, f"Файл не удалось загрузить. Возможно, он повреждён или не является проектом SQPaint.\n\n{error}", f"The file could not be loaded. It may be damaged or not be an SQPaint project.\n\n{error}"),
    )


def show_save_error(parent: QWidget | None, error: Exception) -> None:
    QMessageBox.critical(
        parent,
        _tr(parent, "Ошибка сохранения", "Save error"),
        _tr(parent, f"Не удалось сохранить проект.\n\n{error}", f"Could not save the project.\n\n{error}"),
    )


def show_last_layer_info(parent: QWidget | None = None) -> None:
    QMessageBox.information(
        parent,
        _tr(parent, "Удаление слоя", "Delete layer"),
        _tr(parent, "В проекте должен остаться хотя бы один слой.", "A project must contain at least one layer."),
    )


# --- Диалоги файловых операций ---

def ask_save_as_path(parent: QWidget | None = None, name: str = "Проект") -> str:
    path, _ = QFileDialog.getSaveFileName(
        parent, _tr(parent, "Сохранить проект как", "Save project as"), f"{name}.sqlite",
        f"{_tr(parent, 'Проекты SQPaint (*.sqlite)', 'SQPaint projects (*.sqlite)')};;{_tr(parent, 'Все файлы (*)', 'All files (*)')}",
    )
    if path and not path.lower().endswith(PROJECT_EXTENSION):
        path += PROJECT_EXTENSION
    return path


def ask_import_image_path(parent: QWidget | None = None) -> str:
    path, _ = QFileDialog.getOpenFileName(
        parent, _tr(parent, "Импортировать изображение", "Import image"),
        "", f"{_tr(parent, 'Изображения', 'Images')} (*.png *.jpg *.jpeg *.bmp *.webp);;{_tr(parent, 'Все файлы (*)', 'All files (*)')}",
    )
    return path


def ask_export_image_path(parent: QWidget | None, image_format: str) -> str:
    ext = image_format.lower()
    path, _ = QFileDialog.getSaveFileName(
        parent, _tr(parent, f"Экспортировать {ext.upper()}", f"Export {ext.upper()}"),
        f"Изображение.{ext}",
        f"{ext.upper()} (*.{ext})",
    )
    if path and not path.lower().endswith(f".{ext}"):
        path += f".{ext}"
    return path


class FileInfoDialog(QDialog):
    """Окно просмотра содержимого SQLite-файла проекта."""

    TABLES = (
        ("project", "project"),
        ("layers", "layers"),
        ("logs", "logs"),
    )

    def __init__(self, database_path: str, parent=None):
        super().__init__(parent)
        import sqlite3

        self.setWindowTitle("О файле проекта")
        self.resize(900, 520)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)
        manager = getattr(parent, "localization", None)
        if manager is not None:
            manager.register(self, {"ru": "О файле проекта", "en": "Project file information"})

        try:
            connection = sqlite3.connect(
                f"file:{database_path}?mode=ro", uri=True
            )
            try:
                for tab_title, table_name in self.TABLES:
                    table = QTableWidget(self)
                    table.setEditTriggers(
                        QTableWidget.EditTrigger.NoEditTriggers
                    )
                    table.setAlternatingRowColors(True)
                    table.setSelectionBehavior(
                        QTableWidget.SelectionBehavior.SelectRows
                    )
                    self._load_table(connection, table, table_name)
                    self.tabs.addTab(table, tab_title)
            finally:
                connection.close()
        except sqlite3.Error as error:
            QMessageBox.critical(
                self, _tr(parent, "Ошибка чтения файла", "File read error"),
                _tr(parent, f"Не удалось прочитать содержимое SQLite-файла.\n\n{error}", f"Could not read the SQLite file contents.\n\n{error}"),
            )

    @staticmethod
    def _load_table(connection, widget: QTableWidget, table_name: str) -> None:
        cursor = connection.execute(f'SELECT * FROM "{table_name}"')
        columns = [item[0] for item in cursor.description or ()]
        rows = cursor.fetchall()

        widget.setColumnCount(len(columns))
        widget.setHorizontalHeaderLabels(columns)
        widget.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                if isinstance(value, bytes):
                    display = f"<BLOB: {len(value)} байт>"
                elif value is None:
                    display = "NULL"
                else:
                    display = str(value)
                widget.setItem(
                    row_index, column_index, QTableWidgetItem(display)
                )

        header = widget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)


def show_file_info(parent: QWidget | None, database_path: str) -> None:
    dialog = FileInfoDialog(database_path, parent)
    dialog.exec()


class AboutDialog(QDialog):
    """Информационное окно о программе SQPaint."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе SQPaint")
        self.setModal(True)
        self.setFixedWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        logo_label = QLabel(self)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = Path(__file__).resolve().parents[1] / "logo.png"
        pixmap = QPixmap(str(logo_path))
        if not pixmap.isNull():
            logo_label.setPixmap(
                pixmap.scaled(
                    160, 160,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            layout.addWidget(logo_label)

        title = QLabel("<h2 style='margin: 0'>SQPaint</h2>", self)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        description = QLabel(
            "Растровый графический редактор с поддержкой слоёв. "
            "Проекты сохраняются в формате SQLite (.sqlite).",
            self,
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        technology = QLabel("Создано на Python и PyQt6", self)
        technology.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(technology)

        project_link = QLabel(
            '<a href="https://github.com/RolicsVin/sqpaint">'
            "Исходный код на GitHub</a>",
            self,
        )
        project_link.setOpenExternalLinks(True)
        project_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(project_link)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok, parent=self
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Закрыть")
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        manager = getattr(parent, "localization", None)
        if manager is not None:
            manager.register(self, {"ru": "О программе SQPaint", "en": "About SQPaint"})
            manager.register(description, {"ru": "Растровый графический редактор с поддержкой слоёв. Проекты сохраняются в формате SQLite (.sqlite).", "en": "A raster graphics editor with layer support. Projects are saved in SQLite (.sqlite) format."})
            manager.register(technology, {"ru": "Создано на Python и PyQt6", "en": "Created with Python and PyQt6"})
            manager.register(project_link, {"ru": "Исходный код на GitHub", "en": "Source code on GitHub"})
            manager.register(buttons.button(QDialogButtonBox.StandardButton.Ok), {"ru": "Закрыть", "en": "Close"})


def show_about(parent: QWidget | None = None) -> None:
    """Показывает окно «О программе»."""
    AboutDialog(parent).exec()

class OperationDialog(QDialog):
    """Короткое модальное окно, отображаемое во время файловой операции."""

    def __init__(self, parent, message_ru: str, message_en: str):
        super().__init__(parent)
        self.setWindowTitle(_tr(parent, "Выполняется операция", "Working"))
        self.setModal(True)
        self.setFixedSize(320, 86)
        layout = QVBoxLayout(self)
        label = QLabel(_tr(parent, message_ru, message_en), self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)

    def __enter__(self):
        self.show()
        QApplication.processEvents()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        QApplication.processEvents()
        return False


def confirm_exit(parent, has_unsaved_changes: bool) -> bool:
    """Запрашивает подтверждение выхода с учётом несохранённых изменений."""
    if has_unsaved_changes:
        title = _tr(parent, "Несохранённые изменения", "Unsaved changes")
        message = _tr(
            parent,
            "Вы уверены, что хотите выйти не сохранив?",
            "Are you sure you want to exit without saving?",
        )
    else:
        title = _tr(parent, "Выход", "Exit")
        message = _tr(
            parent,
            "Вы уверены, что хотите выйти?",
            "Are you sure you want to exit?",
        )
    result = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes

