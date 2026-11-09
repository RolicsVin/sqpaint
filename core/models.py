"""В этом модуле содержатся самые главные классы - Project и Layer."""
from PyQt6.QtGui import QImage, QPainter
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Layer:
    """Класс слоя изображения."""
    name: str
    z_order: int
    visible: bool
    image: QImage

    def get_name(self) -> str:
        return self.name

    def set_name(self, name: str) -> None:
        self.name = name

    def get_z_order(self) -> int:
        return self.z_order
    
    def set_z_order(self, z_order: int) -> None:
        self.z_order = z_order
    
    def is_visible(self) -> bool:
        return self.visible
    
    def set_visible(self, visible: bool) -> None:
        self.visible = visible

    def reverse_visible(self) -> bool:
        self.visible = not self.visible
        return self.visible



@dataclass
class Project:
    """Класс проекта."""
    name: str
    width: int
    height: int
    created_at: datetime
    path: str
    layers: list[Layer]

    def get_name(self) -> str:
        return self.name

    def set_name(self, name: str) -> None:
        self.name = name

    def get_path(self) -> str:
        return self.path

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height

    def get_created_at(self) -> datetime:
        return self.created_at

    def get_layers(self) -> list[Layer]:
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
        """Создаёт и добавляет слой с уникальным именем."""
        if image is None:
            image = QImage(
                self.width, self.height, QImage.Format.Format_ARGB32
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

    def remove_layer(self, layer: Layer) -> bool:
        """Удаляет слой из проекта, если он в нём существует."""
        if layer not in self.layers:
            return False
        self.layers.remove(layer)
        self._normalize_layer_order()
        return True

    def move_layer(
        self, source: Layer, target: Layer, insert_before: bool = True
    ) -> bool:
        """Перемещает source относительно target и обновляет z_order."""
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
        """Меняет размер документа и всех слоёв, сохраняя левый верхний угол."""
        width, height = int(width), int(height)
        if width <= 0 or height <= 0:
            raise ValueError("Размеры холста должны быть положительными.")
        if width == self.width and height == self.height:
            return

        resized_images = []
        for layer in self.layers:
            resized = QImage(width, height, QImage.Format.Format_ARGB32)
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

    def _normalize_layer_order(self) -> None:
        """Поддерживает непрерывный z_order в порядке списка слоёв."""
        for z_order, layer in enumerate(self.layers):
            layer.set_z_order(z_order)

    def remove_all_layers(self) -> None:
        """Удаляет все слои проекта."""
        self.layers.clear()

# Ошибки
class ProjectError(Exception):
    '''Класс ошибок класса Project.'''
    pass


class AddLayerError(ProjectError):
    '''Ошибка добавления слоя в проект'''
    pass


class LayerError(Exception):
    '''Класс ошибок класса Layer.'''
    pass