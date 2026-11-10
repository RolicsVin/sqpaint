"""Сервис сериализации и управления постоянной историей проекта."""
import base64
import json
import zlib
from datetime import datetime

from core.image_utils import bytes_to_image, image_to_bytes
from core.models import Layer, Project


class HistoryManager:
    """Хранит ограниченную линейную историю снимков документа в SQLite."""

    def __init__(self, database):
        self.database = database
        self.project = None

    def set_project(self, project: Project) -> None:
        self.project = project

    def capture(self) -> bytes:
        if self.project is None:
            raise RuntimeError("Проект для истории не открыт.")
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
        if self.project is None:
            return False
        after = self.capture()
        if before == after:
            return False
        self.database.record_history(self.project, before, after, label)
        return True

    def undo(self) -> bool:
        entry = self.database.get_history_entry("undo")
        if entry is None:
            return False
        self._restore(entry["state"], entry["cursor"])
        return True

    def redo(self) -> bool:
        entry = self.database.get_history_entry("redo")
        if entry is None:
            return False
        self._restore(entry["state"], entry["cursor"])
        return True

    def _restore(self, payload: bytes, cursor: int) -> None:
        state = json.loads(zlib.decompress(payload).decode("utf-8"))
        project = self.project
        layers = [
            Layer(
                item["name"], int(item["z_order"]), bool(item["visible"]),
                bytes_to_image(base64.b64decode(item["pixels"])),
            )
            for item in state["layers"]
        ]
        restored = Project(
            state["name"], int(state["width"]), int(state["height"]),
            datetime.fromisoformat(state["created_at"]), project.path, layers,
        )
        self.database.restore_history_state(restored, cursor)
        project.name = restored.name
        project.width = restored.width
        project.height = restored.height
        project.created_at = restored.created_at
        project.layers = restored.layers

    def status(self) -> tuple[bool, bool]:
        return self.database.history_status()
