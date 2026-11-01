from core.models import Project
from core.database import ProjectDatabase
from ui.tool_bar import ToolBar
from ui.canvas import Canvas
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget


class DomainWindow(QMainWindow):
    HEADERS_HEIGHT = 25

    def __init__(self, project: Project, database: ProjectDatabase):
        super().__init__()
        self.project = project
        self.database = database

        size = QApplication.primaryScreen().size()
        self.setGeometry(0, 0, size.width(), size.height())

        self.menu_bar = self.menuBar()

        # Файловое меню
        self.file_menu = self.menu_bar.addMenu("Файл")
        self.edit_menu = self.menu_bar.addMenu("Правка")
        self.view_menu = self.menu_bar.addMenu("Вид")
        self.help_menu = self.menu_bar.addMenu("Справка")

        self.new_action = QAction("Создать", self)
        self.open_action = QAction("Открыть", self)
        self.save_action = QAction("Сохранить", self)
        self.exit_action = QAction("Выход", self)

        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.exit_action)

        #self.new_action.triggered.connect(self.save)
        #self.open_action.triggered.connect(self.new_file)
        self.save_action.triggered.connect(self.save)
        self.exit_action.triggered.connect(self.close)

        self.tool_bar = ToolBar(self)
        self.canvas = Canvas(
            self,
            project.get_layers(),
            project.get_width(),
            project.get_height(),
        )
        self.tool_bar.move(0, self.HEADERS_HEIGHT)
        self.tool_bar.resize(size.width(), ToolBar.HEIGHT)
        self.canvas.move(0, ToolBar.HEIGHT + self.HEADERS_HEIGHT)

        # Передаём выбранный цвет с панели инструментов на холст.
        self.tool_bar.color_selected.connect(self.set_canvas_color)

    def save(self):
        self.database.save(self.project)

    def set_canvas_color(self, color):
        self.canvas.color = color
