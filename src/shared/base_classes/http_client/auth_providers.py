"""Concrete auth provider implementations."""

from __future__ import annotations

import base64
import time
from typing import Any

import httpx

from shared.app_exceptions import HttpClientException
from shared.base_classes.http_client.base_auth_provider import AuthProvider


class NoAuth(AuthProvider):
    """No authentication - returns empty headers."""

    async def get_headers(self) -> dict[str, str]:
        return {}


class BearerTokenAuth(AuthProvider):
    """Static bearer token authentication."""

    def __init__(self, token: str) -> None:
        self._token = token

    async def get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}


class ApiKeyAuth(AuthProvider):
    """API key sent as a custom header."""

    def __init__(self, api_key: str, header_name: str = "X-API-Key") -> None:
        self._api_key = api_key
        self._header_name = header_name

    async def get_headers(self) -> dict[str, str]:
        return {self._header_name: self._api_key}


class BasicAuth(AuthProvider):
    """HTTP Basic authentication."""

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password

    async def get_headers(self) -> dict[str, str]:
        credentials = base64.b64encode(
            f"{self._username}:{self._password}".encode()
        ).decode()
        return {"Authorization": f"Basic {credentials}"}


class OAuth2ClientCredentialsAuth(AuthProvider):
    """
    OAuth2 Client Credentials flow with automatic token caching and refresh.
    """

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scopes: list[str] | None = None,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._scopes = scopes or []
        self._http_client = http_client
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    async def get_headers(self) -> dict[str, str]:
        if self._is_token_expired():
            await self.refresh()
        return {"Authorization": f"Bearer {self._access_token}"}

    async def refresh(self) -> None:
        """Fetch a new access token from the token endpoint."""
        try:
            data: dict[str, Any] = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }
            if self._scopes:
                data["scope"] = " ".join(self._scopes)

            if self._http_client is not None:
                response = await self._http_client.post(self._token_url, data=data)
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(self._token_url, data=data)

            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data["access_token"]
            # Expire 60s early to avoid edge cases
            expires_in = token_data.get("expires_in", 3600)
            self._expires_at = time.time() + expires_in - 60
        except httpx.HTTPStatusError as e:
            raise HttpClientException(
                message=f"OAuth2 token request failed: {e.response.status_code} {self._token_url}",
                status_code=e.response.status_code,
                url=self._token_url,
                error_code_label="OAUTH2_TOKEN_ERROR",
            ) from e

    def _is_token_expired(self) -> bool:
        return self._access_token is None or time.time() >= self._expires_at
