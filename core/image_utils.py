"""Преобразование изображений Qt в бинарные данные и обратно."""
from PyQt6.QtCore import QBuffer, QIODevice
from PyQt6.QtGui import QImage


def image_to_bytes(image: QImage) -> bytes:
    """Кодирует QImage в PNG и возвращает его бинарное представление."""
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def bytes_to_image(data: bytes) -> QImage:
    """Декодирует PNG-данные в изображение формата ARGB32."""
    image = QImage()
    image.loadFromData(data, "PNG")
    return image.convertToFormat(QImage.Format.Format_ARGB32)
