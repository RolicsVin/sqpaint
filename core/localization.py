"""Классы локализованных Qt-виджетов и менеджер переводов."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
)


class LocalizedLabel(QLabel):
    """QLabel, текст которого можно переключать между языками."""

    def __init__(self, text: str = "", parent=None, language: str = "ru"):
        """Создаёт подпись и регистрирует исходный текст для выбранного языка.
        """
        super().__init__(text, parent)
        self._language = language
        self._translations = {"ru": text}

    def add_localization(self, language: str, text: str) -> None:
        """Добавляет перевод и сразу применяет его, если язык активен."""
        self._translations[language] = text
        if language == self._language:
            super().setText(text)

    def set_language(self, language: str) -> None:
        """Переключает текст подписи на указанный язык, если перевод
        существует.
        """
        self._language = language
        if language in self._translations:
            super().setText(self._translations[language])


class LocalizedButton(QPushButton):
    """QPushButton с поддержкой переключаемых подписей."""

    def __init__(self, text: str = "", parent=None, language: str = "ru"):
        """Создаёт кнопку и сохраняет её исходную подпись."""
        super().__init__(text, parent)
        self._language = language
        self._translations = {"ru": text}

    def add_localization(self, language: str, text: str) -> None:
        """Добавляет перевод и обновляет подпись активной кнопки."""
        self._translations[language] = text
        if language == self._language:
            super().setText(text)

    def set_language(self, language: str) -> None:
        """Применяет перевод подписи для указанного языка."""
        self._language = language
        if language in self._translations:
            super().setText(self._translations[language])


class LocalizedComboBox(QComboBox):
    """QComboBox, сохраняющий данные элементов при переключении их подписей."""

    def __init__(self, parent=None, language: str = "ru"):
        """Создаёт список и инициализирует хранилище переводов элементов."""
        super().__init__(parent)
        self._language = language
        self._item_translations: list[dict[str, str]] = []

    def add_localized_item(
        self,
        translations: dict[str, str],
        user_data=None,
    ) -> None:
        """Добавляет элемент с переводами и необязательными пользовательскими
        данными.
        """
        translations = dict(translations)
        text = translations.get(self._language) or next(
            iter(translations.values()),
            "",
        )
        self.addItem(text, user_data)
        self._item_translations.append(translations)

    def add_localization(
        self,
        index: int,
        language: str,
        text: str,
    ) -> None:
        """Добавляет или обновляет перевод элемента по его индексу."""
        if not 0 <= index < len(self._item_translations):
            raise IndexError(f"ComboBox item index out of range: {index}")

        self._item_translations[index][language] = text
        if language == self._language:
            self.setItemText(index, text)

    def set_language(self, language: str) -> None:
        """Обновляет подписи всех элементов для указанного языка."""
        self._language = language
        for index, translations in enumerate(self._item_translations):
            text = translations.get(language)
            if text is not None:
                self.setItemText(index, text)


class LocalizationManager:
    """Регистрирует виджеты и синхронизирует их текст с выбранным языком."""

    SUPPORTED_LANGUAGES = ("ru", "en")

    def __init__(self, language: str = "ru"):
        """Создаёт менеджер и выбирает поддерживаемый язык по умолчанию."""
        self.language = (
            language if language in self.SUPPORTED_LANGUAGES else "ru"
        )
        self._widgets: list[tuple[object, dict[str, str]]] = []

    def register(self, widget, translations: dict[str, str]):
        """Регистрирует Qt-элемент и применяет к нему перевод текущего языка.
        """
        translations = dict(translations)

        if isinstance(widget, (LocalizedLabel, LocalizedButton)):
            for language, text in translations.items():
                widget.add_localization(language, text)

        self._widgets.append((widget, translations))
        self._apply_one(widget, translations)
        return widget

    def set_language(self, language: str) -> None:
        """Переключает язык всех зарегистрированных элементов интерфейса."""
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        self.language = language
        for widget, translations in self._widgets:
            self._apply_one(widget, translations)

    def _apply_one(
        self,
        widget,
        translations: dict[str, str],
    ) -> None:
        """Применяет перевод к одному виджету с учётом его типа Qt."""
        if hasattr(widget, "set_language"):
            widget.set_language(self.language)
            return

        text = translations.get(self.language)
        if text is None:
            return

        if isinstance(widget, QMenu):
            widget.setTitle(text)
            widget.menuAction().setText(text)
        elif isinstance(widget, (QDialog, QMainWindow)):
            widget.setWindowTitle(text)
        elif isinstance(widget, QGroupBox):
            widget.setTitle(text)
        elif hasattr(widget, "setText"):
            # QLabel, QPushButton, QCheckBox, QLineEdit, QAction и другие
            # элементы.
            widget.setText(text)
        elif hasattr(widget, "setWindowTitle"):
            # Остальные окна верхнего уровня.
            widget.setWindowTitle(text)
