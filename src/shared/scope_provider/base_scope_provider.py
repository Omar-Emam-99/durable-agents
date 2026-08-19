from abc import ABC, abstractmethod

import punq


class BaseScopeProvider(ABC):
    @abstractmethod
    def init_scope_provider(self, container: punq.Container) -> None:
        """Register dependencies into the DI container."""
        ...
