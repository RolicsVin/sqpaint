"""В этом модуле хранятся классы для работы с SQLite."""
from dataclasses import dataclass
from core.models import *
from image_utils import *
import sqlite3


class ProjectDatabase:
    """Класс для загрузки, сохранения и создания проекта в .sqlite файл."""

    def create(self, path: str, project: Project) -> Project:
        """Создаст новый проект по указанному пути. Если по пути что-то было: перезапишет."""
        with sqlite3.connect(path) as con:
            cur = con.cursor()
            data = cur.execute().fetchall()

    def load(self, path: str) -> Project:
        """Загрузит проект по пути и вернёт Project."""
        with sqlite3.connect(path) as con:
            cur = con.cursor()
            data = cur.execute("SELECT * FROM project").fetchall()[0]

            # восстанавливаем слои
            layers = []
            for layer_data in cur.execute("SELECT * FROM layers").fetchall():
                layers.append(Layer(layer_data[1],
                                    layer_data[2],
                                    bool(layer_data[3]),
                                    bytes_to_image(layer_data[4])))

            return Project(data[1], data[2], data[3], data[4], path, layers)

    def save(self, project: Project) -> None:
        """Сохранит проект."""
        with sqlite3.connect(project.get_path()) as con:
            pass
            con.commit()