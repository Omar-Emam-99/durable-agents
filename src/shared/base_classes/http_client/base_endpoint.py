"""Base endpoint definition for declarative API endpoint configuration."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from shared.base_classes.http_client.base_handler import DelegatingHandler


class HttpMethod(StrEnum):
    """HTTP methods supported by the client."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class BaseEndpoint:
    """
    Base class for declarative endpoint definitions.

    Subclass this per-API and set class attributes.
    The client will pull all config from the endpoint instance.
    """

    method: HttpMethod
    path: str  # e.g. "/api/v1/documents/{document_id}"
    response_model: type[BaseModel] | None = None
    request_model: type[BaseModel] | None = None
    timeout: float | None = None
    retry: int = 0
    handlers: list[type[DelegatingHandler]] | None = None  # endpoint-specific handlers

    def build_url(
        self, base_url: str, path_params: dict[str, Any] | None = None
    ) -> str:
        """Resolve path parameters and build the full URL."""
        path = self.path
        if path_params:
            path = path.format(**path_params)
        return f"{base_url.rstrip('/')}/{path.lstrip('/')}"
