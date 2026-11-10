"""Создание меню и QAction главного окна."""
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QMenu

from ui.dialogs import show_about, show_tutorial


class MenuController:
    """Создаёт меню приложения и связывает действия с методами окна."""

    def __init__(self, window):
        self.window = window

    def build(self) -> None:
        w = self.window
        w.menu_bar = w.menuBar()
        w.file_menu = w.menu_bar.addMenu("Файл")
        w.edit_menu = w.menu_bar.addMenu("Правка")
        w.view_menu = w.menu_bar.addMenu("Вид")
        w.help_menu = w.menu_bar.addMenu("Справка")

        w.new_action = QAction("Создать", w)
        w.open_action = QAction("Открыть", w)
        w.save_action = QAction("Сохранить", w)
        w.save_as_action = QAction("Сохранить как", w)
        w.export_submenu = QMenu("Экспортировать", w)
        w.import_action = QAction("Импортировать", w)
        w.exit_action = QAction("Выход", w)
        w.file_info = QAction("О файле", w)
        w.export_png = w.export_submenu.addAction("PNG")
        w.export_jpg = w.export_submenu.addAction("JPG")

        for action in (w.new_action, w.open_action, w.save_action, w.save_as_action):
            w.file_menu.addAction(action)
        
        w.file_menu.addSeparator()
        w.file_menu.addMenu(w.export_submenu)
        w.file_menu.addAction(w.import_action)
        w.file_menu.addSeparator()
        w.file_menu.addAction(w.exit_action)
        w.file_menu.addSeparator()
        w.file_menu.addAction(w.file_info)

        w.new_action.triggered.connect(w.create_project)
        w.open_action.triggered.connect(w.open_project)
        w.save_action.triggered.connect(w.save)
        w.save_as_action.triggered.connect(w.save_as)
        w.import_action.triggered.connect(w.create_project_from_image)
        w.export_png.triggered.connect(lambda: w.export_image("png"))
        w.export_jpg.triggered.connect(lambda: w.export_image("jpg"))
        w.exit_action.triggered.connect(w.close)
        w.file_info.triggered.connect(w.open_file_info)
        w.save_action.setEnabled(False)
        w.save_as_action.setEnabled(False)
        w.export_submenu.setEnabled(False)
        w.import_action.setEnabled(True)
        w.file_info.setEnabled(False)

        w.canvas_size = QAction("Размер холста", w)
        w.paste_as_layer_action = QAction("Вставить как слой", w)
        w.selfie_action = QAction("Сделать селфи", w)
        w.settings_action = QAction("Настройки", w)
        w.undo_action = QAction("Отменить", w)
        w.undo_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Undo))
        w.redo_action = QAction("Повторить", w)
        w.redo_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Redo))
        w.edit_menu.addAction(w.undo_action)
        w.edit_menu.addAction(w.redo_action)
        w.edit_menu.addSeparator()
        w.undo_action.setEnabled(False)
        w.redo_action.setEnabled(False)
        w.edit_menu.addAction(w.canvas_size)
        w.edit_menu.addAction(w.paste_as_layer_action)
        w.edit_menu.addAction(w.selfie_action)
        w.edit_menu.addAction(w.settings_action)
        w.canvas_size.triggered.connect(w.change_canvas_size)
        w.canvas_size.setEnabled(False)
        w.paste_as_layer_action.triggered.connect(w.import_image)
        w.selfie_action.triggered.connect(w.take_selfie)
        w.selfie_action.setEnabled(False)
        w.settings_action.triggered.connect(w.open_settings)

        w.sub_windows = QMenu("Окна", w)
        w.layers_panel_viewer = QAction("Панель слоёв", w)
        w.tool_bar_viewer = QAction("Панель инструментов", w)
        w.scroller_viewer = QAction("Ползунок масштаба", w)
        for action in (w.layers_panel_viewer, w.tool_bar_viewer, w.scroller_viewer):
            action.setCheckable(True)
        w.sub_windows.addAction(w.layers_panel_viewer)
        w.sub_windows.addAction(w.tool_bar_viewer)
        w.sub_windows.addAction(w.scroller_viewer)

        w.theme = QMenu("Тема", w)
        w.dark_theme = QAction("Тёмная тема", w)
        w.white_theme = QAction("Светлая тема", w)
        w.theme.addAction(w.dark_theme)
        w.theme.addAction(w.white_theme)

        w.langague = QMenu("Язык", w)
        w.ru = QAction("Русский", w)
        w.en = QAction("English", w)
        w.ru.setCheckable(True)
        w.en.setCheckable(True)
        w.langague.addAction(w.ru)
        w.langague.addAction(w.en)
        w.ru.triggered.connect(lambda checked=False: w._set_language("ru"))
        w.en.triggered.connect(lambda checked=False: w._set_language("en"))
        w.start_window_view_button = QAction("Показывать окно приветствия при запуске", w)
        w.start_window_view_button.setCheckable(True)
        w.view_menu.addMenu(w.sub_windows)
        w.view_menu.addMenu(w.theme)
        w.view_menu.addMenu(w.langague)
        w.view_menu.addAction(w.start_window_view_button)

        w.layers_panel_viewer.toggled.connect(w._on_layer_panel_visibility_changed)
        w.tool_bar_viewer.toggled.connect(w._on_toolbar_visibility_changed)
        w.scroller_viewer.toggled.connect(w._on_zoom_visibility_changed)
        w.dark_theme.triggered.connect(lambda: w._set_theme("dark"))
        w.white_theme.triggered.connect(lambda: w._set_theme("light"))
        w.start_window_view_button.toggled.connect(w._on_welcome_preference_changed)

        w.tutorial_action = QAction("Обучение", w)
        w.about_action = QAction("О программе", w)
        w.help_menu.addAction(w.tutorial_action)
        w.help_menu.addAction(w.about_action)
        w.tutorial_action.triggered.connect(lambda: show_tutorial(w))
        w.about_action.triggered.connect(lambda: show_about(w))

