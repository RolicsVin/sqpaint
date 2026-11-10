"""Постоянная история Undo/Redo для SQLite-проектов."""
import base64
import json
import zlib
from datetime import datetime

from core.image_utils import bytes_to_image, image_to_bytes
from core.models import Layer, Project


class HistoryManager:
    """Управляет снимками состояния проекта и их восстановлением.

    Снимки сжимаются и хранятся в SQLite. Количество операций ограничивает
    ProjectDatabase; после перезапуска история восстанавливается автоматически.
    """

    def __init__(self, database, project: Project):
        self.database = database
        self.project = project

    def begin(self) -> bytes:
        """Создаёт сжатый снимок состояния перед изменением."""
        state = {
            "name": self.project.name,
            "width": self.project.width,
            "height": self.project.height,
            "created_at": self.project.created_at.isoformat(),
            "layers": [
                {
                    "name": layer.name,
                    "z_order": layer.z_order,
                    "visible": layer.visible,
                    "pixels": base64.b64encode(image_to_bytes(layer.image)).decode("ascii"),
                }
                for layer in self.project.layers
            ],
        }
        raw = json.dumps(state, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return zlib.compress(raw, level=6)

    def commit(self, before: bytes, label: str) -> bool:
        """Фиксирует изменение и одновременно сохраняет проект."""
        after = self.begin()
        if before == after:
            return False
        self.database.record_history(self.project, before, after, label)
        return True

    @staticmethod
    def _decode(payload: bytes, path: str) -> Project:
        state = json.loads(zlib.decompress(payload).decode("utf-8"))
        layers = [
            Layer(
                item["name"],
                int(item["z_order"]),
                bool(item["visible"]),
                bytes_to_image(base64.b64decode(item["pixels"])),
            )
            for item in state["layers"]
        ]
        return Project(
            state["name"],
            int(state["width"]),
            int(state["height"]),
            datetime.fromisoformat(state["created_at"]),
            path,
            layers,
        )

    def _restore(self, payload: bytes, cursor: int) -> None:
        restored = self._decode(payload, self.project.path)
        # Сначала сохраняем восстановленное состояние и курсор транзакционно.
        self.database.restore_history_state(restored, cursor)
        self.project.name = restored.name
        self.project.width = restored.width
        self.project.height = restored.height
        self.project.created_at = restored.created_at
        self.project.layers = restored.layers

    def undo(self) -> bool:
        entry = self.database.get_history_entry("undo")
        if entry is None:
            return False
        self._restore(entry["before_state"], entry["previous_cursor"])
        return True

    def redo(self) -> bool:
        entry = self.database.get_history_entry("redo")
        if entry is None:
            return False
        self._restore(entry["after_state"], entry["id"])
        return True

    def status(self) -> tuple[bool, bool]:
        return self.database.history_status()
