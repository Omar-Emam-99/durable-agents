"""Built-in delegating handlers for the HTTP client pipeline."""

from __future__ import annotations

import asyncio
import json
import time

from shared.base_classes.http_client.base_auth_provider import AuthProvider
from shared.base_classes.http_client.base_handler import (
    DelegatingHandler,
    HttpRequestMessage,
    HttpResponseMessage,
    NextHandler,
)


class AuthHandler(DelegatingHandler):
    """
    Injects authorization headers into every request.
    If a 401 is received and the provider supports refresh, retries once.
    """

    def __init__(self, auth_provider: AuthProvider) -> None:
        super().__init__()
        self._auth_provider = auth_provider

    async def send_async(
        self, request: HttpRequestMessage, next_handler: NextHandler
    ) -> HttpResponseMessage:
        """Injects authorization headers into every request.

        Args:
            request: The HTTP request message to inject authorization headers into.
            next_handler: The next handler in the pipeline.

        Returns:
            The HTTP response message.
        """
        auth_headers = await self._auth_provider.get_headers()
        request.headers.update(auth_headers)

        response = await next_handler(request)

        if response.status_code == 401:
            self.logger.warning(
                f"Received 401 - refreshing auth credentials for {request.url}"
            )
            await self._auth_provider.refresh()
            auth_headers = await self._auth_provider.get_headers()
            request.headers.update(auth_headers)
            response = await next_handler(request)

        return response


class LoggingHandler(DelegatingHandler):
    """Logs outgoing requests and incoming responses with timing."""

    async def send_async(
        self, request: HttpRequestMessage, next_handler: NextHandler
    ) -> HttpResponseMessage:
        self.logger.info(f"→ {request.method} {request.url}")
        start = time.time()

        response = await next_handler(request)

        elapsed = time.time() - start
        self.logger.info(f"← {response.status_code} ({elapsed:.3f}s) {request.url}")
        return response


class RetryHandler(DelegatingHandler):
    """
    Retries failed requests with exponential backoff.
    Full control over the retry loop - wraps the entire roundtrip.
    """

    def __init__(self, max_retries: int = 3, backoff: float = 1.0) -> None:
        super().__init__()
        self._max_retries = max_retries
        self._backoff = backoff

    async def send_async(
        self, request: HttpRequestMessage, next_handler: NextHandler
    ) -> HttpResponseMessage:
        last_exception: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = await next_handler(request)
                if response.is_success or attempt == self._max_retries:
                    return response
                # Retry on server errors
                if response.status_code >= 500:
                    self.logger.warning(
                        f"Retry {attempt + 1}/{self._max_retries} - {response.status_code} {request.url}"
                    )
                    await asyncio.sleep(self._backoff * (2**attempt))
                    continue
                return response
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Retry {attempt + 1}/{self._max_retries} failed: {e}"
                )
                if attempt == self._max_retries:
                    raise
                await asyncio.sleep(self._backoff * (2**attempt))

        raise last_exception  # type: ignore[misc]


class ResponseDeserializationHandler(DelegatingHandler):
    """
    Auto-parses the response body into the endpoint's response_model (Pydantic).
    Only runs when response_model is set and the response is successful.
    """

    async def send_async(
        self, request: HttpRequestMessage, next_handler: NextHandler
    ) -> HttpResponseMessage:
        response = await next_handler(request)

        if request.endpoint.response_model and response.is_success and response.content:
            data = json.loads(response.content)
            response.parsed = request.endpoint.response_model.model_validate(data)

        return response
