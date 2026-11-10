"""Локализация меню и действий главного окна."""
from services import settings as settings_service


class WindowLocalizationController:
    """Регистрирует переводы главного окна и сохраняет выбранный язык."""

    def __init__(self, window):
        self.window = window

    def register_widgets(self) -> None:
        w = self.window
        entries = [
            (w.file_menu, {"ru": "Файл", "en": "File"}),
            (w.file_menu.menuAction(), {"ru": "Файл", "en": "File"}),
            (w.edit_menu, {"ru": "Правка", "en": "Edit"}),
            (w.edit_menu.menuAction(), {"ru": "Правка", "en": "Edit"}),
            (w.view_menu, {"ru": "Вид", "en": "View"}),
            (w.view_menu.menuAction(), {"ru": "Вид", "en": "View"}),
            (w.help_menu, {"ru": "Справка", "en": "Help"}),
            (w.help_menu.menuAction(), {"ru": "Справка", "en": "Help"}),
            (w.export_submenu, {"ru": "Экспортировать", "en": "Export"}),
            (w.export_submenu.menuAction(), {"ru": "Экспортировать", "en": "Export"}),
            (w.sub_windows, {"ru": "Окна", "en": "Panels"}),
            (w.sub_windows.menuAction(), {"ru": "Окна", "en": "Panels"}),
            (w.theme, {"ru": "Тема", "en": "Theme"}),
            (w.theme.menuAction(), {"ru": "Тема", "en": "Theme"}),
            (w.langague, {"ru": "Язык", "en": "Language"}),
            (w.langague.menuAction(), {"ru": "Язык", "en": "Language"}),
            (w.new_action, {"ru": "Создать", "en": "New"}),
            (w.open_action, {"ru": "Открыть", "en": "Open"}),
            (w.save_action, {"ru": "Сохранить", "en": "Save"}),
            (w.save_as_action, {"ru": "Сохранить как", "en": "Save as"}),
            (w.import_action, {"ru": "Импортировать", "en": "Import"}),
            (w.exit_action, {"ru": "Выход", "en": "Exit"}),
            (w.file_info, {"ru": "О файле", "en": "File information"}),
            (w.undo_action, {"ru": "Отменить", "en": "Undo"}),
            (w.redo_action, {"ru": "Повторить", "en": "Redo"}),
            (w.canvas_size, {"ru": "Размер холста", "en": "Canvas size"}),
            (w.paste_as_layer_action, {"ru": "Вставить как слой", "en": "Paste as layer"}),
            (w.selfie_action, {"ru": "Сделать селфи", "en": "Take a selfie"}),
            (w.settings_action, {"ru": "Настройки", "en": "Settings"}),
            (w.layers_panel_viewer, {"ru": "Панель слоёв", "en": "Layers panel"}),
            (w.tool_bar_viewer, {"ru": "Панель инструментов", "en": "Tools panel"}),
            (w.scroller_viewer, {"ru": "Ползунок масштаба", "en": "Zoom control"}),
            (w.dark_theme, {"ru": "Тёмная тема", "en": "Dark theme"}),
            (w.white_theme, {"ru": "Светлая тема", "en": "Light theme"}),
            (w.start_window_view_button, {"ru": "Показывать окно приветствия при запуске", "en": "Show welcome window on startup"}),
            (w.tutorial_action, {"ru": "Обучение", "en": "Tutorial"}),
            (w.about_action, {"ru": "О программе", "en": "About"}),
            (w.export_png, {"ru": "PNG", "en": "PNG"}),
            (w.export_jpg, {"ru": "JPG", "en": "JPG"}),
        ]
        for widget, translations in entries:
            w.localization.register(widget, translations)
        w.localization.register(w.tool_bar, {})

    def translate(self, ru: str, en: str) -> str:
        return en if self.window.localization.language == "en" else ru

    def set_language(self, language: str) -> None:
        w = self.window
        w.localization.set_language(language)
        w.ru.setChecked(language == "ru")
        w.en.setChecked(language == "en")
        w.settings_data["language"] = language
        settings_service.save_data(w.settings_data)
