"""Minimal DI bootstrap for demos and tests."""

from __future__ import annotations

import punq

from shared.logging import Logger, resolve_logger_services
from shared.scope_provider import set_container


def bootstrap_console_logger(*, debug: bool = True) -> punq.Container:
    """Register a console ``Logger`` in a new punq container and activate it."""
    container = punq.Container()
    services = resolve_logger_services(["console"], level="INFO")
    container.register(Logger, instance=Logger(services, debug=debug))
    set_container(container)
    return container


def reset_container() -> None:
    """Clear the module-level DI container reference."""
    set_container(None)
