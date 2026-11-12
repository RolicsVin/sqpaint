"""Модели проекта и слоёв, используемые графическим редактором."""
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtGui import QImage, QPainter


@dataclass(eq=False)
class Layer:
    """Представляет отдельный слой изображения."""

    name: str
    z_order: int
    visible: bool
    image: QImage

    def get_name(self) -> str:
        """Возвращает название слоя."""
        return self.name

    def set_name(self, name: str) -> None:
        """Устанавливает название слоя."""
        self.name = name

    def get_z_order(self) -> int:
        """Возвращает позицию слоя в порядке наложения."""
        return self.z_order

    def set_z_order(self, z_order: int) -> None:
        """Устанавливает позицию слоя в порядке наложения."""
        self.z_order = z_order

    def is_visible(self) -> bool:
        """Возвращает признак видимости слоя."""
        return self.visible

    def set_visible(self, visible: bool) -> None:
        """Устанавливает видимость слоя."""
        self.visible = visible

    def reverse_visible(self) -> bool:
        """Инвертирует видимость слоя и возвращает новое состояние."""
        self.visible = not self.visible
        return self.visible


@dataclass
class Project:
    """Хранит параметры документа и коллекцию его слоёв."""

    name: str
    width: int
    height: int
    created_at: datetime
    path: str
    layers: list[Layer]
    supports_transparency: bool = True
    max_undo_steps: int = 10

    def get_name(self) -> str:
        """Возвращает название проекта."""
        return self.name

    def set_name(self, name: str) -> None:
        """Изменяет название проекта."""
        self.name = name

    def get_path(self) -> str:
        """Возвращает путь к файлу проекта."""
        return self.path

    def get_width(self) -> int:
        """Возвращает ширину документа в пикселях."""
        return self.width

    def get_height(self) -> int:
        """Возвращает высоту документа в пикселях."""
        return self.height

    def get_created_at(self) -> datetime:
        """Возвращает дату и время создания проекта."""
        return self.created_at

    def get_layers(self) -> list[Layer]:
        """Возвращает список слоёв проекта."""
        return self.layers

    def add_layer(self, layer: Layer) -> bool:
        """Добавляет слой и нормализует порядок слоёв."""
        if not isinstance(layer, Layer):
            raise AddLayerError(f"Добавлять можно только объекты Layer: {layer!r}")

        if any(existing.get_name() == layer.get_name() for existing in self.layers):
            return False

        self.layers.append(layer)
        self._normalize_layer_order()
        return True

    def create_layer(
        self,
        name_prefix: str = "Слой",
        image: QImage | None = None,
        visible: bool = True,
        fill: int = 0,
    ) -> Layer:
        """Создаёт слой с уникальным названием и добавляет его в проект."""
        if image is None:
            image = QImage(
                self.width,
                self.height,
                QImage.Format.Format_ARGB32,
            )
            image.fill(fill)
        else:
            image = image.convertToFormat(QImage.Format.Format_ARGB32)

        existing_names = {layer.get_name() for layer in self.layers}
        number = 1
        name = f"{name_prefix} {number}"

        while name in existing_names:
            number += 1
            name = f"{name_prefix} {number}"

        layer = Layer(name, len(self.layers), visible, image)
        self.add_layer(layer)
        return layer

    def rename_layer(self, layer: Layer, name: str) -> bool:
        """Переименовывает принадлежащий проекту слой с проверкой уникальности имени."""
        name = str(name).strip()
        if layer not in self.layers or not name:
            return False

        if any(
            other is not layer and other.get_name() == name
            for other in self.layers
        ):
            return False

        layer.set_name(name)
        return True

    def set_layer_visibility(self, layer: Layer, visible: bool) -> bool:
        """Изменяет видимость слоя, если он принадлежит проекту."""
        if layer not in self.layers:
            return False

        layer.set_visible(bool(visible))
        return True

    def remove_layer(self, layer: Layer) -> bool:
        """Удаляет слой из проекта и обновляет порядок оставшихся слоёв."""
        if layer not in self.layers:
            return False

        self.layers.remove(layer)
        self._normalize_layer_order()
        return True

    def move_layer(
        self,
        source: Layer,
        target: Layer,
        insert_before: bool = True,
    ) -> bool:
        """Перемещает исходный слой относительно целевого и обновляет z_order."""
        if (
            source is target
            or source not in self.layers
            or target not in self.layers
        ):
            return False

        self.layers.remove(source)
        target_index = self.layers.index(target)
        if not insert_before:
            target_index += 1

        self.layers.insert(target_index, source)
        self._normalize_layer_order()
        return True

    def resize(self, width: int, height: int) -> None:
        """Изменяет размер документа и всех слоёв, сохраняя левый верхний угол."""
        width, height = int(width), int(height)
        if width <= 0 or height <= 0:
            raise ValueError("Размеры холста должны быть положительными.")

        if width == self.width and height == self.height:
            return

        resized_images = []
        for layer in self.layers:
            resized = QImage(
                width,
                height,
                QImage.Format.Format_ARGB32,
            )
            resized.fill(0)

            painter = QPainter(resized)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Source
            )
            painter.drawImage(0, 0, layer.image)
            painter.end()
            resized_images.append(resized)

        for layer, image in zip(self.layers, resized_images):
            layer.image = image

        self.width = width
        self.height = height

    def crop(self, x: int, y: int, width: int, height: int) -> None:
        """Обрезает документ и все слои по заданной прямоугольной области."""
        x, y, width, height = int(x), int(y), int(width), int(height)
        if width <= 0 or height <= 0:
            raise ValueError("Размер области кадрирования должен быть положительным.")

        if x < 0 or y < 0 or x + width > self.width or y + height > self.height:
            raise ValueError("Область кадрирования выходит за границы холста.")

        cropped_images = [
            layer.image.copy(x, y, width, height)
            for layer in self.layers
        ]
        for layer, image in zip(self.layers, cropped_images):
            layer.image = image

        self.width = width
        self.height = height

    def _normalize_layer_order(self) -> None:
        """Назначает слоям последовательные значения z_order по их позиции в списке."""
        for z_order, layer in enumerate(self.layers):
            layer.set_z_order(z_order)

    def remove_all_layers(self) -> None:
        """Удаляет все слои проекта."""
        self.layers.clear()


class ProjectError(Exception):
    """Базовая ошибка операций с проектом."""


class AddLayerError(ProjectError):
    """Ошибка добавления слоя в проект."""


class LayerError(Exception):
    """Базовая ошибка операций со слоем."""
