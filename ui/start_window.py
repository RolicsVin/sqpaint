# Стартовое окно
from core.time_utils import *
from ui.rounded_widget import RoundedWidget
from services import recent_projects

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel


class RecentProjectWindow(QWidget):
        project_select = pyqtSignal(str)

        def __init__(self):
            super().__init__()
            self.setWindowTitle("Недавние проекты")
            self.setFixedSize(700, 500)

            self.Vlayout = QVBoxLayout(self)
            self.Vlayout.addWidget(QLabel('Добро пожаловать в SQPaint!'))

            for project in recent_projects.get_recent_projects():
                  line = RoundedWidget(self)

                  line.hlayout = QHBoxLayout(line)
                  line.hlayout.addWidget(QLabel(self, text=project[0]))
                  line.path = QLabel(self, text=project[1])
                  line.hlayout.addWidget(line.path)
                  line.hlayout.addWidget(QLabel(self, text=datetime_to_str(project[2])))

                  line.clicked.connect(lambda x=line: self._project_change(x))
                  self.Vlayout.addWidget(line)

        def _project_change(self, line):
              self.project_select.emit(line.path.text())
              self.hide()