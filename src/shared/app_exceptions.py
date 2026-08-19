from enum import StrEnum
from typing import Any


class AppErrorCode(StrEnum):
    """Internal error codes for application-level failures."""

    NOT_FOUND = "APP_NOT_FOUND"
    VALIDATION_FAILED = "APP_VALIDATION_FAILED"
    DUPLICATE = "APP_DUPLICATE"
    OPERATION_FAILED = "APP_OPERATION_FAILED"
    DEPENDENCY_FAILED = "APP_DEPENDENCY_FAILED"
    UNAUTHORIZED = "APP_UNAUTHORIZED"
    FORBIDDEN = "APP_FORBIDDEN"


class AppException(Exception):
    """
    Base internal application exception.
    Use this for in-app logic flow — NOT tied to HTTP status codes.
    Catch these in services/routers and decide how to respond.
    """

    error_code: AppErrorCode = AppErrorCode.OPERATION_FAILED
    message: str = "An application error occurred."

    def __init__(self, message: str | None = None, **kwargs: Any) -> None:
        self.message = message or self.__class__.message
        self.context = kwargs
        super().__init__(self.message)


class DataNotFoundException(AppException):
    """Raised when expected data is not found in the database or any data source."""

    error_code = AppErrorCode.NOT_FOUND
    message = "Requested data was not found."


class DataValidationException(AppException):
    """Raised when data fails internal business validation rules."""

    error_code = AppErrorCode.VALIDATION_FAILED
    message = "Data validation failed."


class DuplicateDataException(AppException):
    """Raised when attempting to create data that already exists."""

    error_code = AppErrorCode.DUPLICATE
    message = "Data already exists."


class OperationFailedException(AppException):
    """Raised when a business operation cannot be completed."""

    error_code = AppErrorCode.OPERATION_FAILED
    message = "Operation could not be completed."


class DependencyFailedException(AppException):
    """Raised when an internal dependency (another service, queue, cache) fails."""

    error_code = AppErrorCode.DEPENDENCY_FAILED
    message = "A required dependency failed."


class RepositoryException(AppException):
    """Raised when a repository operation fails unexpectedly."""

    error_code = AppErrorCode.OPERATION_FAILED
    message = "A repository operation failed."

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code_label: str = "REPO_ERROR",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.error_code_label = error_code_label


class HttpClientException(AppException):
    """Raised when an HTTP client request fails."""

    error_code = AppErrorCode.DEPENDENCY_FAILED
    message = "An HTTP client request failed."

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        url: str | None = None,
        error_code_label: str = "HTTP_CLIENT_ERROR",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.url = url
        self.error_code_label = error_code_label


class HttpTimeoutException(HttpClientException):
    """Raised when an HTTP client request times out."""

    message = "HTTP request timed out."

    def __init__(
        self,
        message: str | None = None,
        *,
        url: str | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message, url=url, error_code_label="HTTP_TIMEOUT_ERROR", **kwargs
        )
        self.timeout = timeout
