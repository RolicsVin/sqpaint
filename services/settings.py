"""JSON-хранилище пользовательских настроек SQPaint."""
import json
import os
from pathlib import Path

SETTINGS_FILE = "settings.json"
SETTINGS_FILE_FOLDER = "sqpaint"
DEFAULT_SETTINGS = {
    "view": {
        "theme": "dark",
        "layer_panel_visible": True,
        "toolbar_visible": True,
        "zoom_control_visible": True,
        "show_welcome": True,
    }
}


def get_settings_path() -> str:
    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:
        base = os.getenv("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    folder = os.path.join(base, SETTINGS_FILE_FOLDER)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, SETTINGS_FILE)


def normalize(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def load_data() -> dict:
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
    return result


def save_data(data: dict) -> None:
    path = get_settings_path()
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temp_path, path)
