import os
import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QImage
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QMessageBox

from core.database import ProjectDatabase
from core.models import Layer, Project
from core import image_utils
from services import recent_projects
from ui.start_window import RecentProjectWindow
from ui.canvas import Canvas
from ui.canvas_view import CanvasView
from ui.tool_bar import ToolBar
from ui.layers_panel import LayerPanel
from ui.dialogs import (
    ask_new_project, ask_open_project_path, ask_save_project_path,
    confirm_delete_layer, show_create_error, show_file_exists,
    show_last_layer_info, show_open_error, show_save_error,
    ask_save_as_path, ask_import_image_path, ask_export_image_path,
    show_file_info,
)


class DomainWindow(QMainWindow):
    HEADERS_HEIGHT = 25

    def __init__(self, project: Project | None, database: ProjectDatabase, settings: dict):
        super().__init__()
        self.project = None
        self.database = database
        self.canvas: Canvas | None = None
        self.canvas_view: CanvasView | None = None

        screen = QApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.availableGeometry())

        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("Файл")
        self.edit_menu = self.menu_bar.addMenu("Правка")
        self.view_menu = self.menu_bar.addMenu("Вид")
        self.help_menu = self.menu_bar.addMenu("Справка")

        self.new_action = QAction("Создать", self)
        self.open_action = QAction("Открыть", self)
        self.save_action = QAction("Сохранить", self)
        self.save_as_action = QAction("Сохранить как", self)
        self.export_submenu = QMenu("Экспортировать", self)
        self.import_action = QAction("Импортировать", self)
        self.exit_action = QAction("Выход", self)
        self.file_info = QAction("О файле", self)
        self.export_png = self.export_submenu.addAction("PNG")
        self.export_jpg = self.export_submenu.addAction("JPG")

        for action in (self.new_action, self.open_action, self.save_action, self.save_as_action):
            self.file_menu.addAction(action)
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
        self.save_as_action.triggered.connect(self.save_as)
        self.import_action.triggered.connect(self.import_image)
        self.export_png.triggered.connect(lambda: self.export_image("png"))
        self.export_jpg.triggered.connect(lambda: self.export_image("jpg"))
        self.exit_action.triggered.connect(self.close)
        self.file_info.triggered.connect(self.open_file_info)
        self.save_action.setEnabled(False)
        self.save_as_action.setEnabled(False)
        self.export_submenu.setEnabled(False)
        self.import_action.setEnabled(False)
        self.file_info.setEnabled(False)

        self.insert = QAction("Вставить как слой", self)
        self.settings = QAction("Настройки", self)
        self.edit_menu.addAction(self.insert)
        self.edit_menu.addAction(self.settings)

        self.sub_windows = QMenu("Окна", self)
        self.layers_panel_viewer = QAction("Панель слоёв", self)
        self.tool_bar_viewer = QAction("Панель инструментов", self)
        self.scroller_viewer = QAction("Ползунок", self)
        self.sub_windows.addAction(self.layers_panel_viewer)
        self.sub_windows.addAction(self.tool_bar_viewer)
        self.sub_windows.addAction(self.scroller_viewer)

        self.theme = QMenu("Тема", self)
        self.dark_theme = QAction("Тёмная тема", self)
        self.white_theme = QAction("Светлая тема", self)
        self.theme.addAction(self.dark_theme)
        self.theme.addAction(self.white_theme)

        self.langague = QMenu("Язык", self)
        self.ru = QAction("Русский", self)
        self.en = QAction("English", self)
        self.langague.addAction(self.ru)
        self.langague.addAction(self.en)
        self.start_window_view_button = QAction("Показать окно приветствия", self)
        self.view_menu.addMenu(self.sub_windows)
        self.view_menu.addMenu(self.theme)
        self.view_menu.addMenu(self.langague)
        self.view_menu.addAction(self.start_window_view_button)

        self.insert = QAction("Обучение", self)
        self.settings = QAction("О программе", self)
        self.help_menu.addAction(self.insert)
        self.help_menu.addAction(self.settings)

        self.tool_bar = ToolBar(self)
        self.tool_bar.move(0, self.HEADERS_HEIGHT)
        self.tool_bar.resize(self.width(), ToolBar.HEIGHT)
        self.tool_bar.color_selected.connect(self.set_canvas_color)
        self.tool_bar.tool_selected.connect(self.set_canvas_tool)
        self.tool_bar.width_changed.connect(self.set_canvas_width)
        self.tool_bar.zoom_changed.connect(self.set_canvas_zoom)

        self.canvas_view = CanvasView(self)
        self.canvas_view.zoom_changed.connect(self.tool_bar.set_zoom)
        self.layer_panel = LayerPanel(self, [])
        self.layer_panel.add_layer_requested.connect(self.add_layer)
        self.layer_panel.remove_layer_requested.connect(self.remove_layer)
        self.layer_panel.layer_selected.connect(self.select_layer)
        self._layout_child_widgets()

        if project is not None:
            self.set_project(project)

        self.setWindowTitle("SQPaint")
        self.recent_projects_window = RecentProjectWindow()
        self.recent_projects_window.project_select.connect(self.open_project_path)
        self.recent_projects_window.create_project.connect(self.create_project)
        self.recent_projects_window.open_project.connect(self.open_project)
        self.show()
        self.recent_projects_window.show()

    def _layout_child_widgets(self) -> None:
        panel_width = LayerPanel.WIDTH
        top = self.HEADERS_HEIGHT + ToolBar.HEIGHT
        self.tool_bar.setGeometry(0, self.HEADERS_HEIGHT, self.width(), ToolBar.HEIGHT)
        self.canvas_view.setGeometry(
            0, top, max(0, self.width() - panel_width),
            max(0, self.height() - top)
        )
        self.layer_panel.setGeometry(
            self.width() - panel_width, 0, panel_width, self.height()
        )
        self.layer_panel.raise_()
        self.tool_bar.raise_()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._layout_child_widgets()

    def create_project(self) -> None:
        values = ask_new_project(self)
        if values is None:
            return
        name, width, height = values
        path = ask_save_project_path(self, name)
        if not path:
            return
        if os.path.exists(path):
            show_file_exists(self)
            return

        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(0xFFFFFFFF)
        initial_layer = Layer("Слой 1", 0, True, image)
        try:
            project = self.database.create(path, name, width, height)
            project.layers.append(initial_layer)
            self.database.save(project)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
            show_create_error(self, error)
            return
        self.set_project(project)

    def open_project(self) -> None:
        self.open_project_path(ask_open_project_path(self))

    def open_project_path(self, path: str):
        if not path:
            return
        try:
            project = self.database.load(path)
        except (OSError, sqlite3.Error, ValueError, TypeError) as error:
            show_open_error(self, error)
            return
        self.set_project(project)

    def set_project(self, project: Project) -> None:
        self.project = project
        self.canvas = Canvas(
            self.canvas_view, project.get_layers(),
            project.get_width(), project.get_height()
        )
        self.canvas.set_tool(Canvas.BRUSH)
        self.canvas_view.set_canvas(self.canvas)
        self.layer_panel.layer_change.connect(
            self.canvas.re_draw_canvas, Qt.ConnectionType.UniqueConnection
        )
        self.layer_panel.set_layers(project.get_layers())
        self.canvas_view.set_zoom(100)
        self.save_action.setEnabled(True)
        self.save_as_action.setEnabled(True)
        self.export_submenu.setEnabled(True)
        self.import_action.setEnabled(True)
        self.file_info.setEnabled(True)
        self.setWindowTitle(f"SQPaint — {project.get_name()}")
        recent_projects.add_recent_project(project)

    def add_layer(self) -> None:
        if self.project is None or self.canvas is None:
            return
        existing_names = {layer.get_name() for layer in self.project.layers}
        number = 1
        while f"Слой {number}" in existing_names:
            number += 1
        image = QImage(
            self.project.get_width(), self.project.get_height(),
            QImage.Format.Format_ARGB32
        )
        image.fill(0)
        z_order = max(
            (layer.get_z_order() for layer in self.project.layers), default=-1
        ) + 1
        layer = Layer(f"Слой {number}", z_order, True, image)
        self.project.layers.append(layer)
        self.layer_panel.set_layers(self.project.get_layers())
        self.canvas.layers = self.project.get_layers()
        self.canvas.active = len(self.project.layers) - 1
        self.layer_panel._select_layer(self.canvas.active)
        self.canvas.update()

    def remove_layer(self, layer: Layer) -> None:
        if self.project is None or self.canvas is None:
            return
        if layer not in self.project.layers:
            return
        if len(self.project.layers) <= 1:
            show_last_layer_info(self)
            return
        if not confirm_delete_layer(self, layer.get_name()):
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
        if self.canvas is None or not (0 <= index < len(self.canvas.layers)):
            return
        self.canvas.active = index

    def save(self) -> None:
        if self.project is None:
            return
        try:
            self.database.save(self.project)
        except (OSError, sqlite3.Error, RuntimeError) as error:
            show_save_error(self, error)

    def set_canvas_color(self, color) -> None:
        if self.canvas is not None:
            self.canvas.color = color

    def set_canvas_tool(self, tool_name: str) -> None:
        if self.canvas is not None:
            self.canvas.set_tool(tool_name)

    def set_canvas_width(self, width: int) -> None:
        if self.canvas is not None:
            self.canvas.width_px = width

    def set_canvas_zoom(self, percent: int) -> None:
        if self.canvas_view is not None:
            self.canvas_view.set_zoom(percent)

    def save_as(self) -> None:
        if self.project is None:
            return
        path = ask_save_as_path(self, self.project.get_name())
        if not path:
            return
        if os.path.exists(path):
            show_file_exists(self)
            return
        try:
            self.database.save(self.project)
            destination = sqlite3.connect(path)
            try:
                self.database.conn.backup(destination)
            finally:
                destination.close()
            project = self.database.load(path)
            self.set_project(project)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
            show_save_error(self, error)

    def import_image(self) -> None:
        if self.project is None or self.canvas is None:
            return
        path = ask_import_image_path(self)
        if not path:
            return
        image = QImage(path)
        if image.isNull():
            QMessageBox.warning(
                self, "Импорт изображения",
                "Не удалось открыть выбранное изображение."
            )
            return
        image = image.convertToFormat(QImage.Format.Format_ARGB32)
        existing_names = {layer.get_name() for layer in self.project.layers}
        number = 1
        while f"Импорт {number}" in existing_names:
            number += 1
        z_order = max(
            (layer.get_z_order() for layer in self.project.layers), default=-1
        ) + 1
        layer = Layer(f"Импорт {number}", z_order, True, image)
        self.project.layers.append(layer)
        self.canvas.layers = self.project.get_layers()
        self.canvas.active = len(self.project.layers) - 1
        self.layer_panel.set_layers(self.project.get_layers())
        self.layer_panel._select_layer(self.canvas.active)
        self.canvas.update()

    def export_image(self, image_format: str) -> None:
        if self.canvas is None:
            return
        path = ask_export_image_path(self, image_format)
        if not path:
            return
        output = self.canvas.get_image()
        if not image_utils.save_image(output, path, image_format):
            QMessageBox.critical(
                self, "Экспорт изображения",
                f"Не удалось сохранить изображение:\n{path}"
            )

    def open_file_info(self) -> None:
        if self.project is None:
            return
        try:
            self.database.save(self.project)
        except (OSError, sqlite3.Error, RuntimeError) as error:
            show_save_error(self, error)
            return
        show_file_info(self, self.project.get_path())

    def closeEvent(self, event) -> None:
        self.database.close()
        super().closeEvent(event)
