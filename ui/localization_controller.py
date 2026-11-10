"""Локализация меню и действий главного окна."""
from services import settings as settings_service


class WindowLocalizationController:
    """Регистрирует переводы главного окна и сохраняет выбранный язык."""

    def __init__(self, window):
        self.window = window

    def register_widgets(self) -> None:
        entries = [
            (self.file_menu, {"ru": "Файл", "en": "File"}),
            (self.file_menu.menuAction(), {"ru": "Файл", "en": "File"}),
            (self.edit_menu, {"ru": "Правка", "en": "Edit"}),
            (self.edit_menu.menuAction(), {"ru": "Правка", "en": "Edit"}),
            (self.view_menu, {"ru": "Вид", "en": "View"}),
            (self.view_menu.menuAction(), {"ru": "Вид", "en": "View"}),
            (self.help_menu, {"ru": "Справка", "en": "Help"}),
            (self.help_menu.menuAction(), {"ru": "Справка", "en": "Help"}),
            (self.export_submenu, {"ru": "Экспортировать", "en": "Export"}),
            (self.export_submenu.menuAction(), {"ru": "Экспортировать", "en": "Export"}),
            (self.sub_windows, {"ru": "Окна", "en": "Panels"}),
            (self.sub_windows.menuAction(), {"ru": "Окна", "en": "Panels"}),
            (self.theme, {"ru": "Тема", "en": "Theme"}),
            (self.theme.menuAction(), {"ru": "Тема", "en": "Theme"}),
            (self.langague, {"ru": "Язык", "en": "Language"}),
            (self.langague.menuAction(), {"ru": "Язык", "en": "Language"}),
            (self.new_action, {"ru": "Создать", "en": "New"}),
            (self.open_action, {"ru": "Открыть", "en": "Open"}),
            (self.save_action, {"ru": "Сохранить", "en": "Save"}),
            (self.save_as_action, {"ru": "Сохранить как", "en": "Save as"}),
            (self.import_action, {"ru": "Импортировать", "en": "Import"}),
            (self.exit_action, {"ru": "Выход", "en": "Exit"}),
            (self.file_info, {"ru": "О файле", "en": "File information"}),
            (self.canvas_size, {"ru": "Размер холста", "en": "Canvas size"}),
            (self.paste_as_layer_action, {"ru": "Вставить как слой", "en": "Paste as layer"}),
            (self.selfie_action, {"ru": "Сделать селфи", "en": "Take a selfie"}),
            (self.settings_action, {"ru": "Настройки", "en": "Settings"}),
            (self.layers_panel_viewer, {"ru": "Панель слоёв", "en": "Layers panel"}),
            (self.tool_bar_viewer, {"ru": "Панель инструментов", "en": "Tools panel"}),
            (self.scroller_viewer, {"ru": "Ползунок масштаба", "en": "Zoom control"}),
            (self.dark_theme, {"ru": "Тёмная тема", "en": "Dark theme"}),
            (self.white_theme, {"ru": "Светлая тема", "en": "Light theme"}),
            (self.start_window_view_button, {"ru": "Показывать окно приветствия при запуске", "en": "Show welcome window on startup"}),
            (self.tutorial_action, {"ru": "Обучение", "en": "Tutorial"}),
            (self.about_action, {"ru": "О программе", "en": "About"}),
            (self.export_png, {"ru": "PNG", "en": "PNG"}),
            (self.export_jpg, {"ru": "JPG", "en": "JPG"}),
        ]
        for widget, translations in entries:
            self.localization.register(widget, translations)
        self.localization.register(self.tool_bar, {})

    def translate(self, ru: str, en: str) -> str:
        return en if self.window.localization.language == "en" else ru

    def set_language(self, language: str) -> None:
        w = self.window
        w.localization.set_language(language)
        w.ru.setChecked(language == "ru")
        w.en.setChecked(language == "en")
        w.settings_data["language"] = language
        settings_service.save_data(w.settings_data)
