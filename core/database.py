"""В этом модуле хранятся классы для работы с SQLite."""
import os
import sqlite3
from datetime import datetime

from core.image_utils import bytes_to_image, image_to_bytes
from core.models import Layer, Project
from core.time_utils import datetime_to_str, str_to_datetime


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
        conn = sqlite3.connect(path)
        try:
            conn.executescript(self.SCHEMA)
            with conn:
                conn.execute(
                    "INSERT INTO project (id, name, width, height, created_at) "
                    "VALUES (1, ?, ?, ?, ?)",
                    (project.name, project.width, project.height,
                     datetime_to_str(project.created_at)),
                )
                self._write_layers(project, conn)
        except Exception:
            conn.close()
            raise

        self.path = path
        self.conn = conn
        return project

    def load(self, path: str) -> Project:
        """Загружает проект. Текущее соединение заменяется только после успеха."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Файл не найден: {path}")

        # Сначала проверяем и читаем новый файл. Если он не подходит,
        # текущее соединение и открытый в интерфейсе проект остаются нетронутыми.
        conn = sqlite3.connect(path)
        try:
            row = conn.execute(
                "SELECT name, width, height, created_at FROM project WHERE id = 1"
            ).fetchone()
            if row is None:
                raise ValueError("В выбранном файле отсутствуют данные проекта SQPaint.")

            width, height = int(row[1]), int(row[2])
            if width <= 0 or height <= 0:
                raise ValueError("У проекта указаны некорректные размеры холста.")

            layers = [
                Layer(name, z_order, bool(visible), bytes_to_image(pixels))
                for name, z_order, visible, pixels in conn.execute(
                    "SELECT name, z_order, visible, pixels "
                    "FROM layers ORDER BY z_order"
                )
            ]

            project = Project(
                row[0],
                width,
                height,
                str_to_datetime(row[3]),
                path,
                layers,
            )
        except Exception:
            conn.close()
            raise

        self.close()
        self.path = path
        self.conn = conn
        return project

    def save(self, project: Project) -> None:
        """Перезаписывает данные проекта в уже открытом файле."""
        self._require_conn()

        with self.conn:
            self.conn.execute(
                "UPDATE project SET name = ?, width = ?, height = ? WHERE id = 1",
                (project.name, project.width, project.height),
            )
            self.conn.execute("DELETE FROM layers")
            self._write_layers(project, self.conn)

    def close(self) -> None:
        """Закрывает соединение с файлом проекта."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
        self.path = None

    def _require_conn(self) -> None:
        if self.conn is None:
            raise RuntimeError("Файл проекта не открыт: сначала create() или load()")

    @staticmethod
    def _write_layers(project: Project, conn: sqlite3.Connection) -> None:
        """Записывает слои проекта в SQLite."""
        for layer in project.layers:
            conn.execute(
                "INSERT INTO layers (name, z_order, visible, pixels) "
                "VALUES (?, ?, ?, ?)",
                (
                    layer.name,
                    layer.z_order,
                    int(layer.visible),
                    image_to_bytes(layer.image),
                ),
            )
