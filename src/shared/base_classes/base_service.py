"""Base service class for SDK-based external service integrations.

Unlike ``BaseHttpClient`` (which wraps raw HTTP via httpx), ``BaseService``
is the base for services that rely on vendor SDKs (Azure, GCP, AWS SDK, etc.)
where the SDK itself manages HTTP transport, retries, and serialisation.

Provides:
    - Lazy-resolved ``logger`` property (same pattern as ``BaseUseCase``)
    - Async lifecycle hooks (``close``, ``__aenter__`` / ``__aexit__``)
    - Consistent interface for DI registration
"""

from __future__ import annotations

from abc import ABC

from shared.logging import Logger


class BaseService(ABC):
    """
    Abstract base for SDK-based external service wrappers.

    Subclass this when integrating with a vendor SDK (e.g. Azure Blob,
    AWS SDK, Google Cloud client libraries) rather than making raw HTTP calls.

    Features
    --------
    - **Lazy logger**: resolved from the DI container on first access.
    - **Async lifecycle**: ``close()`` for graceful shutdown; supports
      ``async with`` context manager.
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

    # ── Lifecycle ──────────────────────────────────────────────────────
