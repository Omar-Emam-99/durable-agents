"""Tests for built-in DelegatingHandler implementations."""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from shared.base_classes.http_client.auth_providers import BearerTokenAuth
from shared.base_classes.http_client.base_auth_provider import AuthProvider
from shared.base_classes.http_client.base_endpoint import BaseEndpoint, HttpMethod
from shared.base_classes.http_client.base_handler import (
    HttpRequestMessage,
    HttpResponseMessage,
)
from shared.base_classes.http_client.handlers import (
    AuthHandler,
    LoggingHandler,
    ResponseDeserializationHandler,
    RetryHandler,
)


class Item(BaseModel):
    id: str
    name: str


class FakeEndpoint(BaseEndpoint):
    method = HttpMethod.GET
    path = "/x"
    response_model = Item


def _request(**kwargs) -> HttpRequestMessage:
    endpoint = kwargs.pop("endpoint", FakeEndpoint())
    return HttpRequestMessage(
        endpoint=endpoint,
        method=endpoint.method,
        url=kwargs.pop("url", "http://test/x"),
        headers=kwargs.pop("headers", {}),
        **kwargs,
    )


class RefreshableAuth(AuthProvider):
    def __init__(self) -> None:
        self.token = "stale"
        self.refresh_count = 0

    async def get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    async def refresh(self) -> None:
        self.refresh_count += 1
        self.token = "fresh"


@pytest.mark.asyncio
async def test_auth_handler_injects_headers(setup_di):
    calls: list[HttpRequestMessage] = []

    async def next_handler(req: HttpRequestMessage) -> HttpResponseMessage:
        calls.append(req)
        return HttpResponseMessage(status_code=200, content=b"{}")

    handler = AuthHandler(BearerTokenAuth("t"))
    await handler.send_async(_request(), next_handler)
    assert calls[0].headers["Authorization"] == "Bearer t"


@pytest.mark.asyncio
async def test_auth_handler_refreshes_on_401(setup_di):
    attempts = 0
    auth = RefreshableAuth()

    async def next_handler(req: HttpRequestMessage) -> HttpResponseMessage:
        nonlocal attempts
        attempts += 1
        if req.headers.get("Authorization") == "Bearer stale":
            return HttpResponseMessage(status_code=401, content=b"{}")
        return HttpResponseMessage(status_code=200, content=b'{"ok":true}')

    handler = AuthHandler(auth)
    response = await handler.send_async(_request(), next_handler)
    assert response.status_code == 200
    assert attempts == 2
    assert auth.refresh_count == 1


@pytest.mark.asyncio
async def test_logging_handler_passthrough(setup_di):
    async def next_handler(req: HttpRequestMessage) -> HttpResponseMessage:
        return HttpResponseMessage(status_code=201, content=b"x")

    handler = LoggingHandler()
    response = await handler.send_async(_request(), next_handler)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_retry_handler_on_5xx(setup_di):
    attempts = 0

    async def next_handler(req: HttpRequestMessage) -> HttpResponseMessage:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return HttpResponseMessage(status_code=503, content=b"err")
        return HttpResponseMessage(status_code=200, content=b"ok")

    handler = RetryHandler(max_retries=3, backoff=0)
    response = await handler.send_async(_request(), next_handler)
    assert response.status_code == 200
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_handler_on_exception(setup_di):
    attempts = 0

    async def next_handler(req: HttpRequestMessage) -> HttpResponseMessage:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionError("boom")
        return HttpResponseMessage(status_code=200, content=b"ok")

    handler = RetryHandler(max_retries=2, backoff=0)
    response = await handler.send_async(_request(), next_handler)
    assert response.status_code == 200
    assert attempts == 2


@pytest.mark.asyncio
async def test_retry_handler_does_not_retry_4xx(setup_di):
    attempts = 0

    async def next_handler(req: HttpRequestMessage) -> HttpResponseMessage:
        nonlocal attempts
        attempts += 1
        return HttpResponseMessage(status_code=404, content=b"missing")

    handler = RetryHandler(max_retries=3, backoff=0)
    response = await handler.send_async(_request(), next_handler)
    assert response.status_code == 404
    assert attempts == 1


@pytest.mark.asyncio
async def test_response_deserialization_handler():
    async def next_handler(req: HttpRequestMessage) -> HttpResponseMessage:
        return HttpResponseMessage(
            status_code=200,
            content=json.dumps({"id": "1", "name": "n"}).encode(),
        )

    handler = ResponseDeserializationHandler()
    response = await handler.send_async(_request(), next_handler)
    assert isinstance(response.parsed, Item)
    assert response.parsed.name == "n"
