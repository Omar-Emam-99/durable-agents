"""Tests for application exception hierarchy."""

from shared.app_exceptions import (
    AppErrorCode,
    AppException,
    DataNotFoundException,
    DataValidationException,
    DependencyFailedException,
    DuplicateDataException,
    HttpClientException,
    HttpTimeoutException,
    OperationFailedException,
    RepositoryException,
)


def test_app_exception_defaults():
    exc = AppException()
    assert exc.error_code == AppErrorCode.OPERATION_FAILED
    assert "application error" in exc.message.lower()


def test_subclass_error_codes():
    assert DataNotFoundException().error_code == AppErrorCode.NOT_FOUND
    assert DataValidationException().error_code == AppErrorCode.VALIDATION_FAILED
    assert DuplicateDataException().error_code == AppErrorCode.DUPLICATE
    assert OperationFailedException().error_code == AppErrorCode.OPERATION_FAILED
    assert DependencyFailedException().error_code == AppErrorCode.DEPENDENCY_FAILED


def test_http_client_exception():
    exc = HttpClientException(
        "boom",
        status_code=502,
        url="http://x",
        error_code_label="HTTP_CLIENT_ERROR",
    )
    assert isinstance(exc, AppException)
    assert exc.error_code == AppErrorCode.DEPENDENCY_FAILED
    assert exc.status_code == 502
    assert exc.url == "http://x"
    assert exc.error_code_label == "HTTP_CLIENT_ERROR"


def test_http_timeout_exception():
    exc = HttpTimeoutException("slow", url="http://x", timeout=1.5)
    assert isinstance(exc, HttpClientException)
    assert exc.error_code_label == "HTTP_TIMEOUT_ERROR"
    assert exc.timeout == 1.5


def test_repository_exception_label():
    exc = RepositoryException("db down", error_code_label="REPO_TIMEOUT")
    assert exc.error_code_label == "REPO_TIMEOUT"
