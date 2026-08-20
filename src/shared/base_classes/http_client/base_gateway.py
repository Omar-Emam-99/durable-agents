"""Base gateway class for external service integrations at the domain boundary.

A *Gateway* (or *Port*) represents a domain-level interface for communicating
with external systems (blob storage, APIs, file systems, queues, etc.) that
are **not** traditional database repositories.

Provides:
    - Lazy-resolved ``logger`` property (same pattern as other base classes)
    - Clear semantic separation from ``IBaseRepository`` (database persistence)
"""

from __future__ import annotations

from abc import ABC

from shared.logging import Logger


class BaseGateway(ABC):
    """
    Abstract base for domain-level gateway interfaces.

    Use this as the base class for interfaces that communicate with external
    systems (storage providers, third-party APIs, message brokers, etc.)
    instead of ``IBaseRepository`` which is reserved for database persistence.

    Features
    --------
    - **Lazy logger**: resolved from the DI container on first access.
    - **Provider-agnostic**: implementations live in infrastructure; the domain
      only depends on this abstract contract.
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
