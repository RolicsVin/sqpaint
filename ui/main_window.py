import os
import sqlite3

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QImage
from PyQt6.QtWidgets import QApplication, QDialog, QMainWindow, QMenu, QMessageBox

from core.database import ProjectDatabase
from core.models import Project
from core import image_utils
from services import recent_projects, settings as settings_service
from ui.start_window import RecentProjectWindow
from ui.canvas import Canvas
from ui.canvas_view import CanvasView
from ui.tool_bar import ToolBar
from ui.layers_panel import LayerPanel
from ui.view_manager import ViewManager
from ui.selfie_dialog import SelfieDialog
from ui.dialogs import *


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
        self.import_action.triggered.connect(self.create_project_from_image)
        self.export_png.triggered.connect(lambda: self.export_image("png"))
        self.export_jpg.triggered.connect(lambda: self.export_image("jpg"))
        self.exit_action.triggered.connect(self.close)
        self.file_info.triggered.connect(self.open_file_info)
        self.save_action.setEnabled(False)
        self.save_as_action.setEnabled(False)
        self.export_submenu.setEnabled(False)
        self.import_action.setEnabled(True)
        self.file_info.setEnabled(False)

        self.canvas_size = QAction("Размер холста", self)
        self.paste_as_layer_action = QAction("Вставить как слой", self)
        self.selfie_action = QAction("Сделать селфи", self)
        self.settings_action = QAction("Настройки", self)
        self.edit_menu.addAction(self.canvas_size)
        self.edit_menu.addAction(self.paste_as_layer_action)
        self.edit_menu.addAction(self.selfie_action)
        self.edit_menu.addAction(self.settings_action)
        self.canvas_size.triggered.connect(self.change_canvas_size)
        self.canvas_size.setEnabled(False)
        self.paste_as_layer_action.triggered.connect(self.import_image)
        self.selfie_action.triggered.connect(self.take_selfie)
        self.selfie_action.setEnabled(False)
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
        self.about_action.triggered.connect(lambda: show_about(self))

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
        self.layer_panel.layer_move_requested.connect(self._on_layer_move_requested)
        self.layer_panel.layer_visibility_requested.connect(
            self._on_layer_visibility_requested
        )
        self.layer_panel.layer_rename_requested.connect(
            self._on_layer_rename_requested
        )
        self._layout_child_widgets()

        if project is not None:
            self.set_project(project)

        self.setWindowTitle("SQPaint")
        self.recent_projects_window = RecentProjectWindow()
        self.recent_projects_window.project_select.connect(self.open_project_path)
        self.recent_projects_window.create_project.connect(self.create_project)
        self.recent_projects_window.open_project.connect(self.open_project)
        self.view_manager = ViewManager(
            self.view_settings,
            self.layer_panel,
            self.tool_bar,
            self._layout_child_widgets,
            self.layers_panel_viewer,
            self.tool_bar_viewer,
            self.scroller_viewer,
            self.start_window_view_button,
            self.dark_theme,
            self.white_theme,
            self.recent_projects_window,
        )
        self.view_manager.apply()
        self.show()

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


    def _save_view_settings(self) -> None:
        """Сохраняет уже подготовленные UI-настройки через файловый сервис."""
        self.settings_data["view"] = self.view_settings
        try:
            settings_service.save_data(self.settings_data)
        except OSError as error:
            QMessageBox.warning(
                self, "Настройки",
                f"Не удалось сохранить настройки: {error}"
            )

    def _on_layer_panel_visibility_changed(self, visible: bool) -> None:
        self.view_manager.set_layer_panel_visible(visible)
        self._save_view_settings()

    def _on_toolbar_visibility_changed(self, visible: bool) -> None:
        self.view_manager.set_toolbar_visible(visible)
        self._save_view_settings()

    def _on_zoom_visibility_changed(self, visible: bool) -> None:
        self.view_manager.set_zoom_visible(visible)
        self._save_view_settings()

    def _on_welcome_preference_changed(self, visible: bool) -> None:
        self.view_manager.set_welcome_visible(visible)
        self._save_view_settings()

    def _set_theme(self, theme: str, save: bool = True) -> None:
        self.view_manager.set_theme(theme)
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
        self.view_manager.apply(view)
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

        try:
            project = self.database.create(path, name, width, height)
            project.create_layer(fill=0xFFFFFFFF)
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
        self.canvas.crop_requested.connect(self.crop_document)
        self.canvas_view.set_canvas(self.canvas)
        self.canvas.set_layers(project.get_layers(), active=0)
        self.layer_panel.set_layers(project.get_layers())
        self.canvas_view.set_zoom(100)
        self.save_action.setEnabled(True)
        self.save_as_action.setEnabled(True)
        self.export_submenu.setEnabled(True)
        self.import_action.setEnabled(True)
        self.selfie_action.setEnabled(True)
        self.file_info.setEnabled(True)
        self.canvas_size.setEnabled(True)
        self.setWindowTitle(f"SQPaint — {project.get_name()}")
        recent_projects.add_recent_project(project)

    def crop_document(self, rect) -> None:
        """Применяет выбранную область кадрирования ко всему документу."""
        if self.project is None or self.canvas is None:
            return
        self._commit_pending_transform()
        try:
            self.project.crop(rect.x(), rect.y(), rect.width(), rect.height())
            self.canvas.set_document_size(rect.width(), rect.height())
            self.canvas.update()
            self.canvas_view.viewport().update()
        except (ValueError, MemoryError, RuntimeError) as error:
            QMessageBox.warning(
                self, "Кадрирование",
                f"Не удалось кадрировать холст:\n{error}"
            )

    def change_canvas_size(self) -> None:
        if self.project is None or self.canvas is None:
            return

        new_size = ask_canvas_size(
            self, self.project.get_width(), self.project.get_height()
        )
        if new_size is None:
            return

        width, height = new_size
        if (width, height) == (self.project.get_width(), self.project.get_height()):
            return

        try:
            self.project.resize(width, height)
            self.canvas.set_document_size(width, height)
        except (MemoryError, ValueError, RuntimeError) as error:
            QMessageBox.critical(
                self, "Размер холста",
                f"Не удалось изменить размер холста.\\n\\n{error}"
            )
            return

        self.canvas_view.viewport().update()
        self.canvas_view.zoom_changed.emit(round(self.canvas_view.zoom * 100))

    def add_layer(self) -> None:
        if self.project is None or self.canvas is None:
            return

        layer = self.project.create_layer()
        active_index = self.project.get_layers().index(layer)
        self.canvas.set_layers(self.project.get_layers(), active=active_index)
        self.layer_panel.set_layers(self.project.get_layers())
        self.layer_panel.select_layer(active_index)

    def remove_layer(self, layer) -> None:
        if self.project is None or self.canvas is None:
            return
        if layer not in self.project.get_layers():
            return
        if len(self.project.get_layers()) <= 1:
            show_last_layer_info(self)
            return
        if not confirm_delete_layer(self, layer.get_name()):
            return

        old_index = self.project.get_layers().index(layer)
        if not self.project.remove_layer(layer):
            return

        active_index = min(old_index, len(self.project.get_layers()) - 1)
        self.canvas.set_layers(self.project.get_layers(), active=active_index)
        self.layer_panel.set_layers(self.project.get_layers())
        self.layer_panel.select_layer(active_index)

    def _on_layer_move_requested(self, source, target, insert_before: bool) -> None:
        if self.project is None or self.canvas is None:
            return
        if not self.project.move_layer(source, target, insert_before):
            return

        selected = self.layer_panel.selected_layer
        active_index = (
            self.project.get_layers().index(selected)
            if selected in self.project.get_layers()
            else 0
        )
        self.canvas.set_layers(self.project.get_layers(), active=active_index)
        self.layer_panel.set_layers(self.project.get_layers())
        self.layer_panel.select_layer(active_index)

    def _on_layer_visibility_requested(self, layer, visible: bool) -> None:
        if self.project is None or self.canvas is None:
            return
        if self.project.set_layer_visibility(layer, visible):
            self.canvas.update()

    def _on_layer_rename_requested(self, layer, name: str) -> None:
        if self.project is None:
            return
        self.project.rename_layer(layer, name)
        self.layer_panel.refresh_layer_name(layer)

    def _commit_pending_transform(self) -> None:
        if self.canvas is not None and self.canvas.transform_image is not None:
            self.canvas.commit_image_transform()

    def select_layer(self, index: int) -> None:
        self._commit_pending_transform()
        if self.canvas is not None:
            self.canvas.set_active_layer(index)

    def save(self) -> None:
        if self.project is None:
            return
        self._commit_pending_transform()
        try:
            self.database.save(self.project)
        except (OSError, sqlite3.Error, RuntimeError) as error:
            show_save_error(self, error)

    def set_canvas_color(self, color) -> None:
        if self.canvas is not None:
            self.canvas.color = color

    def set_canvas_tool(self, tool_name: str) -> None:
        if self.canvas is not None:
            self._commit_pending_transform()
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
        self._commit_pending_transform()
        path = ask_save_as_path(self, self.project.get_name())
        if not path:
            return
        if os.path.exists(path):
            show_file_exists(self)
            return
        try:
            project = self.database.save_as(path, self.project)
            self.set_project(project)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
            show_save_error(self, error)

    def import_image(self) -> None:
        """Добавляет выбранное изображение в открытый проект отдельным слоем."""
        if self.project is None or self.canvas is None:
            return
        path = ask_import_image_path(self)
        if not path:
            return

        image = QImage(path)
        if image.isNull():
            QMessageBox.warning(
                self, "Вставить как слой",
                "Не удалось открыть выбранное изображение."
            )
            return

        # Создаём пустой слой, а изображение пока показываем в режиме
        # трансформации. Пользователь сможет переместить его и изменить размер.
        layer = self.project.create_layer("Импорт")
        active_index = self.project.get_layers().index(layer)
        self.canvas.set_layers(self.project.get_layers(), active=active_index)
        self.layer_panel.set_layers(self.project.get_layers())
        self.layer_panel.select_layer(active_index)
        self.canvas.begin_image_transform(image)

    def create_project_from_image(self) -> None:
        """Создаёт новый SQLite-проект, используя изображение как первый слой."""
        image_path = ask_import_image_path(self)
        if not image_path:
            return

        image = QImage(image_path)
        if image.isNull():
            QMessageBox.warning(
                self, "Импорт изображения",
                "Не удалось открыть выбранное изображение."
            )
            return

        project_name = os.path.splitext(os.path.basename(image_path))[0] or "Импорт"
        project_path = ask_save_project_path(self, project_name)
        if not project_path:
            return
        if os.path.exists(project_path):
            show_file_exists(self)
            return

        try:
            project = self.database.create(
                project_path, project_name, image.width(), image.height()
            )
            project.create_layer("Импорт", image)
            self.database.save(project)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
            show_create_error(self, error)
            return

        self.set_project(project)

    def take_selfie(self) -> None:
        """Снимает изображение с веб-камеры и добавляет его отдельным слоем."""
        if self.project is None or self.canvas is None:
            return

        try:
            dialog = SelfieDialog(self)
        except Exception as error:
            QMessageBox.warning(
                self, "Веб-камера",
                f"Не удалось запустить камеру. Проверьте подключение и разрешения.\n\n{error}"
            )
            return

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        image = dialog.get_image()
        if image is None or image.isNull():
            return

        layer = self.project.create_layer("Селфи", image)
        active_index = self.project.get_layers().index(layer)
        self.canvas.set_layers(self.project.get_layers(), active=active_index)
        self.layer_panel.set_layers(self.project.get_layers())
        self.layer_panel.select_layer(active_index)

    def export_image(self, image_format: str) -> None:
        if self.canvas is None:
            return
        self._commit_pending_transform()
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
