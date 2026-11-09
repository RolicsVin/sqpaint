import json
import os

SETTINGS_FILE = 'settings.json'
SETTINGS_FILE_FOLDER = 'sqpaint'


def get_settings_path() -> str:
    folder = os.path.join(os.getenv('LOCALAPPDATA'), SETTINGS_FILE_FOLDER)

    os.makedirs(folder, exist_ok=True) # создаст папку, если её нет
    path = os.path.join(folder, SETTINGS_FILE)

    if not os.path.exists(path): # создаст пустой файл, если его нет
        with open(path, 'w', encoding='utf-8'):
            pass
    
    return path


def normalize(path: str) -> str:
    # D:/Proj/a.sqlite и d:\proj\A.sqlite -> один и тот же ключ
    return os.path.normcase(os.path.abspath(path))


def load_data() -> dict:
    path = normalize(get_settings_path())


def save_data() -> None:
    path = normalize(get_settings_path())