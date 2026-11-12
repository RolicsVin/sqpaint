"""Хранение списка недавно открытых проектов SQPaint в CSV-файле."""
import csv
import os
import shutil
from datetime import datetime
from pathlib import Path

from core.models import Project
from core.time_utils import datetime_to_str, str_to_datetime


RECENT_PROJECTS = "recent_projects.csv"


def _get_csv_path() -> str:
    """Возвращает путь к CSV и переносит файл из старого расположения при необходимости."""
    path = Path(__file__).resolve().parent.parent / RECENT_PROJECTS

    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        legacy_path = Path(local_app_data) / "sqpaint" / RECENT_PROJECTS
        if not path.exists() and legacy_path.is_file():
            try:
                shutil.copy2(legacy_path, path)
            except OSError:
                pass

    if not path.exists():
        path.touch()

    return str(path)


def _normalize(path: str) -> str:
    """Нормализует путь для сравнения файлов с учётом ОС."""
    return os.path.normcase(os.path.abspath(path))


def _read_entries() -> list[tuple[str, str, datetime]]:
    """Читает записи CSV, удаляет дубликаты и возвращает проекты от новых к старым."""
    unique = {}

    with open(_get_csv_path(), "r", encoding="utf-8", newline="") as file:
        for row in csv.reader(file, delimiter=","):
            if len(row) < 3:
                continue

            name, project_path, date_str = row[:3]
            try:
                date = str_to_datetime(date_str)
            except (ValueError, TypeError):
                continue

            key = _normalize(project_path)
            if key not in unique or date > unique[key][2]:
                unique[key] = (name, project_path, date)

    return sorted(unique.values(), key=lambda entry: entry[2], reverse=True)


def get_recent_projects() -> tuple[tuple[str, str, datetime], ...]:
    """Возвращает неизменяемый список недавно открытых проектов."""
    return tuple(_read_entries())


def add_recent_project(project: Project) -> None:
    """Добавляет проект в начало списка, заменяя запись с тем же путём."""
    key = _normalize(project.get_path())
    entries = [
        entry for entry in _read_entries()
        if _normalize(entry[1]) != key
    ]
    entries.append((project.get_name(), project.get_path(), datetime.now()))

    with open(_get_csv_path(), "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, delimiter=",")
        for name, path, date in entries:
            writer.writerow((name, path, datetime_to_str(date)))
