# Стартовое окно
from pathlib import Path

from core.time_utils import *
from ui.rounded_widget import RoundedWidget
from services import recent_projects

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy,
)


# Единый стиль окна. Задан явно, поэтому выглядит одинаково
# и при светлой, и при тёмной теме Windows.
STYLE = """
#startWindow {
    background-color: #1e1e1e;
}
QLabel {
    color: #e6e6e6;
    background: transparent;
}
#title {
    font-size: 28px;
    font-weight: 700;
}
#subtitle, #sectionLabel, #projectPath, #projectDate {
    color: #8a8a8a;
}
#subtitle {
    font-size: 13px;
}
#sectionLabel {
    font-size: 12px;
    font-weight: 600;
}
#projectName {
    font-size: 15px;
    font-weight: 600;
}
#projectPath, #projectDate {
    font-size: 12px;
}
#emptyLabel {
    color: #6f6f6f;
    font-size: 14px;
}

QPushButton {
    border-radius: 8px;
    padding: 10px 22px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton#primaryButton {
    background-color: #3b82f6;
    color: #ffffff;
    border: none;
}
QPushButton#primaryButton:hover {
    background-color: #5a96f7;
}
QPushButton#primaryButton:pressed {
    background-color: #2f6fd8;
}
QPushButton#secondaryButton {
    background-color: #2b2b2b;
    color: #e6e6e6;
    border: 1px solid #3d3d3d;
}
QPushButton#secondaryButton:hover {
    background-color: #353535;
}
QPushButton#secondaryButton:pressed {
    background-color: #262626;
}

#projectsScroll {
    background: transparent;
    border: none;
}
#projectsScroll > QWidget > QWidget {
    background: transparent;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #3d3d3d;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #4d4d4d;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QToolTip {
    background-color: #2b2b2b;
    color: #e6e6e6;
    border: 1px solid #3d3d3d;
}
"""


class ElidedLabel(QLabel):
    """QLabel, который обрезает длинный текст многоточием вместо растягивания окна.
    Полный текст доступен через full_text() и во всплывающей подсказке."""

    def __init__(self, text: str = "", mode=Qt.TextElideMode.ElideRight, parent=None):
        super().__init__(parent)
        self._full_text = text
        self._mode = mode
        self.setToolTip(text)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self._update_text()

    def full_text(self) -> str:
        return self._full_text

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_text()

    def _update_text(self) -> None:
        elided = self.fontMetrics().elidedText(
            self._full_text, self._mode, max(self.width(), 0)
        )
        super().setText(elided)


class ProjectRow(RoundedWidget):
    """Строка списка недавних проектов с подсветкой при наведении."""

    COLOR_NORMAL = "#2b2b2b"
    COLOR_HOVER = "#353535"

    def __init__(self, name: str, path: str, date_text: str, parent=None):
        super().__init__(parent, color=self.COLOR_NORMAL, radius=10)
        self.project_path = path
        self.setFixedHeight(66)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(16)

        # Левая часть: название и путь друг под другом
        texts = QVBoxLayout()
        texts.setSpacing(2)

        name_label = ElidedLabel(name, Qt.TextElideMode.ElideRight)
        name_label.setObjectName("projectName")
        path_label = ElidedLabel(path, Qt.TextElideMode.ElideMiddle)
        path_label.setObjectName("projectPath")

        texts.addWidget(name_label)
        texts.addWidget(path_label)
        layout.addLayout(texts, 1)

        # Правая часть: дата
        date_label = QLabel(date_text)
        date_label.setObjectName("projectDate")
        date_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(date_label, 0)

    def enterEvent(self, event) -> None:
        self.set_color(self.COLOR_HOVER)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.set_color(self.COLOR_NORMAL)
        super().leaveEvent(event)


class RecentProjectWindow(QWidget):
    project_select = pyqtSignal(str)
    open_project = pyqtSignal()
    create_project = pyqtSignal()

    def __init__(self, localization=None, parent=None):
        # Отдельное окно, принадлежащее главному окну: закрывается вместе с ним.
        super().__init__(parent)
        self.setWindowFlag(Qt.Window, True)
        self.localization = localization
        self.setObjectName("startWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)
        self.setWindowTitle("Недавние проекты")
        self.setFixedSize(720, 560)

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(0)

        # --- Логотип приложения ---
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = Path(__file__).resolve().parent.parent / "logo.png"
        logo = QPixmap(str(logo_path))
        if not logo.isNull():
            logo_label.setPixmap(
                logo.scaled(
                    224, 224,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        root.addWidget(logo_label)
        root.addSpacing(12)

        # --- Заголовок ---
        title = QLabel("Добро пожаловать в SQPaint!")
        title.setObjectName("title")
        subtitle = QLabel("Растровый редактор, проекты хранятся в .sqlite")
        subtitle.setObjectName("subtitle")
        root.addWidget(title)
        root.addSpacing(4)
        root.addWidget(subtitle)
        root.addSpacing(22)

        # --- Кнопки ---
        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        self.create_button = QPushButton("Создать проект")
        self.create_button.setObjectName("primaryButton")
        self.create_button.clicked.connect(self.create)
        self.create_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.open_button = QPushButton("Открыть проект…")
        self.open_button.clicked.connect(self.open)
        self.open_button.setObjectName("secondaryButton")
        self.open_button.setCursor(Qt.CursorShape.PointingHandCursor)

        buttons.addWidget(self.create_button)
        buttons.addWidget(self.open_button)
        buttons.addStretch(1)
        root.addLayout(buttons)
        root.addSpacing(28)

        # --- Список недавних проектов ---
        section = QLabel("НЕДАВНИЕ ПРОЕКТЫ")
        section.setObjectName("sectionLabel")
        root.addWidget(section)
        root.addSpacing(10)

        if self.localization is not None:
            self.localization.register(self, {"ru": "Недавние проекты", "en": "Recent projects"})
            self.localization.register(title, {"ru": "Добро пожаловать в SQPaint!", "en": "Welcome to SQPaint!"})
            self.localization.register(subtitle, {"ru": "Растровый редактор, проекты хранятся в .sqlite", "en": "Raster editor; projects are stored in .sqlite"})
            self.localization.register(self.create_button, {"ru": "Создать проект", "en": "Create project"})
            self.localization.register(self.open_button, {"ru": "Открыть проект…", "en": "Open project…"})
            self.localization.register(section, {"ru": "НЕДАВНИЕ ПРОЕКТЫ", "en": "RECENT PROJECTS"})

        scroll = QScrollArea()
        scroll.setObjectName("projectsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.viewport().setAutoFillBackground(False)

        container = QWidget()
        container.setAutoFillBackground(False)
        self.Vlayout = QVBoxLayout(container)
        self.Vlayout.setContentsMargins(0, 0, 8, 0)   # справа отступ под полосу прокрутки
        self.Vlayout.setSpacing(8)

        self._fill_projects()

        scroll.setWidget(container)
        root.addWidget(scroll, 1)

        # Применяем текущий язык после создания всех элементов стартового окна.
        if self.localization is not None:
            self.localization.set_language(self.localization.language)

    def open(self):
        self.open_project.emit()
        self.hide()

    def create(self):
        self.create_project.emit()
        self.hide()

    def _fill_projects(self) -> None:
        projects = recent_projects.get_recent_projects()

        if not projects:
            empty = QLabel(
                "Пока нет недавних проектов.\n"
                "Создайте новый или откройте существующий."
            )
            empty.setObjectName("emptyLabel")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.localization is not None:
                self.localization.register(empty, {"ru": "Пока нет недавних проектов.\nСоздайте новый или откройте существующий.", "en": "No recent projects yet.\nCreate a new project or open an existing one."})
            self.Vlayout.addWidget(empty, 1)
            return

        for name, path, date in projects:
            row = ProjectRow(name, path, datetime_to_str(date))
            row.clicked.connect(lambda r=row: self._project_change(r))
            self.Vlayout.addWidget(row)

        self.Vlayout.addStretch(1)   # чтобы строки не растягивались по высоте

    def _project_change(self, row: ProjectRow) -> None:
        self.project_select.emit(row.project_path)
        self.hide()
