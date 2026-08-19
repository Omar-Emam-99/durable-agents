from collections.abc import Callable

from .base_logger_service import BaseLoggerService
from .console_logger_service import ConsoleLoggerService
from .file_logger_service import FileLoggerService

# Strategy map: service name → factory function that produces a single logger service
SERVICE_MAP: dict[str, Callable[..., BaseLoggerService]] = {
    "console": lambda level, log_file_path: ConsoleLoggerService(level=level),
    "file": lambda level, log_file_path: FileLoggerService(
        level=level, file_path=log_file_path
    ),
}


def resolve_logger_services(
    services: list[str],
    level: str = "INFO",
    log_file_path: str = "logs/app.log",
) -> list[BaseLoggerService]:
    """
    Factory that returns logger service(s) based on a list of service names.

    Args:
        services: List of service names (e.g. ["console", "file"])
        level: Log level threshold
        log_file_path: Path for file logger output

    Returns:
        List of concrete BaseLoggerService implementations
    """
    result = []
    for name in services:
        factory = SERVICE_MAP.get(name)
        if factory:
            result.append(factory(level, log_file_path))

    # Fallback to console if no valid services resolved
    if not result:
        result.append(ConsoleLoggerService(level=level))

    return result
