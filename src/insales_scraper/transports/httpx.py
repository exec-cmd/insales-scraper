import logging
from asyncio import Semaphore, sleep

from httpx import AsyncClient, HTTPError

from ..config import default_config
from .transport import Transport

logger = logging.getLogger(__name__)


class HTTPXTransport(Transport):
    def __init__(self, config=default_config):
        super().__init__(config)

        self.client = AsyncClient(proxy=config.proxy)
        self.semaphore = Semaphore(config.concurrency)

    async def request(self, url: str) -> str:
        async with self.semaphore:
            last_text_error = None

            for _ in range(self.config.retries):
                try:
                    response = await self.client.get(url)
                except HTTPError as e:
                    logger.warning(
                        f"Request failed: {e}; Retry {_ + 1}/{self.config.retries}"
                    )

                    last_text_error = str(e)
                    continue

                if response.is_success:
                    return response.text

                await sleep(self.config.sleep_duration)

            raise RuntimeError(last_text_error)

    async def close(self):
        await self.client.aclose()
