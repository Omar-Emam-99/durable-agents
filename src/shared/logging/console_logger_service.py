import sys
from typing import Any

from loguru import logger as loguru_logger

from .base_logger_service import BaseLoggerService


class ConsoleLoggerService(BaseLoggerService):
    """Concrete logger service that writes to the console using loguru."""

    def __init__(self, level: str = "INFO", serialize: bool = False) -> None:
        # Remove default loguru handler and add a configured one
        loguru_logger.remove()
        loguru_logger.add(
            sys.stderr,
            level=level.upper(),
            serialize=serialize,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
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
