from enum import IntEnum
from typing import Any, ClassVar


class HttpStatusCode(IntEnum):
    """HTTP status codes used across the application."""

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502


class BaseAppException(Exception):
    """Base exception for all application-level errors."""

    status_code: ClassVar[HttpStatusCode] = HttpStatusCode.INTERNAL_SERVER_ERROR
    detail: ClassVar[str] = "An unexpected error occurred."
    error_code: ClassVar[str] = "INTERNAL_ERROR"

    def __init__(self, detail: str | None = None, **kwargs: Any) -> None:
        self.detail = detail or self.__class__.detail
        self.extra = kwargs
        super().__init__(self.detail)


class NotFoundException(BaseAppException):
    """Raised when a requested resource is not found."""

    status_code: ClassVar[HttpStatusCode] = HttpStatusCode.NOT_FOUND
    detail: ClassVar[str] = "Resource not found."
    error_code: ClassVar[str] = "NOT_FOUND"


class BadRequestException(BaseAppException):
    """Raised when the request payload is invalid or malformed."""

    status_code: ClassVar[HttpStatusCode] = HttpStatusCode.BAD_REQUEST
    detail: ClassVar[str] = "Bad request."
    error_code: ClassVar[str] = "BAD_REQUEST"


class UnauthorizedException(BaseAppException):
    """Raised when authentication is missing or invalid."""

    status_code: ClassVar[HttpStatusCode] = HttpStatusCode.UNAUTHORIZED
    detail: ClassVar[str] = "Unauthorized."
    error_code: ClassVar[str] = "UNAUTHORIZED"


class ForbiddenException(BaseAppException):
    """Raised when access to a resource is denied."""

    status_code: ClassVar[HttpStatusCode] = HttpStatusCode.FORBIDDEN
    detail: ClassVar[str] = "Forbidden."
    error_code: ClassVar[str] = "FORBIDDEN"


class ConflictException(BaseAppException):
    """Raised when there is a resource conflict (e.g. duplicate)."""

    status_code: ClassVar[HttpStatusCode] = HttpStatusCode.CONFLICT
    detail: ClassVar[str] = "Conflict."
    error_code: ClassVar[str] = "CONFLICT"


class UnprocessableEntityException(BaseAppException):
    """Raised when the request is well-formed but semantically invalid."""

    status_code: ClassVar[HttpStatusCode] = HttpStatusCode.UNPROCESSABLE_ENTITY
    detail: ClassVar[str] = "Unprocessable entity."
    error_code: ClassVar[str] = "UNPROCESSABLE_ENTITY"


class ExternalServiceException(BaseAppException):
    """Raised when an external/third-party service call fails."""

    status_code: ClassVar[HttpStatusCode] = HttpStatusCode.BAD_GATEWAY
    detail: ClassVar[str] = "External service error."
    error_code: ClassVar[str] = "EXTERNAL_SERVICE_ERROR"
