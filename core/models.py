"""В этом модуле содержатся самые главные классы - Project и Layer."""
from PyQt6.QtGui import QImage
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
        """Добавит слой в проект. Вернёт успех или не успех(bool)."""
        if not isinstance(layer, Layer):
            raise AddLayerError(f'Добавлять можно только слои: {layer}')
        
        if layer.get_name() in list(map(lambda x: x.get_name(), self.layers)):
            # Не может быть одинаковых имём
            print('Добавление слоя потерпело неудачу - имена совпадают.')
            return False

        if layer.get_z_order() in list(map(lambda x: x.get_z_order(), self.layers)):
            # Слои не должны быть друг в друге
            print('Добавление слоя потерпело неудачу - z_order совпадают.')
            return False
        
        self.layers.append(layer)
        print('добавлен слой')
        return True

    def remove_layer(self, layer: Layer) -> bool:
        """Удалит слой из проекта. Вернёт успех или не успех(bool)."""
        if layer not in self.layers:
            print(f'Удаление слоя завершилось ошибкой: такого слоя не существует. {layer.get_name()}')
            return False
        
        self.layers.remove(self.layers)
        print(f'Был удалён слой {layer.get_name()}')

        return True

    def remove_all_layers(self) -> None:
        """ОЧЕНЬ ОСТОРОЖНО. Удаляет все слои."""
        for layer in self.layers:
            self.remove_layer(layer.get_name())
        print('Были удалены все слои')


# Ошибки
class ProjectError:
    '''Класс ошибок класса Project.'''
    pass


class AddLayerError(ProjectError):
    '''Ошибка добавления слоя в проект'''
    pass


class LayerError:
    '''Класс ошибок класса Layer.'''
    pass