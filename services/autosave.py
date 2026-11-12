"""Создание и ротация резервных копий файлов проектов SQPaint."""
import shutil
from datetime import datetime
from pathlib import Path


MAX_BACKUPS = 5
BACKUP_SUFFIX = ".autosave"


def create_backup(
    project_path: str,
    max_backups: int = MAX_BACKUPS,
) -> Path:
    """Создаёт копию SQLite-файла и удаляет резервные копии сверх заданного лимита."""
    source = Path(project_path)
    if not source.is_file():
        raise FileNotFoundError(f"Файл проекта не найден: {source}")

    backup = source.with_name(
        f"{source.stem}{BACKUP_SUFFIX}_{datetime.now():%Y%m%d_%H%M%S_%f}{source.suffix}"
    )
    shutil.copy2(source, backup)

    backups = sorted(
        source.parent.glob(f"{source.stem}{BACKUP_SUFFIX}_*{source.suffix}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for old_backup in backups[max(1, int(max_backups)):]:
        old_backup.unlink(missing_ok=True)

    return backup
