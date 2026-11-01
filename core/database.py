"""В этом модуле хранятся классы для работы с SQLite."""
import sqlite3
from core.models import *
from core.image_utils import *
from core.time_utils import *
from dataclasses import dataclass
from datetime import datetime
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

    def __init__(self):
        self.path: str | None = None
        self.conn: sqlite3.Connection | None = None

    def create(self, path: str, name: str, width: int, height: int) -> Project:
        """Создаёт новый файл проекта и возвращает Project."""
        if os.path.exists(path):
            raise FileExistsError(f"Файл уже существует: {path}")
 
        project = Project(name, width, height, datetime.now(), path, [])
 
        self.close()
        self.path = path
        self.conn = sqlite3.connect(path)
 
        # executescript сам делает commit, поэтому таблицы создаются вне транзакции,
        # а вставки ниже - уже одной транзакцией
        self.conn.executescript(self.SCHEMA)
        with self.conn:
            self.conn.execute(
                "INSERT INTO project (id, name, width, height, created_at) "
                "VALUES (1, ?, ?, ?, ?)",
                (project.name, project.width, project.height,
                 datetime_to_str(project.created_at)),
            )
            self._write_layers(project)
            print("Проект создан")
 
        return project
    
    def load(self, path: str) -> Project:
        """Загрузит проект по пути и вернёт Project. Файл остаётся открытым."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Файл не найден: {path}")
 
        self.close()
        conn = sqlite3.connect(path)
        try:
            row = conn.execute(
                "SELECT name, width, height, created_at FROM project WHERE id = 1"
            ).fetchone()
            if row is None:
                raise ValueError(f"В файле нет данных проекта: {path}")
 
            layers = [
                Layer(name, z_order, bool(visible), bytes_to_image(pixels))
                for name, z_order, visible, pixels in conn.execute(
                    "SELECT name, z_order, visible, pixels "
                    "FROM layers ORDER BY z_order"
                )
            ]
        except Exception:
            conn.close()
            raise
 
        self.path = path
        self.conn = conn
        return Project(row[0], row[1], row[2], str_to_datetime(row[3]), path, layers)

    def save(self, project: Project) -> None:
        """Перезаписывает данные проекта в уже открытом файле."""
        self._require_conn()
 
        with self.conn:
            self.conn.execute(
                "UPDATE project SET name = ?, width = ?, height = ? WHERE id = 1",
                (project.name, project.width, project.height),
            )
            self.conn.execute("DELETE FROM layers")
            self._write_layers(project)
            print("Проект сохранён")

    def close(self) -> None:
        """Закрывает соединение с файлом проекта."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def _require_conn(self) -> None:
        if self.conn is None:
            raise RuntimeError("Файл проекта не открыт: сначала create() или load()")

    def _write_layers(self, project: Project) -> None:
        """Запишет слои в существующий проект."""
        for layer in project.layers:
            self.conn.execute(
                "INSERT INTO layers (name, z_order, visible, pixels) "
                "VALUES (?, ?, ?, ?)",
                (layer.name, layer.z_order, int(layer.visible),
                 image_to_bytes(layer.image))),  # PNG-байты