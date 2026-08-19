"""Base middleware with lazy DI-resolved logger."""

from starlette.middleware.base import BaseHTTPMiddleware

from shared.logging import Logger


class BaseMiddleware(BaseHTTPMiddleware):
    """
    Abstract base for all application middleware.

    Provides a lazily-resolved ``logger`` property so subclasses never
    call ``container.resolve()`` at class-body / import time.
    """

    _logger: Logger | None = None

    @property
    def logger(self) -> Logger:
        """Lazily resolve Logger from the DI container on first access."""
        if self._logger is None:
            from shared.scope_provider import container

            self._logger = container.resolve(Logger)
        return self._logger
