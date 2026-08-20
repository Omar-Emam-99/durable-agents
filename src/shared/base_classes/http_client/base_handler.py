"""DelegatingHandler base class and HTTP message models."""

from __future__ import annotations

from abc import ABC
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shared.base_classes.http_client.base_endpoint import (
        BaseEndpoint,
        HttpMethod,
    )
    from shared.logging import Logger


@dataclass
class HttpRequestMessage:
    """Mutable outgoing HTTP request - passed through the handler pipeline."""

    endpoint: BaseEndpoint
    method: HttpMethod
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, Any] | None = None
    body: Any | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    """Arbitrary bag for handlers to share state (like .NET HttpRequestMessage.Properties)."""


@dataclass
class HttpResponseMessage:
    """Mutable HTTP response - passed back up through the handler pipeline."""

    status_code: int
    headers: dict[str, str] = field(default_factory=dict)
    content: bytes = b""
    parsed: Any | None = None
    request: HttpRequestMessage | None = None
    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """True if status code is in the 2xx range."""
        return 200 <= self.status_code < 300


# Type alias for the next handler in the chain
NextHandler = Callable[[HttpRequestMessage], Awaitable[HttpResponseMessage]]


class DelegatingHandler(ABC):
    """
    Base class for HTTP pipeline handlers - mirrors .NET's DelegatingHandler.

    Each handler receives the request, can modify it, calls the next handler
    in the chain, and can modify/inspect the response on the way back.

    Override ``send_async()`` to implement custom logic.
    """

    def __init__(self) -> None:
        self._logger: Logger | None = None

    @property
    def logger(self) -> Logger:
        """Lazily resolve Logger from the DI container on first access."""
        if self._logger is None:
            from shared.logging import Logger
            from shared.scope_provider import container

            self._logger = container.resolve(Logger)
        return self._logger

    async def send_async(
        self,
        request: HttpRequestMessage,
        next_handler: NextHandler,
    ) -> HttpResponseMessage:
        """
        Process the request and delegate to the next handler.

        Args:
            request: The outgoing request message (mutable).
            next_handler: Call this to pass the request down the chain.

        Returns:
            The response message (possibly modified).
        """
        return await next_handler(request)
