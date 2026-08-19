from typing import Any

from .base_logger_service import BaseLoggerService


class Logger:
    """
    Aggregating logger that fans out every log call to all registered logger services.

    Follows the Open/Closed Principle: add new logger services (file, cloud, etc.)
    without modifying this class — just pass them in the constructor.
    """

    def __init__(self, services: list[BaseLoggerService], debug: bool = False) -> None:
        self._services = services
        self._debug = debug

    def debug(self, message: str, **kwargs: Any) -> None:
        if not self._debug:
            return
        for service in self._services:
            service.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        for service in self._services:
            service.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        for service in self._services:
            service.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        for service in self._services:
            service.error(message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        for service in self._services:
            service.critical(message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log at ERROR level with the current exception's traceback attached."""
        for service in self._services:
            service.exception(message, **kwargs)
