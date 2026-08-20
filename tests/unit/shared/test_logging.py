"""Tests for logging strategies and Logger fan-out."""

from shared.logging import (
    ConsoleLoggerService,
    FileLoggerService,
    Logger,
    resolve_logger_services,
)


def test_resolve_console_and_file(tmp_path):
    log_file = tmp_path / "app.log"
    services = resolve_logger_services(
        ["console", "file"],
        level="INFO",
        log_file_path=str(log_file),
    )
    assert len(services) == 2
    assert isinstance(services[0], ConsoleLoggerService)
    assert isinstance(services[1], FileLoggerService)


def test_resolve_fallback_to_console():
    services = resolve_logger_services(["unknown-service"])
    assert len(services) == 1
    assert isinstance(services[0], ConsoleLoggerService)


def test_logger_fan_out(tmp_path):
    log_file = tmp_path / "fanout.log"
    services = resolve_logger_services(
        ["file"],
        level="DEBUG",
        log_file_path=str(log_file),
    )
    logger = Logger(services, debug=True)
    logger.info("hello-info")
    logger.debug("hello-debug")
    logger.warning("hello-warn")
    content = log_file.read_text()
    assert "hello-info" in content
    assert "hello-debug" in content
    assert "hello-warn" in content


def test_logger_debug_suppressed_when_disabled(tmp_path):
    log_file = tmp_path / "nodebug.log"
    services = resolve_logger_services(["file"], log_file_path=str(log_file))
    logger = Logger(services, debug=False)
    logger.debug("should-not-appear")
    logger.info("should-appear")
    content = log_file.read_text()
    assert "should-not-appear" not in content
    assert "should-appear" in content
