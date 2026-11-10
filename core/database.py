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
        created_at TEXT    NOT NULL,
        max_undo_steps INTEGER NOT NULL DEFAULT 20,
        history_cursor INTEGER NOT NULL DEFAULT 0
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

    CREATE TABLE action_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        command_type TEXT NOT NULL,
        before_state BLOB NOT NULL,
        after_state BLOB NOT NULL,
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
            self._ensure_history_schema(conn)
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
            self._ensure_history_schema(conn)
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

    def save_as(self, path: str, project: Project) -> Project:
        """Сохраняет проект в новый SQLite-файл и переключает БД на него."""
        if os.path.exists(path):
            raise FileExistsError(f"Файл уже существует: {path}")

        self.save(project)
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
        """Мигрирует старые проекты и создаёт таблицу истории."""
        columns = {row[1] for row in conn.execute("PRAGMA table_info(project)")}
        if "max_undo_steps" not in columns:
            conn.execute("ALTER TABLE project ADD COLUMN max_undo_steps INTEGER NOT NULL DEFAULT 20")
        if "history_cursor" not in columns:
            conn.execute("ALTER TABLE project ADD COLUMN history_cursor INTEGER NOT NULL DEFAULT 0")
        conn.execute("""CREATE TABLE IF NOT EXISTS action_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, command_type TEXT NOT NULL,
            before_state BLOB NOT NULL, after_state BLOB NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")

    def record_history(self, project: Project, before_state: bytes, after_state: bytes, command_type: str) -> None:
        """Сохраняет проект и новую команду в одной транзакции."""
        self._require_conn()
        with self.conn:
            self.conn.execute("UPDATE project SET name=?, width=?, height=? WHERE id=1", (project.name, project.width, project.height))
            self.conn.execute("DELETE FROM layers")
            self._write_layers(project, self.conn)
            cursor, limit = self.conn.execute("SELECT history_cursor, max_undo_steps FROM project WHERE id=1").fetchone()
            self.conn.execute("DELETE FROM action_history WHERE id > ?", (cursor,))
            self.conn.execute("INSERT INTO action_history(command_type,before_state,after_state) VALUES(?,?,?)", (command_type, sqlite3.Binary(before_state), sqlite3.Binary(after_state)))
            self.conn.execute("UPDATE project SET history_cursor=last_insert_rowid() WHERE id=1")
            self.conn.execute("DELETE FROM action_history WHERE id NOT IN (SELECT id FROM action_history ORDER BY id DESC LIMIT ?)", (max(1, int(limit)),))

    def get_history_entry(self, direction: str) -> dict | None:
        """Возвращает соседнюю команду, не изменяя курсор."""
        self._require_conn()
        cursor = self.conn.execute("SELECT history_cursor FROM project WHERE id=1").fetchone()[0]
        if direction == "undo":
            row = self.conn.execute("SELECT id,before_state FROM action_history WHERE id=?", (cursor,)).fetchone()
            if row is None: return None
            previous = self.conn.execute("SELECT COALESCE(MAX(id),0) FROM action_history WHERE id < ?", (cursor,)).fetchone()[0]
            return {"id": row[0], "before_state": row[1], "previous_cursor": previous}
        if direction == "redo":
            row = self.conn.execute("SELECT id,after_state FROM action_history WHERE id > ? ORDER BY id LIMIT 1", (cursor,)).fetchone()
            return None if row is None else {"id": row[0], "after_state": row[1]}
        raise ValueError("direction должен быть 'undo' или 'redo'")

    def restore_history_state(self, project: Project, cursor: int) -> None:
        """Сохраняет восстановленное состояние и курсор одной транзакцией."""
        self._require_conn()
        with self.conn:
            self.conn.execute("UPDATE project SET name=?,width=?,height=?,history_cursor=? WHERE id=1", (project.name, project.width, project.height, int(cursor)))
            self.conn.execute("DELETE FROM layers")
            self._write_layers(project, self.conn)

    def history_status(self) -> tuple[bool, bool]:
        self._require_conn()
        cursor = self.conn.execute("SELECT history_cursor FROM project WHERE id=1").fetchone()[0]
        undo = self.conn.execute("SELECT 1 FROM action_history WHERE id=?", (cursor,)).fetchone() is not None
        redo = self.conn.execute("SELECT 1 FROM action_history WHERE id>? LIMIT 1", (cursor,)).fetchone() is not None
        return undo, redo

    def set_history_limit(self, limit: int) -> None:
        self._require_conn()
        limit = max(1, int(limit))
        with self.conn:
            self.conn.execute("UPDATE project SET max_undo_steps=? WHERE id=1", (limit,))
            self.conn.execute("DELETE FROM action_history WHERE id NOT IN (SELECT id FROM action_history ORDER BY id DESC LIMIT ?)", (limit,))
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
