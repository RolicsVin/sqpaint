from core.models import *
from ui.tool_bar import ToolBar
from ui.canvas import Canvas
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout


class DomainWindow(QMainWindow):
    def __init__(self, project: Project):
        super().__init__()
        self.project = project

        self.setWindowTitle(project.get_name())
        self.setGeometry(300, 300, project.get_width(),
                         project.get_height() + ToolBar.HEIGHT)

        self.layout = QVBoxLayout()

        self.tool_bar = ToolBar()
        self.canvas = Canvas(project.get_layers(),
                             project.get_width(),
                             project.get_height())

        self.layout.addWidget(self.tool_bar)
        self.layout.addWidget(self.canvas)

        self.show()