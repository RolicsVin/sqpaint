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

    def __init__(self, database=None, limit: int = 10):
        self.database = database  # Оставлено для совместимости конструктора контроллера.
        self.project = None
        self.limit = max(1, int(limit))
        self._states: list[dict] = []
        self._labels: list[str] = []
        self._cursor = 0
        self._saved_state = None

    def set_project(self, project, saved_history=None) -> None:
        self.project = project
        self.limit = max(1, int(getattr(project, "max_undo_steps", 10)))
        self._states = []
        self._labels = []
        self._cursor = 0

        if saved_history:
            self.limit = max(1, int(saved_history.get("limit", self.limit)))
            records = saved_history.get("records", [])
            if records:
                self._states.append(self._decode_state(
                    records[0]["before_state"],
                    project.supports_transparency,
                    project.max_undo_steps,
                ))
                for record in records:
                    self._labels.append(record["command_type"])
                    self._states.append(self._decode_state(
                        record["after_state"],
                        project.supports_transparency,
                        project.max_undo_steps,
                    ))
                self._cursor = max(0, min(int(saved_history.get("cursor", len(records))), len(records)))
                self.mark_saved()
                return

        self._states = [self.capture()]
        self.mark_saved()

    def set_limit(self, limit: int) -> None:
        """Изменяет лимит истории и удаляет самые старые действия при необходимости."""
        self.limit = max(1, int(limit))
        overflow = max(0, len(self._labels) - self.limit)
        if overflow:
            del self._labels[:overflow]
            del self._states[:overflow]
            self._cursor = max(0, self._cursor - overflow)

    def capture(self) -> dict:
        if self.project is None:
            raise RuntimeError("Проект для истории не открыт.")
        return {
            "name": self.project.name,
            "width": self.project.width,
            "height": self.project.height,
            "created_at": self.project.created_at,
            "supports_transparency": self.project.supports_transparency,
            "max_undo_steps": self.project.max_undo_steps,
            "layers": [
                {
                    "name": layer.name,
                    "z_order": layer.z_order,
                    "visible": layer.visible,
                    "image": QImage(layer.image),
                    "cache_key": layer.image.cacheKey(),
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
            or left.get("supports_transparency", True) != right.get("supports_transparency", True)
            or left.get("max_undo_steps", 10) != right.get("max_undo_steps", 10)
            or len(left["layers"]) != len(right["layers"])
        ):
            return False
        for a, b in zip(left["layers"], right["layers"]):
            if (
                a["name"] != b["name"]
                or a["z_order"] != b["z_order"]
                or a["visible"] != b["visible"]
                or a["cache_key"] != b["cache_key"]
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
        self.project.supports_transparency = bool(state.get("supports_transparency", True))
        self.project.max_undo_steps = max(1, int(state.get("max_undo_steps", 10)))
        self.limit = self.project.max_undo_steps
        self.project.layers = [
            Layer(
                item["name"],
                int(item["z_order"]),
                bool(item["visible"]),
                QImage(item["image"]),
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
            "supports_transparency": bool(state.get("supports_transparency", True)),
            "max_undo_steps": int(state.get("max_undo_steps", 10)),
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
    def _decode_state(
        payload: bytes, fallback_transparency: bool = True, fallback_limit: int = 10
    ) -> dict:
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
                "cache_key": image.cacheKey(),
            })
        return {
            "name": state["name"],
            "width": int(state["width"]),
            "height": int(state["height"]),
            "created_at": datetime.fromisoformat(state["created_at"]),
            "supports_transparency": bool(state.get("supports_transparency", fallback_transparency)),
            "max_undo_steps": max(1, int(state.get("max_undo_steps", fallback_limit))),
            "layers": layers,
        }

    def export_for_save(self) -> dict:
        """Сериализует историю для записи в SQLite при явном сохранении."""
        if not self._states:
            return {"records": [], "cursor": 0, "limit": self.limit}
        encoded_states = [self._encode_state(state) for state in self._states]
        records = []
        for index, label in enumerate(self._labels):
            records.append({
                "command_type": label,
                "before_state": encoded_states[index],
                "after_state": encoded_states[index + 1],
            })
        return {"records": records, "cursor": self._cursor, "limit": self.limit}

    def mark_saved(self) -> None:
        """Запоминает снимок истории, соответствующий последнему Save."""
        self._saved_state = (
            self._states[self._cursor]
            if self._states and self.project is not None else None
        )

    def is_dirty(self) -> bool:
        """Проверяет, находится ли курсор на сохранённом состоянии документа."""
        if self.project is None or self._saved_state is None:
            return False
        return self._states[self._cursor] is not self._saved_state

    def status(self) -> tuple[bool, bool]:
        return self._cursor > 0, self._cursor < len(self._states) - 1
