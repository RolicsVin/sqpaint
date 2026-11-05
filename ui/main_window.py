import os
import sqlite3
from services import recent_projects

from PyQt6.QtGui import QAction, QActionGroup, QImage
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QMenu
)

from core.database import ProjectDatabase
from core.models import Layer, Project
from ui.canvas import Canvas
from ui.tool_bar import ToolBar
from ui.layers_panel import LayerPanel
from ui.dialogs import *


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

        # Файл
        self.new_action = QAction("Создать", self)
        self.open_action = QAction("Открыть", self) # подразумевается только sqlite
        self.save_action = QAction("Сохранить", self)
        self.save_as_action = QAction("Сохранить как", self)

        self.export_submenu = QMenu("Экспорировать", self)
        self.import_action = QAction("Импортировать", self) # Тут подразумевается png, jpg и другие, не sqlite!

        self.exit_action = QAction("Выход", self)
        self.file_info = QAction("О Файле", self)

        self.export_png = self.export_submenu.addAction("PNG")
        self.export_jpg = self.export_submenu.addAction("JPG")

        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)

        self.file_menu.addSeparator()
        self.file_menu.addMenu(self.export_submenu)
        self.file_menu.addAction(self.import_action)

        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        self.file_menu.addSeparator()
        self.file_menu.addAction(self.file_info)

        self.new_action.triggered.connect(self.create_project)
        self.open_action.triggered.connect(self.open_project)
        self.save_action.triggered.connect(self.save)
        self.exit_action.triggered.connect(self.close)
        self.save_action.setEnabled(False)
        self.export_submenu.setEnabled(False)

        # Правка
        self.insert = QAction("Вставить как слой", self)
        self.settings = QAction("Настройки", self)

        self.edit_menu.addAction(self.insert)
        self.edit_menu.addAction(self.settings)

        # Вид

        # Справка
        self.insert = QAction("Обучение", self)
        self.settings = QAction("О программе", self)

        self.help_menu.addAction(self.insert)
        self.help_menu.addAction(self.settings)

        # Панель инструментов и слои
        self.tool_bar = ToolBar(self)
        self.tool_bar.move(0, self.HEADERS_HEIGHT)
        self.tool_bar.resize(self.width(), ToolBar.HEIGHT)

        self.layer_panel = LayerPanel(self, [])
        self.layer_panel.resize(LayerPanel.WIDTH, self.height())
        self.layer_panel.move(self.width() - LayerPanel.WIDTH, 0)
        self.layer_panel.add_layer_requested.connect(self.add_layer)
        self.layer_panel.remove_layer_requested.connect(self.remove_layer)
        self.layer_panel.layer_selected.connect(self.select_layer)

        self.tool_bar.color_selected.connect(self.set_canvas_color)
        self.tool_bar.tool_selected.connect(self.set_canvas_tool)

        if project is not None:
            self.set_project(project)

        self.setWindowTitle("SQPaint")


    def resizeEvent(self, event) -> None:
        """Подгоняет положение и высоту боковой панели под размер окна."""
        super().resizeEvent(event)

        if hasattr(self, "layer_panel"):
            self.layer_panel.setGeometry(
                self.width() - LayerPanel.WIDTH,
                0,
                LayerPanel.WIDTH,
                self.height(),
            )

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
        image.fill(0xFFFFFFFF)
        initial_layer = Layer("Слой 1", 0, True, image)
        try:
            project = self.database.create(
                path,
                name,
                width,
                height,
            )
            project.layers.append(initial_layer)
            self.database.save(project)
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
        self.layer_panel.layer_change.connect(self.canvas.re_draw_canvas)
        self.canvas.show()

        self.layer_panel.set_layers(project.get_layers())

        self.save_action.setEnabled(True)
        self.export_submenu.setEnabled(True)
        self.setWindowTitle(f"SQPaint — {project.get_name()}")

        recent_projects.add_recent_project(project)

    def add_layer(self) -> None:
        """Создаёт новый прозрачный слой и делает его активным."""
        if self.project is None or self.canvas is None:
            return

        existing_names = {layer.get_name() for layer in self.project.layers}
        number = 1
        while f"Слой {number}" in existing_names:
            number += 1

        image = QImage(
            self.project.get_width(),
            self.project.get_height(),
            QImage.Format.Format_ARGB32,
        )
        image.fill(0)

        z_order = max(
            (layer.get_z_order() for layer in self.project.layers),
            default=-1,
        ) + 1
        layer = Layer(f"Слой {number}", z_order, True, image)
        self.project.layers.append(layer)

        self.layer_panel.set_layers(self.project.get_layers())
        self.canvas.layers = self.project.get_layers()
        self.canvas.active = len(self.project.layers) - 1
        self.layer_panel._select_layer(self.canvas.active)
        self.canvas.update()

    def remove_layer(self, layer: Layer) -> None:
        """Удаляет выбранный слой, сохраняя в проекте хотя бы один слой."""
        if self.project is None or self.canvas is None:
            return

        if layer not in self.project.layers:
            return

        if len(self.project.layers) <= 1:
            QMessageBox.information(
                self,
                "Удаление слоя",
                "В проекте должен остаться хотя бы один слой.",
            )
            return

        dialog = DeleteLayerDialog(layer.get_name(), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        old_index = self.project.layers.index(layer)
        self.project.layers.remove(layer)

        active_index = min(old_index, len(self.project.layers) - 1)
        self.canvas.layers = self.project.get_layers()
        self.canvas.active = active_index
        self.layer_panel.set_layers(self.project.get_layers())
        self.layer_panel._select_layer(active_index)
        self.canvas.update()

    def select_layer(self, index: int) -> None:
        """Переключает активный слой холста."""
        if self.canvas is None or not (0 <= index < len(self.canvas.layers)):
            return

        self.canvas.active = index

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
