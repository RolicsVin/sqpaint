from PyQt6.QtCore import QBuffer, QIODevice
from PyQt6.QtGui import QImage


def image_to_bytes(img: QImage) -> bytes:
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


def bytes_to_image(data: bytes) -> QImage:
    img = QImage()
    img.loadFromData(data, "PNG")
    return img.convertToFormat(QImage.Format.Format_ARGB32)