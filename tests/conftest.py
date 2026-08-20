"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from shared.testing import bootstrap_console_logger, create_echo_app, reset_container


@pytest.fixture
def setup_di():
    """Activate a console Logger in the DI container for the test."""
    container = bootstrap_console_logger(debug=True)
    yield container
    reset_container()


@pytest.fixture
def asgi_app():
    """Fresh Starlette echo app (mutable route state starts clean)."""
    return create_echo_app()
