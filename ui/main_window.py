import os
import sqlite3

from PyQt6.QtGui import QAction, QImage
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSpinBox,
)

from core.database import ProjectDatabase
from core.models import Layer, Project
from ui.canvas import Canvas
from ui.tool_bar import ToolBar


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


class DomainWindow(QMainWindow):
    HEADERS_HEIGHT = 25

    def __init__(self, project: Project | None, database: ProjectDatabase):
        super().__init__()
        self.project = None
        self.database = database
        self.canvas: Canvas | None = None

        screen = QApplication.primaryScreen()
        if screen is not None:
            size = screen.availableGeometry()
            self.setGeometry(size)

        self.menu_bar = self.menuBar()

        self.file_menu = self.menu_bar.addMenu("Файл")
        self.edit_menu = self.menu_bar.addMenu("Правка")
        self.view_menu = self.menu_bar.addMenu("Вид")
        self.help_menu = self.menu_bar.addMenu("Справка")

        self.new_action = QAction("Создать", self)
        self.open_action = QAction("Открыть", self)
        self.save_action = QAction("Сохранить", self)
        self.exit_action = QAction("Выход", self)

        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        self.new_action.triggered.connect(self.create_project)
        self.open_action.triggered.connect(self.open_project)
        self.save_action.triggered.connect(self.save)
        self.exit_action.triggered.connect(self.close)
        self.save_action.setEnabled(False)

        self.tool_bar = ToolBar(self)
        self.tool_bar.move(0, self.HEADERS_HEIGHT)
        self.tool_bar.resize(self.width(), ToolBar.HEIGHT)
        self.tool_bar.color_selected.connect(self.set_canvas_color)
        self.tool_bar.tool_selected.connect(self.set_canvas_tool)

        if project is not None:
            self.set_project(project)

        self.setWindowTitle("SQPaint")

    def create_project(self) -> None:
        dialog = NewProjectDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        name, width, height = dialog.get_values()
        if not name:
            QMessageBox.warning(
                self,
                "Некорректное название",
                "Введите название проекта.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Создать проект",
            f"{name}.sqlite",
            "Проекты SQPaint (*.sqlite)",
        )
        if not path:
            return

        if not path.lower().endswith(".sqlite"):
            path += ".sqlite"

        if os.path.exists(path):
            QMessageBox.warning(
                self,
                "Файл уже существует",
                "Выберите другое имя или другое расположение файла. "
                "Существующие файлы не перезаписываются.",
            )
            return

        image = QImage(
            width,
            height,
            QImage.Format.Format_ARGB32,
        )
        image.fill(0)
        initial_layer = Layer("Слой 1", 0, True, image)
        project = Project(
            name=name,
            width=width,
            height=height,
            created_at=__import__("datetime").datetime.now(),
            path=path,
            layers=[initial_layer],
        )

        try:
            project = self.database.create(
                path,
                name,
                width,
                height,
            )
            # В БД и в модели должен быть один и тот же начальный слой.
            project.layers.append(initial_layer)
            with self.database.conn:
                self.database._write_layers(project, self.database.conn)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
            QMessageBox.critical(
                self,
                "Не удалось создать проект",
                f"Проект не удалось создать.\n\n{error}",
            )
            return

        self.set_project(project)

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть проект",
            "",
            "Проекты SQPaint (*.sqlite);;Все файлы (*)",
        )
        if not path:
            return

        try:
            project = self.database.load(path)
        except (OSError, sqlite3.Error, ValueError, TypeError) as error:
            QMessageBox.critical(
                self,
                "Не удалось открыть проект",
                f"Файл не удалось загрузить. Возможно, он повреждён "
                f"или не является проектом SQPaint.\n\n{error}",
            )
            return

        self.set_project(project)

    def set_project(self, project: Project) -> None:
        if self.canvas is not None:
            self.canvas.hide()
            self.canvas.deleteLater()

        self.project = project
        self.canvas = Canvas(
            self,
            project.get_layers(),
            project.get_width(),
            project.get_height(),
        )
        self.canvas.set_tool("brush")
        self.canvas.move(0, ToolBar.HEIGHT + self.HEADERS_HEIGHT)
        self.canvas.show()

        self.save_action.setEnabled(True)
        self.setWindowTitle(f"SQPaint — {project.get_name()}")

    def save(self) -> None:
        if self.project is None:
            return

        try:
            self.database.save(self.project)
        except (OSError, sqlite3.Error, RuntimeError) as error:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить проект.\n\n{error}",
            )

    def set_canvas_color(self, color) -> None:
        if self.canvas is not None:
            self.canvas.color = color

    def set_canvas_tool(self, tool_name: str) -> None:
        if self.canvas is not None:
            self.canvas.set_tool(tool_name)

    def closeEvent(self, event) -> None:
        self.database.close()
        super().closeEvent(event)
