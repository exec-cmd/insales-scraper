import logging
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    retry_delay_seconds: float = 4.5
    max_request_attempts: int = 5
    max_concurrent_requests: int = 5

    transport_backend: str = "httpx"
    proxy_url: str | None = None

    output_file_path: Path = Path("output.json")

    log_level: int = logging.WARNING

    fail_on_request_error: bool = False

    interval_between_runs_seconds: float = 15
    number_of_runs: int = 1


default_config = Config()
