"""Централизованное определение путей приложения и пользовательских данных
SQPaint.
"""
import sys
from pathlib import Path


def get_app_dir() -> Path:
    """Возвращает каталог приложения: рядом с EXE или в корне исходного
    проекта.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def get_data_dir() -> Path:
    """Возвращает каталог пользовательских данных приложения."""
    return get_app_dir()


def ensure_app_dirs() -> None:
    """Создаёт каталог пользовательских данных, если он отсутствует."""
    get_data_dir().mkdir(parents=True, exist_ok=True)


def get_settings_path() -> Path:
    """Возвращает путь к файлу пользовательских настроек."""
    return get_data_dir() / "settings.json"


def get_recent_projects_path() -> Path:
    """Возвращает путь к файлу списка недавно открытых проектов."""
    return get_data_dir() / "recent_projects.csv"


def get_resource_path(relative_path: str) -> Path:
    """Возвращает путь к ресурсу, учитывая временный каталог PyInstaller."""
    if getattr(sys, "frozen", False):
        base_path = Path(getattr(sys, "_MEIPASS", get_app_dir()))
    else:
        base_path = get_app_dir()

    return base_path / relative_path
