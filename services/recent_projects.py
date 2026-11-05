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


def get_recent_projects():
    path = _get_csv_path()
    with open(path, 'r', encoding='utf-8', newline='') as f:
         reader = csv.reader(f, delimiter=',')
         arr = []

         for row in reader:
              element = (row[0], row[1], str_to_datetime(row[2]))
              arr.append(element)
        
         return tuple(arr)


def add_recent_project(project: Project):
    with open(os.path.join(os.getenv('LOCALAPPDATA'), RECENT_PROJECTS_FOLDER, RECENT_PROJECTS)
                  , mode='a', encoding='utf8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow((project.get_name(),
                             project.get_path(),
                             datetime_to_str(datetime.now())))