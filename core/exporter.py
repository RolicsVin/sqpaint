"""Экспорт итогового изображения документа в графические форматы."""
from PyQt6.QtGui import QImage, QPainter


class Exporter:
    """Сервис экспорта изображений в файловые форматы."""

    @staticmethod
    def export(image: QImage, path: str, image_format: str) -> bool:
        """Сохраняет QImage в указанном формате.

        JPEG не поддерживает прозрачность, поэтому перед сохранением
        изображение объединяется с белым фоном.
        """
        if image is None or image.isNull() or not path or not image_format:
            return False

        image_format = image_format.lower()

        if image_format in ("jpg", "jpeg"):
            output = QImage(image.size(), QImage.Format.Format_RGB32)
            output.fill(0xFFFFFFFF)

            painter = QPainter(output)
            painter.drawImage(0, 0, image)
            painter.end()

            return output.save(path, "JPEG")

        return image.save(path, image_format.upper())
