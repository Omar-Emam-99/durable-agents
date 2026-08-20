"""
This module provides the DI container and the base scope provider.
"""

from __future__ import annotations

from typing import Any, cast

import punq

from .base_scope_provider import BaseScopeProvider

__all__ = ["BaseScopeProvider", "container"]

# Module-level container reference — set by infrastructure.di.container.setup()
_container: punq.Container | None = None


class _LazyContainer:
    """Forwards attribute access to the real container after ``set_container``."""

    def __getattr__(self, name: str) -> Any:
        if _container is None:
            raise RuntimeError(
                "DI container not initialized — call setup() before resolving dependencies."
            )
        return getattr(_container, name)


container = cast(punq.Container, _LazyContainer())


def set_container(c: punq.Container | None) -> None:
    """Called by the DI bootstrap to inject the container. Do NOT call directly."""
    global _container
    _container = c
