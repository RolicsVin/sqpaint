"""Преобразование дат и времени между строковым и объектным представлениями."""
from datetime import datetime


def str_to_datetime(date_str: str) -> datetime:
    """Преобразует строку формата «дд.мм.гггг чч.мм» в объект datetime."""
    return datetime.strptime(date_str, "%d.%m.%Y %H.%M")


def datetime_to_str(date: datetime) -> str:
    """Преобразует datetime в строку формата «дд.мм.гггг чч.мм»."""
    return date.strftime("%d.%m.%Y %H.%M")
