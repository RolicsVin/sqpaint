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

def save_image(image: QImage, path: str, image_format: str) -> bool:
    """Сохраняет QImage в указанном формате.

    Для JPEG изображение предварительно объединяется с белым фоном,
    поскольку формат не поддерживает прозрачность.
    """
    image_format = image_format.lower()
    output = image

    if image_format in ("jpg", "jpeg"):
        output = QImage(
            image.size(),
            QImage.Format.Format_RGB32,
        )
        output.fill(0xFFFFFFFF)

        from PyQt6.QtGui import QPainter
        painter = QPainter(output)
        painter.drawImage(0, 0, image)
        painter.end()

        image_format = "JPEG"

    return output.save(path, image_format.upper())
