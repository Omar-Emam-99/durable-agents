"""Integration tests for BaseHttpClient against the local ASGI echo app."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from pydantic import BaseModel

from shared.base_classes.http_client import (
    AuthHandler,
    BaseEndpoint,
    BaseHttpClient,
    BasePayload,
    BearerTokenAuth,
    HttpMethod,
    LoggingHandler,
    ResponseDeserializationHandler,
    RetryHandler,
)
from shared.base_classes.http_client.base_auth_provider import AuthProvider
from shared.base_classes.http_client.base_handler import (
    DelegatingHandler,
    HttpResponseMessage,
)


class ItemModel(BaseModel):
    id: str
    name: str


class GetEcho(BaseEndpoint):
    method = HttpMethod.GET
    path = "/echo"


class GetItem(BaseEndpoint):
    method = HttpMethod.GET
    path = "/items/{id}"
    response_model = ItemModel


class GetMissing(BaseEndpoint):
    method = HttpMethod.GET
    path = "/nope"


class GetFlaky(BaseEndpoint):
    method = HttpMethod.GET
    path = "/flaky"


class GetSecure(BaseEndpoint):
    method = HttpMethod.GET
    path = "/secure"


class PostItem(BaseEndpoint):
    method = HttpMethod.POST
    path = "/items"


class CreatePayload(BasePayload):
    def __init__(self, name: str) -> None:
        self.name = name

    def to_payload(self) -> dict[str, Any]:
        return {"name": self.name}


class RefreshableBearer(AuthProvider):
    def __init__(self) -> None:
        self._token = "stale-token"

    async def get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def refresh(self) -> None:
        self._token = "fresh-token"


class EndpointLoggingHandler(DelegatingHandler):
    """Zero-arg handler suitable for endpoint.handlers."""

    async def send_async(self, request, next_handler):
        request.properties["endpoint_handler"] = True
        return await next_handler(request)


class GetEchoWithEndpointHandler(BaseEndpoint):
    method = HttpMethod.GET
    path = "/echo"
    handlers = [EndpointLoggingHandler]


def _client(app, handlers=None) -> BaseHttpClient:
    return BaseHttpClient(
        "http://test",
        transport=httpx.ASGITransport(app=app),
        handlers=handlers or [],
    )


@pytest.mark.asyncio
async def test_call_success_parsed(setup_di, asgi_app):
    async with _client(
        asgi_app,
        [ResponseDeserializationHandler(), LoggingHandler()],
    ) as client:
        result = await client.call(GetItem(), path_params={"id": "7"})
        assert result.is_success
        assert isinstance(result.data, ItemModel)
        assert result.data.id == "7"


@pytest.mark.asyncio
async def test_call_http_error(setup_di, asgi_app):
    async with _client(asgi_app) as client:
        result = await client.call(GetMissing())
        assert result.is_failure
        assert result.error_code == "HTTP_404"


@pytest.mark.asyncio
async def test_retry_flaky(setup_di, asgi_app):
    async with _client(
        asgi_app,
        [RetryHandler(max_retries=2, backoff=0)],
    ) as client:
        result = await client.call(GetFlaky())
        assert result.is_success
        body = json.loads(result.data.content)
        assert body["ok"] is True


@pytest.mark.asyncio
async def test_auth_refresh_secure(setup_di, asgi_app):
    async with _client(
        asgi_app,
        [AuthHandler(RefreshableBearer()), LoggingHandler()],
    ) as client:
        result = await client.call(GetSecure())
        assert result.is_success


@pytest.mark.asyncio
async def test_bearer_echoed(setup_di, asgi_app):
    async with _client(
        asgi_app,
        [AuthHandler(BearerTokenAuth("tok"))],
    ) as client:
        result = await client.call(GetEcho())
        assert result.is_success
        assert isinstance(result.data, HttpResponseMessage)
        headers = json.loads(result.data.content)["headers"]
        assert headers["authorization"] == "Bearer tok"


@pytest.mark.asyncio
async def test_payload_post(setup_di, asgi_app):
    async with _client(asgi_app) as client:
        result = await client.call(PostItem(), body=CreatePayload("n"))
        assert result.is_success
        body = json.loads(result.data.content)
        assert body["body"] == {"name": "n"}


@pytest.mark.asyncio
async def test_endpoint_handlers_run(setup_di, asgi_app):
    seen: dict[str, bool] = {}

    class CaptureHandler(DelegatingHandler):
        async def send_async(self, request, next_handler):
            response = await next_handler(request)
            seen["endpoint_handler"] = bool(request.properties.get("endpoint_handler"))
            return response

    async with _client(asgi_app, [CaptureHandler()]) as client:
        result = await client.call(GetEchoWithEndpointHandler())
        assert result.is_success
        assert seen.get("endpoint_handler") is True


@pytest.mark.asyncio
async def test_async_context_manager_closes(setup_di, asgi_app):
    client = _client(asgi_app)
    async with client:
        assert not client._client.is_closed
    assert client._client.is_closed
