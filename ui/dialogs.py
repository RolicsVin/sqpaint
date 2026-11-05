from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QWidget,
)


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

        form = QFormLayout(self)
        form.addRow("Название:", self.name_edit)
        form.addRow("Ширина:", self.width_spin)
        form.addRow("Высота:", self.height_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def get_values(self) -> tuple[str, int, int]:
        return (
            self.name_edit.text().strip(),
            self.width_spin.value(),
            self.height_spin.value(),
        )


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

    name, width, height = dialog.get_values()
    if not name:
        QMessageBox.warning(
            parent,
            "Некорректное название",
            "Введите название проекта.",
        )
        return None

    return name, width, height


def ask_save_project_path(parent: QWidget | None, name: str) -> str:
    """Выбор пути для нового проекта. Пустая строка — пользователь отменил."""
    path, _ = QFileDialog.getSaveFileName(
        parent,
        "Создать проект",
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
        "Открыть проект",
        "",
        f"{PROJECT_FILTER};;Все файлы (*)",
    )
    return path


def confirm_delete_layer(parent: QWidget | None, layer_name: str) -> bool:
    """Спрашивает подтверждение удаления слоя. True — удалить."""
    dialog = DeleteLayerDialog(layer_name, parent)
    return dialog.exec() == QDialog.DialogCode.Accepted


# --- Сообщения ---

def show_file_exists(parent: QWidget | None = None) -> None:
    QMessageBox.warning(
        parent,
        "Файл уже существует",
        "Выберите другое имя или другое расположение файла. "
        "Существующие файлы не перезаписываются.",
    )


def show_create_error(parent: QWidget | None, error: Exception) -> None:
    QMessageBox.critical(
        parent,
        "Не удалось создать проект",
        f"Проект не удалось создать.\n\n{error}",
    )


def show_open_error(parent: QWidget | None, error: Exception) -> None:
    QMessageBox.critical(
        parent,
        "Не удалось открыть проект",
        f"Файл не удалось загрузить. Возможно, он повреждён "
        f"или не является проектом SQPaint.\n\n{error}",
    )


def show_save_error(parent: QWidget | None, error: Exception) -> None:
    QMessageBox.critical(
        parent,
        "Ошибка сохранения",
        f"Не удалось сохранить проект.\n\n{error}",
    )


def show_last_layer_info(parent: QWidget | None = None) -> None:
    QMessageBox.information(
        parent,
        "Удаление слоя",
        "В проекте должен остаться хотя бы один слой.",
    )