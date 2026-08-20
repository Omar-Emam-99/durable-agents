"""Tests for the punq scope provider."""

import punq
import pytest

from shared.logging import Logger, resolve_logger_services
from shared.scope_provider import container, set_container


def test_container_raises_before_setup():
    set_container(None)
    with pytest.raises(RuntimeError, match="not initialized"):
        container.resolve(Logger)


def test_set_container_and_resolve():
    c = punq.Container()
    logger = Logger(resolve_logger_services(["console"]), debug=False)
    c.register(Logger, instance=logger)
    set_container(c)
    try:
        assert container.resolve(Logger) is logger
    finally:
        set_container(None)
