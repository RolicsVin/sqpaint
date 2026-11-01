from core.models import Project
from core.database import ProjectDatabase
from ui.tool_bar import ToolBar
from ui.canvas import Canvas
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget


class DomainWindow(QMainWindow):
    def __init__(self, project: Project, database: ProjectDatabase):
        super().__init__()
        self.project = project
        self.database = database

        self.setWindowTitle(project.get_name())
        self.setGeometry(
            300,
            300,
            project.get_width(),
            project.get_height() + ToolBar.HEIGHT,
        )

        central_widget = QWidget(self)
        central_layout = QVBoxLayout(central_widget)

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

        self.new_action.triggered.connect(self.save)
        #self.open_action.triggered.connect(self.new_file)
        #self.save_action.triggered.connect(self.save_file)
        self.exit_action.triggered.connect(self.close)

        self.tool_bar = ToolBar()
        self.canvas = Canvas(
            project.get_layers(),
            project.get_width(),
            project.get_height(),
        )

        # Передаём выбранный цвет с панели инструментов на холст.
        self.tool_bar.color_selected.connect(self.set_canvas_color)

        central_layout.addWidget(self.tool_bar)
        central_layout.addWidget(self.canvas)

        self.setCentralWidget(central_widget)

    def save(self):
        self.database.save(self.project)

    def set_canvas_color(self, color):
        self.canvas.color = color
