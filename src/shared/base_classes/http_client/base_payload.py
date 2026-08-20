"""Base payload class for HTTP client request bodies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BasePayload(ABC):
    """
    Base class for request payloads.

    Subclass this and override ``to_payload()`` to define how your
    data is serialized into a dict/map before being sent as the request body.
    """

    @abstractmethod
    def to_payload(self) -> dict[str, Any]:
        """
        Convert this payload into a dictionary suitable for JSON serialization.

        Override this method to control exactly what gets sent in the request body.
        """
        ...
