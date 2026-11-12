"""Управление визуальным состоянием главного окна SQPaint.

Модуль работает с Qt-виджетами, но не читает и не сохраняет настройки на диске.
Хранение настроек остаётся ответственностью services.settings.
"""
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


class ViewManager:
    """Применяет параметры отображения к переданным компонентам интерфейса."""

    def __init__(
        self,
        settings: dict,
        layer_panel,
        tool_bar,
        layout_callback,
        layer_panel_action,
        toolbar_action,
        zoom_action,
        welcome_action,
        dark_theme_action,
        light_theme_action,
        recent_window=None,
    ):
        """Сохраняет ссылки на виджеты и действия, которыми управляет менеджер."""
        self.settings = settings
        self.layer_panel = layer_panel
        self.tool_bar = tool_bar
        self.layout_callback = layout_callback
        self.layer_panel_action = layer_panel_action
        self.toolbar_action = toolbar_action
        self.zoom_action = zoom_action
        self.welcome_action = welcome_action
        self.dark_theme_action = dark_theme_action
        self.light_theme_action = light_theme_action
        self.recent_window = recent_window

        self.dark_theme_action.setCheckable(True)
        self.light_theme_action.setCheckable(True)

    def apply(
        self,
        values: dict | None = None,
        apply_welcome: bool = True,
    ) -> None:
        """Применяет настройки видимости элементов и тему оформления.

        При apply_welcome=False обновляется состояние QAction, но видимость
        стартового окна не меняется. Это позволяет отложить настройку до запуска.
        """
        if values is not None:
            self.settings.update(values)

        self._set_action_checked(
            self.layer_panel_action,
            self.settings.get("layer_panel_visible", True),
        )
        self._set_action_checked(
            self.toolbar_action,
            self.settings.get("toolbar_visible", True),
        )
        self._set_action_checked(
            self.zoom_action,
            self.settings.get("zoom_control_visible", True),
        )
        self._set_action_checked(
            self.welcome_action,
            self.settings.get("show_welcome", True),
        )

        self.layer_panel.setVisible(self.layer_panel_action.isChecked())
        self.tool_bar.setVisible(self.toolbar_action.isChecked())
        self._set_zoom_visible(self.zoom_action.isChecked())

        if apply_welcome:
            self._set_welcome_visible(self.welcome_action.isChecked())

        self._set_theme(self.settings.get("theme", "dark"))
        self.layout_callback()

    @staticmethod
    def _set_action_checked(action, checked: bool) -> None:
        """Меняет состояние QAction без вызова подключённых обработчиков."""
        action.blockSignals(True)
        action.setChecked(bool(checked))
        action.blockSignals(False)

    def set_layer_panel_visible(self, visible: bool) -> None:
        """Изменяет видимость панели слоёв и перестраивает компоновку."""
        self.settings["layer_panel_visible"] = bool(visible)
        self.layer_panel.setVisible(bool(visible))
        self.layout_callback()

    def set_toolbar_visible(self, visible: bool) -> None:
        """Изменяет видимость панели инструментов и перестраивает компоновку."""
        self.settings["toolbar_visible"] = bool(visible)
        self.tool_bar.setVisible(bool(visible))
        self.layout_callback()

    def set_zoom_visible(self, visible: bool) -> None:
        """Изменяет видимость элементов управления масштабом."""
        self.settings["zoom_control_visible"] = bool(visible)
        self._set_zoom_visible(bool(visible))

    def _set_zoom_visible(self, visible: bool) -> None:
        """Синхронно показывает или скрывает ползунок и его подпись."""
        self.tool_bar.zoom_control.setVisible(visible)
        self.tool_bar.zoom_label.setVisible(visible)

    def set_welcome_visible(self, visible: bool) -> None:
        """Сохраняет настройку отображения стартового окна и применяет её."""
        self.settings["show_welcome"] = bool(visible)
        self._set_welcome_visible(bool(visible))

    def _set_welcome_visible(self, visible: bool) -> None:
        """Показывает или скрывает окно недавних проектов."""
        if self.recent_window is None:
            return

        if visible:
            self.recent_window.show()
        else:
            self.recent_window.hide()

    def set_theme(self, theme: str) -> None:
        """Применяет тему оформления без изменения других настроек."""
        self._set_theme(theme)

    def _set_theme(self, theme: str) -> None:
        """Настраивает палитру приложения и обновляет состояние переключателей темы."""
        if theme not in ("dark", "light"):
            theme = "dark"

        self.settings["theme"] = theme
        self.layer_panel.apply_theme(theme)

        if self.recent_window is not None:
            self.recent_window.apply_theme(theme)

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

        self._set_action_checked(self.dark_theme_action, theme == "dark")
        self._set_action_checked(self.light_theme_action, theme == "light")
