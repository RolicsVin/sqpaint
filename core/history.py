"""Управление историей изменений документа в оперативной памяти.

Снимки используют QImage.copy(): Qt применяет implicit sharing, поэтому копирование
изображения не сериализует пиксели и не обращается к диску. Сериализация выполняется
только при явном сохранении проекта.
"""
import base64
import json
import zlib
from datetime import datetime

from PyQt6.QtGui import QImage

from core.models import Layer


class HistoryManager:
    """Хранит ограниченную линейную историю состояний документа в RAM."""

    def __init__(self, database=None, limit: int = 20):
        self.database = database  # Оставлено для совместимости конструктора контроллера.
        self.project = None
        self.limit = max(1, int(limit))
        self._states: list[dict] = []
        self._labels: list[str] = []
        self._cursor = 0

    def set_project(self, project, saved_history=None) -> None:
        self.project = project
        self._states = []
        self._labels = []
        self._cursor = 0

        if saved_history:
            self.limit = max(1, int(saved_history.get("limit", self.limit)))
            records = saved_history.get("records", [])
            if records:
                self._states.append(self._decode_state(records[0]["before_state"]))
                for record in records:
                    self._labels.append(record["command_type"])
                    self._states.append(self._decode_state(record["after_state"]))
                self._cursor = max(0, min(int(saved_history.get("cursor", len(records))), len(records)))
                return

        self._states = [self.capture()]

    def capture(self) -> dict:
        if self.project is None:
            raise RuntimeError("Проект для истории не открыт.")
        return {
            "name": self.project.name,
            "width": self.project.width,
            "height": self.project.height,
            "created_at": self.project.created_at,
            "layers": [
                {
                    "name": layer.name,
                    "z_order": layer.z_order,
                    "visible": layer.visible,
                    "image": layer.image.copy(),
                }
                for layer in self.project.layers
            ],
        }

    @staticmethod
    def _same_state(left: dict, right: dict) -> bool:
        if (
            left["name"] != right["name"]
            or left["width"] != right["width"]
            or left["height"] != right["height"]
            or left["created_at"] != right["created_at"]
            or len(left["layers"]) != len(right["layers"])
        ):
            return False
        for a, b in zip(left["layers"], right["layers"]):
            if (
                a["name"] != b["name"]
                or a["z_order"] != b["z_order"]
                or a["visible"] != b["visible"]
                or a["image"] != b["image"]
            ):
                return False
        return True

    def commit(self, before: dict, label: str) -> bool:
        if self.project is None or before is None:
            return False
        after = self.capture()
        if self._same_state(before, after):
            return False

        # Отбрасываем ветку Redo при создании нового действия после Undo.
        self._states = self._states[:self._cursor + 1]
        self._labels = self._labels[:self._cursor]
        self._states.append(after)
        self._labels.append(str(label))
        self._cursor += 1

        if len(self._labels) > self.limit:
            overflow = len(self._labels) - self.limit
            del self._labels[:overflow]
            del self._states[:overflow]
            self._cursor = max(0, self._cursor - overflow)
        return True

    def undo(self) -> bool:
        if self.project is None or self._cursor <= 0:
            return False
        self._cursor -= 1
        self._apply_state(self._states[self._cursor])
        return True

    def redo(self) -> bool:
        if self.project is None or self._cursor >= len(self._states) - 1:
            return False
        self._cursor += 1
        self._apply_state(self._states[self._cursor])
        return True

    def _apply_state(self, state: dict) -> None:
        self.project.name = state["name"]
        self.project.width = state["width"]
        self.project.height = state["height"]
        self.project.created_at = state["created_at"]
        self.project.layers = [
            Layer(
                item["name"],
                int(item["z_order"]),
                bool(item["visible"]),
                item["image"].copy(),
            )
            for item in state["layers"]
        ]

    @staticmethod
    def _encode_state(state: dict) -> bytes:
        serialized = {
            "name": state["name"],
            "width": state["width"],
            "height": state["height"],
            "created_at": state["created_at"].isoformat(),
            "layers": [],
        }
        for layer in state["layers"]:
            image = layer["image"]
            # PNG-кодирование выполняется только при явном сохранении.
            from PyQt6.QtCore import QBuffer, QIODevice
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")
            serialized["layers"].append({
                "name": layer["name"],
                "z_order": layer["z_order"],
                "visible": layer["visible"],
                "pixels": base64.b64encode(bytes(buffer.data())).decode("ascii"),
            })
            buffer.close()
        raw = json.dumps(serialized, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return zlib.compress(raw, level=6)

    @staticmethod
    def _decode_state(payload: bytes) -> dict:
        from PyQt6.QtCore import QByteArray
        state = json.loads(zlib.decompress(payload).decode("utf-8"))
        layers = []
        for item in state["layers"]:
            image = QImage.fromData(QByteArray(base64.b64decode(item["pixels"])), "PNG")
            if image.isNull():
                raise ValueError("Не удалось восстановить изображение из истории проекта.")
            layers.append({
                "name": item["name"],
                "z_order": int(item["z_order"]),
                "visible": bool(item["visible"]),
                "image": image,
            })
        return {
            "name": state["name"],
            "width": int(state["width"]),
            "height": int(state["height"]),
            "created_at": datetime.fromisoformat(state["created_at"]),
            "layers": layers,
        }

    def export_for_save(self) -> dict:
        """Сериализует историю для записи в SQLite при явном сохранении."""
        if not self._states:
            return {"records": [], "cursor": 0, "limit": self.limit}
        records = []
        for index, label in enumerate(self._labels):
            records.append({
                "command_type": label,
                "before_state": self._encode_state(self._states[index]),
                "after_state": self._encode_state(self._states[index + 1]),
            })
        return {"records": records, "cursor": self._cursor, "limit": self.limit}

    def status(self) -> tuple[bool, bool]:
        return self._cursor > 0, self._cursor < len(self._states) - 1
