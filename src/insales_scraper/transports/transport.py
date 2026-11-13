from abc import ABC, abstractmethod

from ..config import default_config


class TransportError(RuntimeError):
    def __init__(
        self,
        url: str,
        attempts: int,
        status_code: int | None = None,
        cause: BaseException | None = None,
    ):
        self.url = url
        self.attempts = attempts
        self.status_code = status_code
        self.cause = cause

        message = f"Request failed for {url} after {attempts} attempts"
        if status_code is not None:
            message += f" with HTTP {status_code}"
        if cause is not None:
            message += f": {type(cause).__name__}: {cause}"

        super().__init__(message)


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
