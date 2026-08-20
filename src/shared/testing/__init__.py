"""Test and demo helpers for shared (DI bootstrap, local ASGI echo app)."""

from shared.testing.asgi_echo_app import create_echo_app
from shared.testing.di import bootstrap_console_logger, reset_container

__all__ = [
    "bootstrap_console_logger",
    "create_echo_app",
    "reset_container",
]
