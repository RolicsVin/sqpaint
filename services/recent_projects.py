from core.models import Project
from core.time_utils import *
import csv
import os
from datetime import datetime


RECENT_PROJECTS = 'recent_projects.csv'
RECENT_PROJECTS_FOLDER = 'sqpaint'


def get_recent_project() -> tuple[tuple[str, str, datetime]]:

    if not os.path.exists(os.path.join(os.getenv('LOCALAPPDATA'), RECENT_PROJECTS_FOLDER)):
        os.mkdir(os.path.join(os.getenv('LOCALAPPDATA'), RECENT_PROJECTS_FOLDER))
    
    with open(os.path.join(os.getenv('LOCALAPPDATA'), RECENT_PROJECTS_FOLDER, RECENT_PROJECTS)
              , mode='r', encoding='utf8', newline='') as f:
         reader = csv.reader(f)
         return tuple(reader)
    


def add_recent_project(project: Project):
    with open(os.path.join(os.getenv('LOCALAPPDATA'), RECENT_PROJECTS_FOLDER, RECENT_PROJECTS)
                  , mode='a', encoding='utf8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow((project.get_name(),
                             project.get_path(),
                             datetime_to_str(datetime.now())))
