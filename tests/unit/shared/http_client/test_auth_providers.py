"""Tests for concrete AuthProvider implementations."""

from __future__ import annotations

import base64

import httpx
import pytest

from shared.app_exceptions import HttpClientException
from shared.base_classes.http_client.auth_providers import (
    ApiKeyAuth,
    BasicAuth,
    BearerTokenAuth,
    NoAuth,
    OAuth2ClientCredentialsAuth,
)


@pytest.mark.asyncio
async def test_no_auth():
    assert await NoAuth().get_headers() == {}


@pytest.mark.asyncio
async def test_bearer_token_auth():
    headers = await BearerTokenAuth("abc").get_headers()
    assert headers == {"Authorization": "Bearer abc"}


@pytest.mark.asyncio
async def test_api_key_auth():
    headers = await ApiKeyAuth("k", header_name="X-Key").get_headers()
    assert headers == {"X-Key": "k"}


@pytest.mark.asyncio
async def test_basic_auth():
    headers = await BasicAuth("u", "p").get_headers()
    expected = base64.b64encode(b"u:p").decode()
    assert headers == {"Authorization": f"Basic {expected}"}


@pytest.mark.asyncio
async def test_oauth2_client_credentials(asgi_app):
    transport = httpx.ASGITransport(app=asgi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        auth = OAuth2ClientCredentialsAuth(
            token_url="http://test/oauth/token",
            client_id="cid",
            client_secret="secret",
            scopes=["a"],
            http_client=client,
        )
        headers = await auth.get_headers()
        assert headers["Authorization"].startswith("Bearer oauth-token-")
        # Cached — second call should not bump counter unless expired
        headers2 = await auth.get_headers()
        assert headers2 == headers


@pytest.mark.asyncio
async def test_oauth2_refresh_failure(asgi_app):
    transport = httpx.ASGITransport(app=asgi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        auth = OAuth2ClientCredentialsAuth(
            token_url="http://test/echo",  # wrong method/endpoint -> not a token
            client_id="cid",
            client_secret="secret",
            http_client=client,
        )
        with pytest.raises(HttpClientException) as exc_info:
            await auth.refresh()
        # GET /echo returns 405 for POST, or we get JSON without access_token
        # POST to /echo may 405 Method Not Allowed
        assert exc_info.value.error_code_label == "OAUTH2_TOKEN_ERROR"
