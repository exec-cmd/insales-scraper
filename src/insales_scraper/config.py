import logging
from dataclasses import dataclass


@dataclass
class Config:
    sleep_duration: float = 4.5
    retries: int = 5
    concurrency: int = 5

    transport: str = "httpx"
    level: int = logging.WARNING

    fatalist: bool = False


config = Config()
