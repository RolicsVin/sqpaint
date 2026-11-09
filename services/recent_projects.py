from core.models import Project
from core.time_utils import *
import csv
import os
from datetime import datetime


RECENT_PROJECTS = 'recent_projects.csv'
RECENT_PROJECTS_FOLDER = 'sqpaint'


def _get_csv_path():
    folder = os.path.join(os.getenv('LOCALAPPDATA'), RECENT_PROJECTS_FOLDER)
    os.makedirs(folder, exist_ok=True)           # создаст папку, если её нет
    path = os.path.join(folder, RECENT_PROJECTS)
    if not os.path.exists(path):                 # создаст пустой файл, если его нет
        with open(path, 'w', encoding='utf-8', newline=''):
            pass
    return path


def _normalize(path: str) -> str:
    # D:/Proj/a.sqlite и d:\proj\A.sqlite -> один и тот же ключ
    return os.path.normcase(os.path.abspath(path))


def _read_entries():
    """Читает csv, выкидывает дубли и битые строки.
    Возвращает список (имя, путь, дата), самые свежие первыми."""
    unique = {}
    with open(_get_csv_path(), 'r', encoding='utf-8', newline='') as f:
        for row in csv.reader(f, delimiter=','):
            if len(row) < 3: # пустая или битая строка
                continue
            name, project_path, date_str = row[:3]
            try:
                date = str_to_datetime(date_str)
            except (ValueError, TypeError):
                continue
            key = _normalize(project_path)
            # при повторе оставляем запись с более поздней датой
            if key not in unique or date > unique[key][2]:
                unique[key] = (name, project_path, date)
    return sorted(unique.values(), key=lambda e: e[2], reverse=True)


def get_recent_projects():
    return tuple(_read_entries())


def add_recent_project(project: Project):
    key = _normalize(project.get_path())
    # убираем старую запись об этом проекте, если она была
    entries = [e for e in _read_entries() if _normalize(e[1]) != key]
    entries.append((project.get_name(), project.get_path(), datetime.now()))

    with open(_get_csv_path(), 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=',')
        for name, path, date in entries:
            writer.writerow((name, path, datetime_to_str(date)))