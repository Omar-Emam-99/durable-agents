"""
Shared app results module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AppResult[T]:
    """
    Internal result wrapper for in-app communication between layers.
    Use this instead of raising exceptions when you want the caller to decide what to do.
    """

    success: bool
    data: T | None = None
    error_code: str | None = None
    message: str | None = None
    errors: list[str] | None = None
    debug: list[str] | None = None
    traceback: str | None = None
    timestamp: datetime | None = None

    @classmethod
    def ok(cls, data: T) -> AppResult[T]:
        """
        Create a successful result.
        """
        return cls(success=True, data=data)

    @classmethod
    def failure(
        cls,
        error_code: str,
        message: str,
        errors: list[str] | None = None,
        debug: list[str] | None = None,
        traceback: str | None = None,
    ) -> AppResult[T]:
        """
        Create a failed result.
        """
        return cls(
            success=False,
            error_code=error_code,
            message=message,
            errors=errors,
            debug=debug,
            traceback=traceback,
        )

    @property
    def is_success(self) -> bool:
        """
        Check if the result is successful.
        """
        return self.success

    @property
    def is_failure(self) -> bool:
        """
        Check if the result is failed.
        """
        return not self.success

    @property
    def is_error(self) -> bool:
        """
        Check if the result is an error.
        """
        return self.error_code is not None


@dataclass
class PaginatedResult[T]:
    """Typed container for paginated query results used across layers."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
