"""Abstract base repository interface – pure domain, no infrastructure dependencies."""

import uuid
from abc import ABC, abstractmethod

from shared.app_results import AppResult, PaginatedResult
from shared.logging import Logger


class IBaseRepository[DomainT](ABC):
    """
    Abstract generic repository interface for domain models.
    All methods return AppResult[T] for consistent error handling.
    This interface has NO infrastructure (SQLAlchemy) dependencies.

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
        if self._logger is None:
            raise RuntimeError("Logger not found in the DI container")
        return self._logger

    @abstractmethod
    async def find_by_id(self, entity_id: uuid.UUID) -> AppResult[DomainT | None]:
        """Find a single domain model by its UUID."""
        ...

    @abstractmethod
    async def find_all(
        self, page: int = 1, page_size: int = 20
    ) -> AppResult[PaginatedResult[DomainT]]:
        """Find all domain models with pagination."""
        ...

    @abstractmethod
    async def create(self, entity: DomainT) -> AppResult[DomainT]:
        """Persist a new domain model."""
        ...

    @abstractmethod
    async def update(self, entity: DomainT) -> AppResult[DomainT]:
        """Update an existing domain model."""
        ...

    @abstractmethod
    async def delete(self, entity_id: uuid.UUID) -> AppResult[bool]:
        """Delete a domain model by id."""
        ...
