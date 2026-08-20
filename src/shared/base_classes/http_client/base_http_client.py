"""Base HTTP client with DelegatingHandler pipeline - inspired by .NET HttpClient / Refit."""

from __future__ import annotations

from typing import Any

import httpx

from shared.app_exceptions import HttpClientException, HttpTimeoutException
from shared.app_results import AppResult
from shared.base_classes.http_client.base_auth_provider import AuthProvider
from shared.base_classes.http_client.base_endpoint import BaseEndpoint
from shared.base_classes.http_client.base_handler import (
    DelegatingHandler,
    HttpRequestMessage,
    HttpResponseMessage,
    NextHandler,
)
from shared.base_classes.http_client.base_payload import BasePayload
from shared.logging import Logger


class BaseHttpClient:
    """
    Reusable async HTTP client with a DelegatingHandler pipeline.

    Subclass this, declare endpoints, configure handlers in __init__ - done.
    Do NOT override ``call()`` unless absolutely necessary.

    All responses are wrapped in ``AppResult[T]`` for consistent error handling.
    """

    def __init__(
        self,
        base_url: str,
        *,
        auth_provider: AuthProvider | None = None,
        default_timeout: float = 30.0,
        default_headers: dict[str, str] | None = None,
        handlers: list[DelegatingHandler] | None = None,
        verify_ssl: bool = True,
        transport: httpx.AsyncBaseTransport | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._logger: Logger | None = None
        self._base_url = base_url.rstrip("/")
        self._auth_provider = auth_provider
        self._default_timeout = default_timeout
        self._default_headers = default_headers or {}
        self._handlers: list[DelegatingHandler] = handlers or []
        if http_client is not None:
            self._client = http_client
        else:
            self._client = httpx.AsyncClient(
                timeout=default_timeout,
                verify=verify_ssl,
                transport=transport,
            )

    @property
    def logger(self) -> Logger:
        """Lazily resolve Logger from the DI container on first access."""
        if self._logger is None:
            from shared.scope_provider import container

            self._logger = container.resolve(Logger)
        return self._logger

    async def call(
        self,
        endpoint: BaseEndpoint,
        *,
        path_params: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
        body: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> AppResult[Any]:
        """
        Execute a request through the handler pipeline.

        Args:
            endpoint: The endpoint definition (method, path, response_model, etc.)
            path_params: Values to interpolate into the URL path.
            query_params: Query string parameters.
            body: Request body (dict, list, or Pydantic model).
            headers: Additional headers for this specific request.

        Returns:
            AppResult wrapping the parsed response model or HttpResponseMessage.
        """
        try:
            # Build the request message
            request = self._build_request_message(
                endpoint,
                path_params=path_params,
                query_params=query_params,
                body=body,
                headers=headers,
            )

            # Build the handler chain and invoke
            pipeline = self._build_pipeline(endpoint)
            response = await pipeline(request)

            # Check for HTTP errors
            if not response.is_success:
                return AppResult.failure(
                    message=f"HTTP {response.status_code}: {request.method} {request.url}",
                    error_code=f"HTTP_{response.status_code}",
                )

            # Return parsed model or full response
            if endpoint.response_model and response.parsed is not None:
                return AppResult.ok(response.parsed)
            return AppResult.ok(response)

        except (HttpClientException, HttpTimeoutException) as e:
            self.logger.exception(f"HTTP client error: {e.message}")
            return AppResult.failure(
                message=e.message,
                error_code=e.error_code_label,
            )
        except Exception as e:
            self.logger.exception(f"Unexpected error in HTTP client: {e}")
            return AppResult.failure(
                message=f"Unexpected error: {e}",
                error_code="HTTP_UNEXPECTED_ERROR",
            )

    def _build_request_message(
        self,
        endpoint: BaseEndpoint,
        *,
        path_params: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
        body: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpRequestMessage:
        """Construct an HttpRequestMessage from endpoint metadata and call arguments."""
        url = endpoint.build_url(self._base_url, path_params)

        merged_headers = {**self._default_headers}
        if headers:
            merged_headers.update(headers)

        # If body is a BasePayload, convert it via to_payload()
        serialized_body = body
        if isinstance(body, BasePayload):
            serialized_body = body.to_payload()

        # Default content type for requests with a body
        if serialized_body is not None and "Content-Type" not in merged_headers:
            merged_headers["Content-Type"] = "application/json"

        return HttpRequestMessage(
            endpoint=endpoint,
            method=endpoint.method,
            url=url,
            headers=merged_headers,
            query_params=query_params,
            body=serialized_body,
        )

    def _build_pipeline(self, endpoint: BaseEndpoint) -> NextHandler:
        """
        Compose handlers into a nested chain (onion model).
        Order: [...client_handlers, ...endpoint_handlers, _http_transport]
        """
        # Instantiate endpoint-level handlers (they are stored as types)
        endpoint_handlers: list[DelegatingHandler] = []
        if endpoint.handlers:
            for handler_cls in endpoint.handlers:
                endpoint_handlers.append(handler_cls())

        all_handlers = [*self._handlers, *endpoint_handlers]

        # The innermost callable is the actual HTTP transport
        next_handler: NextHandler = self._http_transport

        # Wrap from inside out
        for handler in reversed(all_handlers):
            prev = next_handler

            async def _make_caller(
                req: HttpRequestMessage,
                _h: DelegatingHandler = handler,
                _n: NextHandler = prev,
            ) -> HttpResponseMessage:
                return await _h.send_async(req, _n)

            next_handler = _make_caller

        return next_handler

    async def _http_transport(self, request: HttpRequestMessage) -> HttpResponseMessage:
        """The innermost handler - performs the actual HTTP call via httpx."""
        timeout = request.endpoint.timeout or self._default_timeout

        try:
            response = await self._client.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                params=request.query_params,
                json=request.body if request.body is not None else None,
                timeout=timeout,
            )

            return HttpResponseMessage(
                status_code=response.status_code,
                headers=dict(response.headers),
                content=response.content,
                request=request,
            )
        except httpx.TimeoutException as e:
            raise HttpTimeoutException(
                message=f"Request timed out: {request.method} {request.url}",
                url=request.url,
                timeout=timeout,
            ) from e
        except httpx.HTTPError as e:
            raise HttpClientException(
                message=f"HTTP request failed: {request.method} {request.url} - {e}",
                url=request.url,
            ) from e

    async def close(self) -> None:
        """Gracefully close the underlying httpx client."""
        await self._client.aclose()

    async def __aenter__(self) -> BaseHttpClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
