from core.models import Project
from core.time_utils import *
import csv
import os
import shutil
from pathlib import Path
from datetime import datetime


RECENT_PROJECTS = "recent_projects.csv"


def _get_csv_path() -> str:
    """Возвращает CSV в корне проекта, перенося старый файл при первом запуске."""
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
    # D:/Proj/a.sqlite и d:\\proj\\A.sqlite -> один и тот же ключ
    return os.path.normcase(os.path.abspath(path))


def _read_entries():
    """Читает csv, выкидывает дубли и битые строки.
    Возвращает список (имя, путь, дата), самые свежие первыми."""
    unique = {}
    with open(_get_csv_path(), "r", encoding="utf-8", newline="") as f:
        for row in csv.reader(f, delimiter=","):
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
    return sorted(unique.values(), key=lambda e: e[2], reverse=True)


def get_recent_projects():
    return tuple(_read_entries())


def add_recent_project(project: Project):
    key = _normalize(project.get_path())
    entries = [e for e in _read_entries() if _normalize(e[1]) != key]
    entries.append((project.get_name(), project.get_path(), datetime.now()))

    with open(_get_csv_path(), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=",")
        for name, path, date in entries:
            writer.writerow((name, path, datetime_to_str(date)))
