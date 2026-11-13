import logging
from asyncio import Semaphore, sleep

from httpx import AsyncClient, HTTPError

from ..config import default_config
from .transport import Transport, TransportError

logger = logging.getLogger(__name__)


class HTTPXTransport(Transport):
    def __init__(self, config=default_config):
        super().__init__(config)

        self.client = AsyncClient(proxy=config.proxy_url)
        self.semaphore = Semaphore(config.max_concurrent_requests)

    async def request(self, url: str) -> str:
        async with self.semaphore:
            last_error = None
            last_status_code = None

            for attempt in range(self.config.max_request_attempts):
                try:
                    response = await self.client.get(url)
                except HTTPError as error:
                    logger.warning(
                        f"Request failed: {error}; Retry {attempt + 1}/{self.config.max_request_attempts}"
                    )
                    last_error = error
                    continue

                if response.is_success:
                    return response.text

                last_status_code = response.status_code
                await sleep(self.config.retry_delay_seconds)

            raise TransportError(
                url,
                self.config.max_request_attempts,
                status_code=last_status_code,
                cause=last_error,
            ) from last_error

    async def close(self):
        await self.client.aclose()
