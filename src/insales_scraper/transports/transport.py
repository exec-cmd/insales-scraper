from abc import ABC, abstractmethod

from ..config import default_config


class Transport(ABC):
    def __init__(self, config=default_config):
        self.config = config

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @abstractmethod
    async def request(self, url: str) -> str: ...

    @abstractmethod
    async def close(self): ...
