import os
import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QImage, QPalette, QColor
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QMessageBox

from core.database import ProjectDatabase
from core.models import Layer, Project
from core import image_utils
from services import recent_projects, settings as settings_service
from ui.start_window import RecentProjectWindow
from ui.canvas import Canvas
from ui.canvas_view import CanvasView
from ui.tool_bar import ToolBar
from ui.layers_panel import LayerPanel
from ui.dialogs import (
    SettingsDialog,
    ask_new_project, ask_open_project_path, ask_save_project_path,
    confirm_delete_layer, show_create_error, show_file_exists,
    show_last_layer_info, show_open_error, show_save_error,
    ask_save_as_path, ask_import_image_path, ask_export_image_path,
    show_file_info, ask_canvas_size,
)


class DomainWindow(QMainWindow):
    HEADERS_HEIGHT = 25

    def __init__(self, project: Project | None, database: ProjectDatabase, settings: dict):
        super().__init__()
        self.project = None
        self.database = database
        self.settings_data = settings if isinstance(settings, dict) else settings_service.load_data()
        self.view_settings = self.settings_data.setdefault("view", {})
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

        self.canvas_size = QAction("Размер холста", self)
        self.paste_as_layer_action = QAction("Вставить как слой", self)
        self.settings_action = QAction("Настройки", self)
        self.edit_menu.addAction(self.canvas_size)
        self.edit_menu.addAction(self.paste_as_layer_action)
        self.edit_menu.addAction(self.settings_action)
        # Временная заглушка: пока «Вставить как слой» использует импорт изображения.
        self.canvas_size.triggered.connect(self.change_canvas_size)
        self.canvas_size.setEnabled(False)
        self.paste_as_layer_action.triggered.connect(self.import_image)
        self.settings_action.triggered.connect(self.open_settings)

        self.sub_windows = QMenu("Окна", self)
        self.layers_panel_viewer = QAction("Панель слоёв", self)
        self.tool_bar_viewer = QAction("Панель инструментов", self)
        self.scroller_viewer = QAction("Ползунок масштаба", self)
        for action in (self.layers_panel_viewer, self.tool_bar_viewer, self.scroller_viewer):
            action.setCheckable(True)
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
        self.start_window_view_button = QAction("Показывать окно приветствия при запуске", self)
        self.start_window_view_button.setCheckable(True)
        self.view_menu.addMenu(self.sub_windows)
        self.view_menu.addMenu(self.theme)
        self.view_menu.addMenu(self.langague)
        self.view_menu.addAction(self.start_window_view_button)

        self.layers_panel_viewer.toggled.connect(self._on_layer_panel_visibility_changed)
        self.tool_bar_viewer.toggled.connect(self._on_toolbar_visibility_changed)
        self.scroller_viewer.toggled.connect(self._on_zoom_visibility_changed)
        self.dark_theme.triggered.connect(lambda: self._set_theme("dark"))
        self.white_theme.triggered.connect(lambda: self._set_theme("light"))
        self.start_window_view_button.toggled.connect(self._on_welcome_preference_changed)

        self.tutorial_action = QAction("Обучение", self)
        self.about_action = QAction("О программе", self)
        self.help_menu.addAction(self.tutorial_action)
        self.help_menu.addAction(self.about_action)

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
        self.layer_panel.layers_reordered.connect(self._on_layers_reordered)
        self._layout_child_widgets()

        if project is not None:
            self.set_project(project)

        self.setWindowTitle("SQPaint")
        self.recent_projects_window = RecentProjectWindow()
        self.recent_projects_window.project_select.connect(self.open_project_path)
        self.recent_projects_window.create_project.connect(self.create_project)
        self.recent_projects_window.open_project.connect(self.open_project)
        self._apply_view_settings()
        self.show()
        if self.view_settings.get("show_welcome", True):
            self.recent_projects_window.show()

    def _layout_child_widgets(self) -> None:
        panel_width = LayerPanel.WIDTH if not self.layer_panel.isHidden() else 0
        top = self.HEADERS_HEIGHT + (ToolBar.HEIGHT if not self.tool_bar.isHidden() else 0)
        self.tool_bar.setGeometry(0, self.HEADERS_HEIGHT, self.width(), ToolBar.HEIGHT)
        self.canvas_view.setGeometry(
            0, top, max(0, self.width() - panel_width),
            max(0, self.height() - top)
        )
        self.layer_panel.setGeometry(
            self.width() - panel_width, 0, panel_width, self.height()
        )

        # Явно задаём порядок слоёв дочерних виджетов:
        # область холста находится снизу, панели инструментов и слоёв — сверху.
        self.canvas_view.lower()
        self.tool_bar.raise_()
        self.layer_panel.raise_()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._layout_child_widgets()


    def _apply_view_settings(self) -> None:
        """Применяет сохранённые параметры интерфейса при запуске."""
        actions = (
            (self.layers_panel_viewer, "layer_panel_visible"),
            (self.tool_bar_viewer, "toolbar_visible"),
            (self.scroller_viewer, "zoom_control_visible"),
            (self.start_window_view_button, "show_welcome"),
        )
        for action, key in actions:
            action.blockSignals(True)
            action.setChecked(self.view_settings.get(key, True))
            action.blockSignals(False)

        self.layer_panel.setVisible(self.layers_panel_viewer.isChecked())
        self.tool_bar.setVisible(self.tool_bar_viewer.isChecked())
        self.tool_bar.zoom_control.setVisible(self.scroller_viewer.isChecked())
        self.tool_bar.zoom_label.setVisible(self.scroller_viewer.isChecked())
        self._set_theme(self.view_settings.get("theme", "dark"), save=False)
        self._layout_child_widgets()

    def _save_view_settings(self) -> None:
        self.settings_data["view"] = self.view_settings
        try:
            settings_service.save_data(self.settings_data)
        except OSError as error:
            QMessageBox.warning(self, "Настройки", f"Не удалось сохранить настройки: {error}")

    def _on_layer_panel_visibility_changed(self, visible: bool) -> None:
        self.layer_panel.setVisible(visible)
        self.view_settings["layer_panel_visible"] = visible
        self._layout_child_widgets()
        self._save_view_settings()

    def _on_toolbar_visibility_changed(self, visible: bool) -> None:
        self.tool_bar.setVisible(visible)
        self.view_settings["toolbar_visible"] = visible
        self._layout_child_widgets()
        self._save_view_settings()

    def _on_zoom_visibility_changed(self, visible: bool) -> None:
        self.tool_bar.zoom_control.setVisible(visible)
        self.tool_bar.zoom_label.setVisible(visible)
        self.view_settings["zoom_control_visible"] = visible
        self._save_view_settings()

    def _on_welcome_preference_changed(self, visible: bool) -> None:
        self.view_settings["show_welcome"] = visible
        if hasattr(self, "recent_projects_window"):
            if visible:
                self.recent_projects_window.show()
            else:
                self.recent_projects_window.hide()
        self._save_view_settings()

    def _set_theme(self, theme: str, save: bool = True) -> None:
        if theme not in ("dark", "light"):
            theme = "dark"
        self.view_settings["theme"] = theme
        app = QApplication.instance()
        if app is not None:
            app.setStyle("Fusion")
            palette = QPalette()
            if theme == "dark":
                colors = {
                    QPalette.ColorRole.Window: "#242424",
                    QPalette.ColorRole.WindowText: "#eeeeee",
                    QPalette.ColorRole.Base: "#181818",
                    QPalette.ColorRole.AlternateBase: "#2b2b2b",
                    QPalette.ColorRole.Text: "#eeeeee",
                    QPalette.ColorRole.Button: "#353535",
                    QPalette.ColorRole.ButtonText: "#eeeeee",
                    QPalette.ColorRole.Highlight: "#42658c",
                    QPalette.ColorRole.HighlightedText: "#ffffff",
                }
            else:
                colors = {
                    QPalette.ColorRole.Window: "#eeeeee",
                    QPalette.ColorRole.WindowText: "#202020",
                    QPalette.ColorRole.Base: "#ffffff",
                    QPalette.ColorRole.AlternateBase: "#f2f2f2",
                    QPalette.ColorRole.Text: "#202020",
                    QPalette.ColorRole.Button: "#e2e2e2",
                    QPalette.ColorRole.ButtonText: "#202020",
                    QPalette.ColorRole.Highlight: "#3978bd",
                    QPalette.ColorRole.HighlightedText: "#ffffff",
                }
            for role, color in colors.items():
                palette.setColor(role, QColor(color))
            app.setPalette(palette)

        self.dark_theme.setCheckable(True)
        self.white_theme.setCheckable(True)
        self.dark_theme.setChecked(theme == "dark")
        self.white_theme.setChecked(theme == "light")
        if save:
            self._save_view_settings()

    def open_settings(self) -> None:
        """Открывает окно настроек с временной копией текущих значений."""
        dialog = SettingsDialog(self.settings_data, self)
        dialog.apply_requested.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self, values: dict) -> None:
        """Применяет и сохраняет настройки, переданные окном настроек."""
        view = values.get("view", {})
        self.view_settings.update(view)
        self._apply_view_settings()
        self._save_view_settings()

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
        # Сигнал панели должен быть подключён только к текущему Canvas.
        try:
            self.layer_panel.layer_change.disconnect()
        except TypeError:
            pass

        self.project = project
        self.canvas = Canvas(
            self.canvas_view, project.get_layers(),
            project.get_width(), project.get_height()
        )
        self.canvas.set_tool(Canvas.BRUSH)
        self.canvas_view.set_canvas(self.canvas)
        self.layer_panel.layer_change.connect(self.canvas.re_draw_canvas)
        self.layer_panel.set_layers(project.get_layers())
        self.canvas_view.set_zoom(100)
        self.save_action.setEnabled(True)
        self.save_as_action.setEnabled(True)
        self.export_submenu.setEnabled(True)
        self.import_action.setEnabled(True)
        self.file_info.setEnabled(True)
        self.canvas_size.setEnabled(True)
        self.setWindowTitle(f"SQPaint — {project.get_name()}")
        recent_projects.add_recent_project(project)

    def change_canvas_size(self) -> None:
        """Запрашивает новые размеры и изменяет все слои документа."""
        if self.project is None or self.canvas is None:
            return

        new_size = ask_canvas_size(
            self, self.project.get_width(), self.project.get_height()
        )
        if new_size is None:
            return

        width, height = new_size
        if (width, height) == (
            self.project.get_width(), self.project.get_height()
        ):
            return

        try:
            self.canvas.resize_document(width, height)
        except (MemoryError, ValueError, RuntimeError) as error:
            QMessageBox.critical(
                self, "Размер холста",
                f"Не удалось изменить размер холста.\\n\\n{error}"
            )
            return

        self.project.width = width
        self.project.height = height
        self.canvas_view.viewport().update()
        self.canvas_view.zoom_changed.emit(round(self.canvas_view.zoom * 100))

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

    def _on_layers_reordered(self) -> None:
        """Синхронизирует холст с новым порядком слоёв."""
        if self.project is None or self.canvas is None:
            return
        self.canvas.layers = self.project.get_layers()
        selected = self.layer_panel.selected_layer
        if selected in self.canvas.layers:
            self.canvas.active = self.canvas.layers.index(selected)
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
        self._save_view_settings()
        self.database.close()
        super().closeEvent(event)
