"""Загрузка, нормализация и сохранение пользовательских настроек SQPaint."""
import json
import os
import shutil
from pathlib import Path


SETTINGS_FILE = "settings.json"
SETTINGS_FILE_FOLDER = "sqpaint"
DEFAULT_SETTINGS = {
    "language": "ru",
    "autosave": {"interval_minutes": 5},
    "view": {
        "theme": "dark",
        "layer_panel_visible": True,
        "toolbar_visible": True,
        "zoom_control_visible": True,
        "show_welcome": True,
    },
}


def get_settings_path() -> str:
    """Возвращает путь к JSON-файлу настроек и переносит старую конфигурацию."""
    root = Path(__file__).resolve().parent.parent
    path = root / SETTINGS_FILE

    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:
        base = os.getenv("XDG_CONFIG_HOME") or str(Path.home() / ".config")

    legacy_path = Path(base) / SETTINGS_FILE_FOLDER / SETTINGS_FILE
    if not path.exists() and legacy_path.is_file():
        try:
            shutil.copy2(legacy_path, path)
        except OSError:
            pass

    return str(path)


def normalize(path: str) -> str:
    """Преобразует путь к файлу в нормализованный абсолютный путь."""
    return os.path.normcase(os.path.abspath(path))


def load_data() -> dict:
    """Загружает настройки, объединяет их со значениями по умолчанию и проверяет параметры."""
    path = get_settings_path()

    try:
        with open(path, "r", encoding="utf-8") as file:
            loaded = json.load(file)
            data = loaded if isinstance(loaded, dict) else {}
    except (OSError, json.JSONDecodeError):
        data = {}

    result = json.loads(json.dumps(DEFAULT_SETTINGS))
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key].update(value)
        else:
            result[key] = value

    try:
        interval = int(result["autosave"].get("interval_minutes", 5))
    except (TypeError, ValueError):
        interval = 5

    result["autosave"]["interval_minutes"] = min(120, max(1, interval))
    return result


def save_data(data: dict) -> None:
    """Атомарно сохраняет настройки в JSON-файл."""
    path = get_settings_path()
    temp_path = path + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        file.flush()
        os.fsync(file.fileno())

    os.replace(temp_path, path)
