import os
from typing import Any

from loguru import logger as loguru_logger

from .base_logger_service import BaseLoggerService


class FileLoggerService(BaseLoggerService):
    """Concrete logger service that writes to a file using loguru."""

    def __init__(
        self,
        level: str = "INFO",
        file_path: str = "logs/app.log",
        rotation: str = "10 MB",
    ) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        loguru_logger.add(
            file_path,
            level=level.upper(),
            rotation=rotation,
            retention="30 days",
            compression="gz",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} - "
                "{message}"
            ),
        )
        self._logger = loguru_logger

    def debug(self, message: str, **kwargs: Any) -> None:
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        self._logger.opt(exception=True).error(message, **kwargs)
