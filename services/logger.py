"""Централизованное логирование действий SQPaint."""
import logging


class AppLogger:
    """Отправляет события в консоль и в SQLite текущего проекта."""

    def __init__(self, database):
        """Настраивает именованный логгер и обработчик вывода в консоль."""
        self.database = database
        self._logger = logging.getLogger("SQPaint")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        has_handler = any(
            getattr(handler, "_sqpaint_handler", False)
            for handler in self._logger.handlers
        )
        if not has_handler:
            handler = logging.StreamHandler()
            handler._sqpaint_handler = True
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            self._logger.addHandler(handler)

    def log(
        self,
        action: str,
        details: str = "",
        level: int = logging.INFO,
    ) -> None:
        """Записывает событие в консоль и, если проект открыт, в таблицу logs."""
        message = f"{action}: {details}" if details else action
        self._logger.log(level, message)

        try:
            if self.database is not None and self.database.conn is not None:
                self.database.add_log(message)
        except Exception:
            # Сбой журналирования не должен блокировать редактирование.
            self._logger.exception("Не удалось записать событие в таблицу logs")
