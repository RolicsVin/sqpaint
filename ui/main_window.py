import sqlite3

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
)

from core.database import ProjectDatabase
from core.models import Project
from ui.canvas import Canvas
from ui.tool_bar import ToolBar


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
