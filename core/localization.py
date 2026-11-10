"""Runtime localization primitives for SQPaint widgets."""
from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QPushButton, QComboBox


class LocalizedLabel(QLabel):
    """QLabel with language-specific text that can be switched at runtime."""

    def __init__(self, text: str = "", parent=None, language: str = "ru"):
        super().__init__(text, parent)
        self._language = language
        self._translations = {"ru": text}

    def add_localization(self, language: str, text: str) -> None:
        self._translations[language] = text
        if language == self._language:
            super().setText(text)

    def set_language(self, language: str) -> None:
        self._language = language
        if language in self._translations:
            super().setText(self._translations[language])


class LocalizedButton(QPushButton):
    """QPushButton with runtime-switchable captions."""

    def __init__(self, text: str = "", parent=None, language: str = "ru"):
        super().__init__(text, parent)
        self._language = language
        self._translations = {"ru": text}

    def add_localization(self, language: str, text: str) -> None:
        self._translations[language] = text
        if language == self._language:
            super().setText(text)

    def set_language(self, language: str) -> None:
        self._language = language
        if language in self._translations:
            super().setText(self._translations[language])


class LocalizedComboBox(QComboBox):
    """QComboBox whose item captions are translated without changing item data."""

    def __init__(self, parent=None, language: str = "ru"):
        super().__init__(parent)
        self._language = language
        self._item_translations: list[dict[str, str]] = []

    def add_localized_item(self, translations: dict[str, str], user_data=None) -> None:
        translations = dict(translations)
        text = translations.get(self._language) or next(iter(translations.values()), "")
        self.addItem(text, user_data)
        self._item_translations.append(translations)

    def add_localization(self, index: int, language: str, text: str) -> None:
        if not 0 <= index < len(self._item_translations):
            raise IndexError(f"ComboBox item index out of range: {index}")
        self._item_translations[index][language] = text
        if language == self._language:
            self.setItemText(index, text)

    def set_language(self, language: str) -> None:
        self._language = language
        for index, translations in enumerate(self._item_translations):
            text = translations.get(language)
            if text is not None:
                self.setItemText(index, text)


class LocalizationManager:
    """Keeps registered widgets synchronized with the selected language."""

    SUPPORTED_LANGUAGES = ("ru", "en")

    def __init__(self, language: str = "ru"):
        self.language = language if language in self.SUPPORTED_LANGUAGES else "ru"
        self._widgets: list[tuple[object, dict[str, str]]] = []

    def register(self, widget, translations: dict[str, str]):
        """Register a Qt widget/action/menu. Returns the same object for convenience."""
        translations = dict(translations)
        if isinstance(widget, (LocalizedLabel, LocalizedButton)):
            for language, text in translations.items():
                widget.add_localization(language, text)
        self._widgets.append((widget, translations))
        self._apply_one(widget, translations)
        return widget

    def set_language(self, language: str) -> None:
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")
        self.language = language
        for widget, translations in self._widgets:
            self._apply_one(widget, translations)

    def _apply_one(self, widget, translations: dict[str, str]) -> None:
        if hasattr(widget, "set_language"):
            widget.set_language(self.language)
            return
        text = translations.get(self.language)
        if text is None:
            return
        if hasattr(widget, "setTitle"):
            widget.setTitle(text)
        elif hasattr(widget, "setText"):
            widget.setText(text)
