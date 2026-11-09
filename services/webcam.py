"""Захват кадров с веб-камеры через OpenCV."""

import cv2
from PyQt6.QtGui import QImage


class Webcam:
    """Небольшая обёртка над cv2.VideoCapture без зависимости от UI."""

    def __init__(self, camera_index: int = 0):
        self._capture = cv2.VideoCapture(camera_index)
        if not self._capture.isOpened():
            self._capture.release()
            raise RuntimeError(
                "Не удалось открыть веб-камеру. Проверьте подключение и разрешения."
            )

    def read(self) -> QImage | None:
        """Считывает кадр и возвращает независимый RGB QImage."""
        success, frame = self._capture.read()
        if not success or frame is None:
            return None

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = frame.shape
        image = QImage(
            frame.data,
            width,
            height,
            channels * width,
            QImage.Format.Format_RGB888,
        )
        return image.copy()

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
