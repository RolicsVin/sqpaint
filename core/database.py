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
        self._loaded_history: dict | None = None

    def create(self, path: str, name: str, width: int, height: int, supports_transparency: bool = True, max_undo_steps: int = 10) -> Project:
        """Создаёт новый файл проекта и возвращает Project."""
        if os.path.exists(path):
            raise FileExistsError(f"Файл уже существует: {path}")

        project = Project(name, width, height, datetime.now(), path, [], bool(supports_transparency), max(1, int(max_undo_steps)))

        self.close()
        conn = sqlite3.connect(path)
        try:
            conn.executescript(self.SCHEMA)
            self._ensure_history_schema(conn)
            with conn:
                conn.execute(
                    "INSERT INTO project "
                    "(id, name, width, height, created_at, supports_transparency, max_undo_steps) "
                    "VALUES (1, ?, ?, ?, ?, ?, ?)",
                    (
                        project.name, project.width, project.height,
                        datetime_to_str(project.created_at),
                        int(project.supports_transparency), project.max_undo_steps,
                    ),
                )
                self._write_layers(project, conn)
        except Exception:
            conn.close()
            raise

        self.path = path
        self.conn = conn
        self._loaded_history = None
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

            project_columns = {item[1] for item in conn.execute("PRAGMA table_info(project)")}
            supports_transparency = bool(conn.execute("SELECT supports_transparency FROM project WHERE id=1").fetchone()[0]) if "supports_transparency" in project_columns else True
            project_history_limit = int(conn.execute("SELECT max_undo_steps FROM project WHERE id=1").fetchone()[0]) if "max_undo_steps" in project_columns else 10
            project = Project(
                row[0], width, height, str_to_datetime(row[3]), path, layers,
                supports_transparency, max(1, project_history_limit),
            )

            # Читаем историю без изменения файла при открытии проекта.
            loaded_history = None
            tables = {
                item[0] for item in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            columns = {item[1] for item in conn.execute("PRAGMA table_info(project)")}
            if "action_history" in tables and "history_cursor" in columns:
                history_rows = conn.execute(
                    "SELECT command_type, before_state, after_state "
                    "FROM action_history ORDER BY id"
                ).fetchall()
                cursor_value = conn.execute(
                    "SELECT history_cursor FROM project WHERE id=1"
                ).fetchone()[0]
                max_steps = (
                    conn.execute("SELECT max_undo_steps FROM project WHERE id=1").fetchone()[0]
                    if "max_undo_steps" in columns else 10
                )
                cursor_index = sum(
                    1 for item in conn.execute("SELECT id FROM action_history ORDER BY id")
                    if item[0] <= int(cursor_value)
                )
                loaded_history = {
                    "records": [
                        {
                            "command_type": item[0],
                            "before_state": bytes(item[1]),
                            "after_state": bytes(item[2]),
                        }
                        for item in history_rows
                    ],
                    "cursor": cursor_index,
                    "limit": int(max_steps),
                }
        except Exception:
            conn.close()
            raise

        self.close()
        self.path = path
        self.conn = conn
        self._loaded_history = loaded_history
        self._ensure_logs_schema(conn)
        return project

    def save(self, project: Project, history_data: dict | None = None) -> None:
        """Сохраняет документ и историю только по явной команде пользователя."""
        self._require_conn()
        self._ensure_history_schema(self.conn)
        history_data = history_data or {"records": [], "cursor": 0, "limit": getattr(project, "max_undo_steps", 10)}

        with self.conn:
            self.conn.execute(
                "UPDATE project SET name=?, width=?, height=?, history_cursor=?, max_undo_steps=?, supports_transparency=? WHERE id=1",
                (
                    project.name, project.width, project.height,
                    int(history_data.get("cursor", 0)),
                    max(1, int(history_data.get("limit", getattr(project, "max_undo_steps", 10)))),
                    int(bool(project.supports_transparency)),
                ),
            )
            self.conn.execute("DELETE FROM layers")
            self._write_layers(project, self.conn)
            self.conn.execute("DELETE FROM action_history")
            for index, record in enumerate(history_data.get("records", []), start=1):
                self.conn.execute(
                    "INSERT INTO action_history(id,command_type,before_state,after_state) VALUES(?,?,?,?)",
                    (
                        index,
                        record["command_type"],
                        sqlite3.Binary(record["before_state"]),
                        sqlite3.Binary(record["after_state"]),
                    ),
                )
        self._loaded_history = history_data

    @staticmethod
    def _ensure_logs_schema(conn: sqlite3.Connection) -> None:
        """Создаёт таблицу журналирования в старых проектах."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    def add_log(self, message: str) -> None:
        """Добавляет запись в журнал открытого проекта."""
        self._require_conn()
        self._ensure_logs_schema(self.conn)
        with self.conn:
            self.conn.execute(
                "INSERT INTO logs (log) VALUES (?)",
                (str(message),),
            )

    def load_history(self) -> dict | None:
        """Возвращает историю, прочитанную при открытии текущего проекта."""
        return self._loaded_history

    def save_as(self, path: str, project: Project, history_data: dict | None = None) -> Project:
        """Сохраняет проект в новый SQLite-файл и переключает БД на него."""
        if os.path.exists(path):
            raise FileExistsError(f"Файл уже существует: {path}")

        self.save(project, history_data)
        destination = sqlite3.connect(path)
        try:
            self._require_conn()
            self.conn.backup(destination)
        except Exception:
            destination.close()
            try:
                os.remove(path)
            except OSError:
                pass
            raise
        else:
            destination.close()

        return self.load(path)


    @staticmethod
    def _ensure_history_schema(conn: sqlite3.Connection) -> None:
        """Добавляет таблицы истории в новые и уже существующие проекты."""
        columns = {row[1] for row in conn.execute("PRAGMA table_info(project)")}
        if "max_undo_steps" not in columns:
            conn.execute(
                "ALTER TABLE project ADD COLUMN max_undo_steps INTEGER NOT NULL DEFAULT 10"
            )
        if "supports_transparency" not in columns:
            conn.execute(
                "ALTER TABLE project ADD COLUMN supports_transparency INTEGER NOT NULL DEFAULT 1"
            )
        if "history_cursor" not in columns:
            conn.execute(
                "ALTER TABLE project ADD COLUMN history_cursor INTEGER NOT NULL DEFAULT 0"
            )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS action_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_type TEXT NOT NULL,
                before_state BLOB NOT NULL,
                after_state BLOB NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def close(self) -> None:
        """Закрывает соединение с файлом проекта."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None
        self.path = None
        self._loaded_history = None

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
