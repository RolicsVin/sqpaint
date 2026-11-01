"""В этом модуле хранятся классы для работы с SQLite."""
from dataclasses import dataclass
from datetime import datetime
from core.models import *
from core.image_utils import *
import sqlite3
import os


class ProjectDatabase:
    """Класс для загрузки, сохранения и создания проекта в .sqlite файл."""

    SCHEMA = """
    CREATE TABLE project (
        id         INTEGER PRIMARY KEY CHECK (id = 1),
        name       TEXT    NOT NULL,
        width      INTEGER NOT NULL,
        height     INTEGER NOT NULL,
        created_at TEXT    NOT NULL
    );
    
    CREATE TABLE layers (
        id      INTEGER PRIMARY KEY,
        name    TEXT    NOT NULL,
        z_order INTEGER NOT NULL,
        visible INTEGER NOT NULL DEFAULT 1,
        pixels  BLOB    NOT NULL
    );
    
    CREATE TABLE logs (
        id         INTEGER PRIMARY KEY,
        log        TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """

    def create(self, path: str, name: str, width: int, height: int) -> None:
        """Создаёт новый файл проекта: таблицы, строку project и все слои."""
        if os.path.exists(path):
            raise FileExistsError(f"Файл уже существует: {path}")

        project = Project(name, width, height, datetime.now(), path, [])
    
        self.path = path
        self.conn = sqlite3.connect(path)
    
        # "with conn" = одна транзакция: либо всё записалось, либо ничего
        with self.conn:
            self.conn.executescript(self.SCHEMA)
            self.conn.execute(
                "INSERT INTO project (id, name, width, height, created_at) "
                "VALUES (1, ?, ?, ?, ?)",
                (project.name, project.width, project.height, str(project.created_at)),
            )
            self._write_layers(project)
            print("Проект создан")

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
            """Перезаписывает данные проекта в уже открытом файле."""
            if self.conn is None:
                raise RuntimeError("Файл проекта не открыт: сначала create() или load()")
    
            with self.conn:
                self.conn.execute(
                    "UPDATE project SET name = ?, width = ?, height = ? WHERE id = 1",
                    (project.name, project.width, project.height),
                )
                self.conn.execute("DELETE FROM layers")
                self._write_layers(project)
                print("Проект сохранён")

    def _write_layers(self, project: Project) -> None:
        """Запишет слои в существующий проект."""
        for layer in project.layers:
            cur = self.conn.execute(
                "INSERT INTO layers (name, z_order, visible, pixels) "
                "VALUES (?, ?, ?, ?)",
                (
                    layer.name,
                    layer.z_order,
                    int(layer.visible),
                    image_to_bytes(layer.image), # PNG-байты
                ),
            )
            layer.id = cur.lastrowid  # запоминаем id, который выдала БД