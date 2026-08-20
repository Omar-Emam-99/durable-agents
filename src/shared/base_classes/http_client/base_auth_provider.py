"""Authorization provider protocol and auth type enum."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum


class AuthType(StrEnum):
    """Supported authorization strategies."""

    NONE = "none"
    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"
    BASIC = "basic"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"


class AuthProvider(ABC):
    """
    Abstract base for authorization providers.
    Each provider knows how to produce the headers required for its auth strategy.
    """

    @abstractmethod
    async def get_headers(self) -> dict[str, str]:
        """Return authorization headers to attach to the request."""
        ...

    async def refresh(self) -> None:
        """
        Optionally refresh credentials (e.g. rotate an OAuth2 token).
        Default implementation is a no-op.
        """
