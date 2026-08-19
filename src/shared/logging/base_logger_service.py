from abc import ABC, abstractmethod
from typing import Any


class BaseLoggerService(ABC):
    """Abstract base for all logger service implementations (Open/Closed Principle)."""

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def exception(self, message: str, **kwargs: Any) -> None:
        """Log at ERROR level with the current exception's traceback attached."""
        ...
