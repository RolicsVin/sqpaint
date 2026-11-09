from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSlider


class ZoomControl(QWidget):
    zoom_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(5)

        self.zoom_out_button = QPushButton("−", self)
        self.zoom_out_button.setFixedWidth(24)
        self.zoom_out_button.setToolTip("Уменьшить масштаб")
        self.zoom_in_button = QPushButton("+", self)
        self.zoom_in_button.setFixedWidth(24)
        self.zoom_in_button.setToolTip("Увеличить масштаб")

        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(10, 400)
        self.slider.setValue(100)
        self.slider.setFixedWidth(125)
        self.slider.setToolTip("Масштаб холста")

        self.value_label = QLabel("100%", self)
        self.value_label.setMinimumWidth(42)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight |
                                      Qt.AlignmentFlag.AlignVCenter)
        self.reset_button = QPushButton("100%", self)
        self.reset_button.setToolTip("Сбросить масштаб")
        self.reset_button.setFixedWidth(48)

        layout.addWidget(self.zoom_out_button)
        layout.addWidget(self.slider)
        layout.addWidget(self.zoom_in_button)
        layout.addWidget(self.value_label)
        layout.addWidget(self.reset_button)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.zoom_out_button.clicked.connect(
            lambda: self.set_value(self.slider.value() - 10)
        )
        self.zoom_in_button.clicked.connect(
            lambda: self.set_value(self.slider.value() + 10)
        )
        self.reset_button.clicked.connect(lambda: self.set_value(100))

    def _on_slider_changed(self, value: int) -> None:
        self.value_label.setText(f"{value}%")
        self.zoom_changed.emit(value)

    def set_value(self, value: int) -> None:
        self.slider.setValue(max(10, min(400, int(value))))

    def set_zoom(self, value: int) -> None:
        """Синхронизирует ползунок без повторной отправки сигнала."""
        value = max(10, min(400, int(value)))
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.value_label.setText(f"{value}%")
