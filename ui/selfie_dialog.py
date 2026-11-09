"""Диалог предпросмотра и съёмки селфи."""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout,
)

from services.webcam import Webcam


class SelfieDialog(QDialog):
    """Показывает видео с камеры и возвращает сделанный снимок."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Сделать селфи")
        self.setModal(True)
        self.resize(720, 560)

        self._camera = Webcam()
        self._image = None

        self.preview = QLabel("Ожидание камеры…", self)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(480, 360)
        self.preview.setStyleSheet("background: #202020; color: white;")

        self.capture_button = QPushButton("Сделать снимок", self)
        self.cancel_button = QPushButton("Отмена", self)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.capture_button)
        buttons.addWidget(self.cancel_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.preview, 1)
        layout.addLayout(buttons)

        self.capture_button.clicked.connect(self._capture)
        self.cancel_button.clicked.connect(self.reject)

        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._update_preview)
        self._timer.start()

    def _update_preview(self) -> None:
        image = self._camera.read()
        if image is None:
            return
        pixmap = QPixmap.fromImage(image).scaled(
            self.preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview.setPixmap(pixmap)

    def _capture(self) -> None:
        image = self._camera.read()
        if image is None:
            QMessageBox.warning(
                self, "Камера", "Не удалось получить кадр с веб-камеры."
            )
            return
        self._image = image
        self.accept()

    def get_image(self):
        """Возвращает снимок или None, если диалог отменён."""
        return self._image

    def done(self, result: int) -> None:
        self._timer.stop()
        self._camera.release()
        super().done(result)
