from core.models import Project
from ui.tool_bar import ToolBar
from ui.canvas import Canvas
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget


class DomainWindow(QMainWindow):
    def __init__(self, project: Project):
        super().__init__()
        self.project = project

        self.setWindowTitle(project.get_name())
        self.setGeometry(
            300,
            300,
            project.get_width(),
            project.get_height() + ToolBar.HEIGHT,
        )

        central_widget = QWidget(self)
        central_layout = QVBoxLayout(central_widget)

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

    def set_canvas_color(self, color):
        self.canvas.color = color
