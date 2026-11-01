"""В этом модуле хранятся классы для работы с SQLite."""
from dataclasses import dataclass
from datetime import datetime
from core.models import *
from image_utils import *
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

    def create(self, path: str, name: str, width: int, height: int) -> Project:
        """Создаёт новый файл проекта: таблицы, строку project и все слои."""
        if os.path.exists(path):
            raise FileExistsError(f"Файл уже существует: {path}")

        project = Project(name, width, height, datetime.now(), path, [])
    
        self.close()
        self.path = path
        self.conn = sqlite3.connect(path)
    
        # "with conn" = одна транзакция: либо всё записалось, либо ничего
        with self.conn:
            self.conn.executescript(self.SCHEMA)
            self.conn.execute(
                "INSERT INTO project (id, name, width, height, created_at) "
                "VALUES (1, ?, ?, ?, ?)",
                (project.name, project.width, project.height, project.created_at),
            )
            self._write_layers(project)
            print("Проект создан")
            
            return Project

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