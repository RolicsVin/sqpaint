"""Контроллер пользовательских настроек и визуального состояния окна."""
from PyQt6.QtWidgets import QMessageBox

from services import settings as settings_service
from ui.dialogs import SettingsDialog


class PreferencesController:
    """Связывает настройки приложения с ViewManager и хранилищем JSON."""

    def __init__(self, window):
        self.window = window

    def save(self) -> None:
        w = self.window
        w.settings_data["view"] = w.view_settings
        try:
            settings_service.save_data(w.settings_data)
        except OSError as error:
            QMessageBox.warning(
                w, w._tr("Настройки", "Settings"),
                w._tr(
                    f"Не удалось сохранить настройки: {error}",
                    f"Could not save settings: {error}",
                ),
            )

    def layer_panel_visibility_changed(self, visible: bool) -> None:
        self.window.view_manager.set_layer_panel_visible(visible)
        self.save()

    def toolbar_visibility_changed(self, visible: bool) -> None:
        self.window.view_manager.set_toolbar_visible(visible)
        self.save()

    def zoom_visibility_changed(self, visible: bool) -> None:
        self.window.view_manager.set_zoom_visible(visible)
        self.save()

    def welcome_preference_changed(self, visible: bool) -> None:
        self.window.view_manager.set_welcome_visible(visible)
        self.save()

    def set_theme(self, theme: str, save: bool = True) -> None:
        self.window.view_manager.set_theme(theme)
        if save:
            self.save()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.window.settings_data, self.window)
        dialog.apply_requested.connect(self.apply_settings)
        dialog.exec()

    def apply_settings(self, values: dict) -> None:
        view = values.get("view", {})

        # show_welcome — настройка следующего запуска. Обновляем её
        # значение и QAction, но не показываем стартовое окно сейчас.
        self.window.view_settings.update(view)
        runtime_view = {
            key: value for key, value in view.items()
            if key != "show_welcome"
        }
        self.window.view_manager.apply(runtime_view, apply_welcome=False)

        project_values = values.get("project")
        project = self.window.project
        if project is not None and isinstance(project_values, dict):
            before = self.window.history_controller.begin()
            project.supports_transparency = bool(
                project_values.get("supports_transparency", project.supports_transparency)
            )
            project.max_undo_steps = max(
                1, int(project_values.get("max_undo_steps", project.max_undo_steps))
            )
            self.window.history_controller.set_limit(project.max_undo_steps)
            self.window.history_controller.commit(before, "ChangeProjectSettings")
            if self.window.canvas is not None:
                self.window.canvas.supports_transparency = project.supports_transparency
                self.window.canvas.update()
            self.window.history_controller._refresh_title()
        self.save()
