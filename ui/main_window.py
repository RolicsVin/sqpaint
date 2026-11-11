from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow

from core.database import ProjectDatabase
from services.logger import AppLogger
from core.models import Project
from core.localization import LocalizationManager
from services import recent_projects, settings as settings_service
from ui.start_window import RecentProjectWindow
from ui.canvas import Canvas
from ui.canvas_view import CanvasView
from ui.tool_bar import ToolBar
from ui.layers_panel import LayerPanel
from ui.view_manager import ViewManager
from ui.document_controller import DocumentController
from ui.localization_controller import WindowLocalizationController
from ui.preferences_controller import PreferencesController
from ui.menu_controller import MenuController
from ui.history_controller import HistoryController
from ui.autosave_controller import AutoSaveController
from ui.dialogs import confirm_exit


class DomainWindow(QMainWindow):
    HEADERS_HEIGHT = 25

    def __init__(self, project: Project | None, database: ProjectDatabase, settings: dict):
        super().__init__()
        self.project = None
        self.database = database
        self.logger = AppLogger(database)
        self.settings_data = settings if isinstance(settings, dict) else settings_service.load_data()
        self.view_settings = self.settings_data.setdefault("view", {})
        self.canvas: Canvas | None = None
        self.canvas_view: CanvasView | None = None

        screen = QApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.availableGeometry())

        self.menu_controller = MenuController(self)
        self.menu_controller.build()
        self.history_controller = HistoryController(self)
        self.autosave_controller = AutoSaveController(self)

        self.tool_bar = ToolBar(self)
        saved_language = self.settings_data.get("language", "ru")
        self.localization = LocalizationManager(
            saved_language if saved_language in LocalizationManager.SUPPORTED_LANGUAGES else "ru"
        )
        self.localization_controller = WindowLocalizationController(self)
        self.localization_controller.register_widgets()
        self.tool_bar.set_language(self.localization.language)
        self.ru.setChecked(self.localization.language == "ru")
        self.en.setChecked(self.localization.language == "en")
        self.tool_bar.move(0, self.HEADERS_HEIGHT)
        self.tool_bar.resize(self.width(), ToolBar.HEIGHT)
        self.tool_bar.color_selected.connect(self.set_canvas_color)
        self.tool_bar.tool_selected.connect(self.set_canvas_tool)
        self.tool_bar.shape_selected.connect(self.set_canvas_shape)
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
        self.recent_projects_window = RecentProjectWindow(self.localization, self)
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
        self.document_controller = DocumentController(self)
        self.preferences_controller = PreferencesController(self)

        # Повторно применяем язык после полной сборки интерфейса:
        # QMenu отображается через menuAction(), поэтому синхронизируем и его текст.
        self._set_language(self.localization.language)
        self.ru.setChecked(self.localization.language == "ru")
        self.en.setChecked(self.localization.language == "en")
        self.showMaximized()
        # Стартовое окно должно оставаться поверх главного при запуске.
        if self.recent_projects_window.isVisible():
            self.recent_projects_window.raise_()
            self.recent_projects_window.activateWindow()


    def _tr(self, ru: str, en: str) -> str:
        return self.localization_controller.translate(ru, en)

    def _set_language(self, language: str) -> None:
        self.localization_controller.set_language(language)
        self.tool_bar.set_language(language)

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
        self.preferences_controller.save()

    def _on_layer_panel_visibility_changed(self, visible: bool) -> None:
        self.preferences_controller.layer_panel_visibility_changed(visible)

    def _on_toolbar_visibility_changed(self, visible: bool) -> None:
        self.preferences_controller.toolbar_visibility_changed(visible)

    def _on_zoom_visibility_changed(self, visible: bool) -> None:
        self.preferences_controller.zoom_visibility_changed(visible)

    def _on_welcome_preference_changed(self, visible: bool) -> None:
        self.preferences_controller.welcome_preference_changed(visible)

    def _set_theme(self, theme: str, save: bool = True) -> None:
        self.preferences_controller.set_theme(theme, save)

    def open_settings(self) -> None:
        self.preferences_controller.open_settings()

    def _apply_settings(self, values: dict) -> None:
        self.preferences_controller.apply_settings(values)

    def create_project(self) -> None:
        self.document_controller.create_project()

    def open_project(self) -> None:
        self.document_controller.open_project()

    def open_project_path(self, path: str) -> None:
        self.document_controller.open_project_path(path)

    def set_project(self, project: Project) -> None:
        self.project = project
        self.autosave_controller.start()
        self.logger.log("Проект открыт", project.get_name())
        self.canvas = Canvas(
            self.canvas_view, project.get_layers(),
            project.get_width(), project.get_height(),
            project.supports_transparency,
        )
        self.canvas.set_tool(Canvas.BRUSH)
        self.canvas.crop_requested.connect(self.crop_document)
        self.canvas_view.set_canvas(self.canvas)
        self.canvas.set_layers(project.get_layers(), active=0)
        self.layer_panel.set_layers(project.get_layers())
        self.canvas_view.set_zoom(100)
        self.history_controller.set_project(project)
        self.save_action.setEnabled(True)
        self.save_as_action.setEnabled(True)
        self.export_submenu.setEnabled(True)
        self.import_action.setEnabled(True)
        self.selfie_action.setEnabled(True)
        self.file_info.setEnabled(True)
        self.canvas_size.setEnabled(True)
        self.setWindowTitle(f"SQPaint — {project.get_name()}")
        recent_projects.add_recent_project(project)

    # Document and layer workflows are delegated to DocumentController.
    def crop_document(self, rect) -> None:
        self.document_controller.crop_document(rect)

    def change_canvas_size(self) -> None:
        self.document_controller.change_canvas_size()

    def add_layer(self) -> None:
        self.document_controller.add_layer()

    def remove_layer(self, layer) -> None:
        self.document_controller.remove_layer(layer)

    def _on_layer_move_requested(self, source, target, insert_before: bool) -> None:
        self.document_controller.move_layer(source, target, insert_before)

    def _on_layer_visibility_requested(self, layer, visible: bool) -> None:
        self.document_controller.set_layer_visibility(layer, visible)

    def _on_layer_rename_requested(self, layer, name: str) -> None:
        self.document_controller.rename_layer(layer, name)

    def _commit_pending_transform(self) -> None:
        if self.canvas is not None and self.canvas.transform_image is not None:
            self.canvas.commit_image_transform()

    def select_layer(self, index: int) -> None:
        self.document_controller.select_layer(index)

    def save(self) -> None:
        self.document_controller.save()

    def set_canvas_color(self, color) -> None:
        if self.canvas is not None:
            self.canvas.color = color
            self.logger.log("Выбран цвет", color.name())

    def set_canvas_tool(self, tool_name: str) -> None:
        if self.canvas is not None:
            self._commit_pending_transform()
            self.canvas.set_tool(tool_name)
            self.logger.log("Выбран инструмент", tool_name)

    def set_canvas_shape(self, shape_name: str) -> None:
        if self.canvas is not None:
            self.canvas.set_shape(shape_name)
            self.logger.log("Выбрана фигура", shape_name)

    def set_canvas_width(self, width: int) -> None:
        if self.canvas is not None:
            self.canvas.width_px = width

    def set_canvas_zoom(self, percent: int) -> None:
        if self.canvas_view is not None:
            self.canvas_view.set_zoom(percent)

    def save_as(self) -> None:
        self.document_controller.save_as()

    def import_image(self) -> None:
        self.document_controller.import_image()

    def create_project_from_image(self) -> None:
        self.document_controller.create_project_from_image()

    def take_selfie(self) -> None:
        self.document_controller.take_selfie()

    def export_image(self, image_format: str) -> None:
        self.document_controller.export_image(image_format)

    def open_file_info(self) -> None:
        self.document_controller.open_file_info()

    def closeEvent(self, event) -> None:
        self._commit_pending_transform()
        self.history_controller.flush_pending()
        has_unsaved_changes = (
            self.history_controller.is_dirty() if self.project is not None else False
        )
        if not confirm_exit(self, has_unsaved_changes):
            event.ignore()
            return

        self.autosave_controller.stop()
        if self.project is not None:
            self.logger.log("Проект закрывается", self.project.get_name())
        self._save_view_settings()
        # Явно закрываем отдельное стартовое окно при закрытии главного.
        self.recent_projects_window.close()
        self.database.close()
        event.accept()
        super().closeEvent(event)
