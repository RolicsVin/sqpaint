from core.models import Project
from core.time_utils import *
import csv
import os
from datetime import datetime


RECENT_PROJECTS = 'recent_projects.csv'
RECENT_PROJECTS_FOLDER = 'sqpaint'


def get_recent_projects() -> tuple[tuple]:
    if not os.path.exists(os.path.join(os.getenv('LOCALAPPDATA'), RECENT_PROJECTS_FOLDER)):
        os.mkdir(os.path.join(os.getenv('LOCALAPPDATA'), RECENT_PROJECTS_FOLDER))
    if not os.path.exists(os.path.join(os.getenv('LOCALAPPDATA'), RECENT_PROJECTS_FOLDER)):
        # Создаём csv файл
        with open(os.path.join(os.getenv('LOCALAPPDATA'), RECENT_PROJECTS_FOLDER, RECENT_PROJECTS),
                  mode='w',
                  encoding='utf8',
                  newline='') as f:
                  pass
    
    with open(os.path.join(os.getenv('LOCALAPPDATA'), RECENT_PROJECTS_FOLDER, RECENT_PROJECTS)
              , mode='r', encoding='utf8', newline='') as f:
         arr = []
         reader = csv.reader(f, delimiter=',')

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