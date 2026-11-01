"""Модуль для работы с временем."""
from datetime import datetime


def str_to_datetime(date_str: str) -> datetime:
    """Преобразует строку dd.mm.yyyy hh.mm в datetime."""
    return datetime.strptime(date_str, "%d.%m.%Y %H.%M")


def datetime_to_str(date: datetime) -> str:
    """Преобразует datetime в строку dd.mm.yyyy hh.mm."""
    return date.strftime("%d.%m.%Y %H.%M")