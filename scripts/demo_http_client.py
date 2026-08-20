#!/usr/bin/env python3
"""
Offline demo: subclass BaseHttpClient against a local Starlette ASGI app.

Covers every built-in AuthProvider and DelegatingHandler without network I/O.

Note: ``BaseHttpClient(auth_provider=...)`` is stored but not auto-wired —
pass ``AuthHandler(provider)`` in ``handlers=[...]``. Include
``ResponseDeserializationHandler`` when endpoints declare ``response_model``.

Run:  uv run python scripts/demo_http_client.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Allow ``uv run python scripts/demo_http_client.py`` without installing the package
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import httpx
from pydantic import BaseModel

from shared.base_classes.http_client import (
    ApiKeyAuth,
    AuthHandler,
    AuthProvider,
    BaseEndpoint,
    BaseHttpClient,
    BasePayload,
    BasicAuth,
    BearerTokenAuth,
    DelegatingHandler,
    HttpMethod,
    LoggingHandler,
    NoAuth,
    OAuth2ClientCredentialsAuth,
    ResponseDeserializationHandler,
    RetryHandler,
)
from shared.base_classes.http_client.base_handler import HttpResponseMessage
from shared.testing import bootstrap_console_logger, create_echo_app, reset_container

BASE_URL = "http://test"


class ItemModel(BaseModel):
    id: str
    name: str


class CreateItemPayload(BasePayload):
    def __init__(self, name: str) -> None:
        self.name = name

    def to_payload(self) -> dict[str, Any]:
        return {"name": self.name}


class GetEcho(BaseEndpoint):
    method = HttpMethod.GET
    path = "/echo"


class GetItem(BaseEndpoint):
    method = HttpMethod.GET
    path = "/items/{id}"
    response_model = ItemModel


class PostItem(BaseEndpoint):
    method = HttpMethod.POST
    path = "/items"


class GetSecure(BaseEndpoint):
    method = HttpMethod.GET
    path = "/secure"


class GetFlaky(BaseEndpoint):
    method = HttpMethod.GET
    path = "/flaky"


class RefreshableBearerAuth(AuthProvider):
    """Starts with a stale token; ``refresh()`` swaps to ``fresh-token``."""

    def __init__(self, token: str = "stale-token") -> None:
        self._token = token

    async def get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def refresh(self) -> None:
        self._token = "fresh-token"


class DemoApiClient(BaseHttpClient):
    """Example API client built on BaseHttpClient."""

    def __init__(
        self,
        base_url: str,
        *,
        handlers: list[DelegatingHandler] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            base_url,
            handlers=handlers or [],
            transport=transport,
            http_client=http_client,
        )


def _print_result(label: str, ok: bool, detail: Any) -> None:
    print(f"  [{'OK' if ok else 'FAIL'}] {label}: {detail}")


def _echo_headers(result: Any) -> dict[str, str]:
    if not result.is_success or not isinstance(result.data, HttpResponseMessage):
        return {}
    payload = json.loads(result.data.content)
    return {k.lower(): v for k, v in payload.get("headers", {}).items()}


async def section_no_auth(transport: httpx.ASGITransport) -> None:
    print("\n1) NoAuth + Logging + Deserialize")
    async with DemoApiClient(
        BASE_URL,
        transport=transport,
        handlers=[
            LoggingHandler(),
            AuthHandler(NoAuth()),
            ResponseDeserializationHandler(),
        ],
    ) as client:
        echo = await client.call(GetEcho())
        _print_result("GET /echo", echo.is_success, echo.data)
        item = await client.call(GetItem(), path_params={"id": "42"})
        _print_result(
            "GET /items/42",
            item.is_success and isinstance(item.data, ItemModel),
            item.data,
        )


async def section_bearer(transport: httpx.ASGITransport) -> None:
    print("\n2) BearerTokenAuth")
    async with DemoApiClient(
        BASE_URL,
        transport=transport,
        handlers=[AuthHandler(BearerTokenAuth("demo-token")), LoggingHandler()],
    ) as client:
        result = await client.call(GetEcho())
        auth = _echo_headers(result).get("authorization")
        _print_result(
            "Authorization header",
            result.is_success and auth == "Bearer demo-token",
            auth,
        )


async def section_api_key(transport: httpx.ASGITransport) -> None:
    print("\n3) ApiKeyAuth")
    async with DemoApiClient(
        BASE_URL,
        transport=transport,
        handlers=[AuthHandler(ApiKeyAuth("secret-key", header_name="X-API-Key"))],
    ) as client:
        result = await client.call(GetEcho())
        key = _echo_headers(result).get("x-api-key")
        _print_result("X-API-Key", result.is_success and key == "secret-key", key)


async def section_basic(transport: httpx.ASGITransport) -> None:
    print("\n4) BasicAuth")
    async with DemoApiClient(
        BASE_URL,
        transport=transport,
        handlers=[AuthHandler(BasicAuth("user", "pass"))],
    ) as client:
        result = await client.call(GetEcho())
        auth = _echo_headers(result).get("authorization", "")
        _print_result(
            "Authorization",
            result.is_success and auth.startswith("Basic "),
            auth,
        )


async def section_oauth2(transport: httpx.ASGITransport) -> None:
    print("\n5) OAuth2ClientCredentialsAuth")
    token_client = httpx.AsyncClient(transport=transport, base_url=BASE_URL)
    oauth = OAuth2ClientCredentialsAuth(
        token_url=f"{BASE_URL}/oauth/token",
        client_id="cid",
        client_secret="csecret",
        scopes=["read"],
        http_client=token_client,
    )
    try:
        async with DemoApiClient(
            BASE_URL,
            transport=transport,
            handlers=[AuthHandler(oauth), LoggingHandler()],
        ) as client:
            result = await client.call(GetEcho())
            auth = _echo_headers(result).get("authorization", "")
            _print_result(
                "OAuth Authorization",
                result.is_success and auth.startswith("Bearer oauth-token-"),
                auth,
            )
    finally:
        await token_client.aclose()


async def section_retry_and_auth_refresh(transport: httpx.ASGITransport) -> None:
    print("\n6) Full pipeline: Retry + Auth refresh + Logging + Deserialize")
    # Fresh app so /flaky starts at zero hits
    transport = httpx.ASGITransport(app=create_echo_app())
    async with DemoApiClient(
        BASE_URL,
        transport=transport,
        handlers=[
            RetryHandler(max_retries=3, backoff=0),
            AuthHandler(RefreshableBearerAuth("stale-token")),
            LoggingHandler(),
            ResponseDeserializationHandler(),
        ],
    ) as client:
        flaky = await client.call(GetFlaky())
        body = (
            json.loads(flaky.data.content)
            if flaky.is_success and isinstance(flaky.data, HttpResponseMessage)
            else None
        )
        _print_result("GET /flaky (retry 5xx)", flaky.is_success, body)
        secure = await client.call(GetSecure())
        secure_body = (
            json.loads(secure.data.content)
            if secure.is_success and isinstance(secure.data, HttpResponseMessage)
            else secure.message
        )
        _print_result(
            "GET /secure (401 then refresh)",
            secure.is_success,
            secure_body,
        )


async def section_payload(transport: httpx.ASGITransport) -> None:
    print("\n7) BasePayload POST body")
    async with DemoApiClient(
        BASE_URL,
        transport=transport,
        handlers=[LoggingHandler()],
    ) as client:
        result = await client.call(PostItem(), body=CreateItemPayload("widget"))
        body = (
            json.loads(result.data.content)
            if result.is_success and isinstance(result.data, HttpResponseMessage)
            else result.message
        )
        _print_result("POST /items", result.is_success, body)


async def main() -> None:
    bootstrap_console_logger(debug=False)
    try:
        app = create_echo_app()
        transport = httpx.ASGITransport(app=app)
        await section_no_auth(transport)
        await section_bearer(transport)
        await section_api_key(transport)
        await section_basic(transport)
        await section_oauth2(transport)
        await section_retry_and_auth_refresh(transport)
        await section_payload(httpx.ASGITransport(app=create_echo_app()))
        print("\nDemo complete.")
    finally:
        reset_container()


if __name__ == "__main__":
    asyncio.run(main())
