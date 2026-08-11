import logging
from asyncio import Semaphore, sleep

from curl_cffi import AsyncSession, CurlError

from ..config import config
from .transport import Transport

logger = logging.getLogger(__name__)


class CurlCFFITransport(Transport):
    def __init__(self):
        self.client = AsyncSession()
        self.semaphore = Semaphore(config.concurrency)

    async def request(self, url: str) -> str:
        async with self.semaphore:
            last_text_error = None

            for _ in range(config.retries):
                try:
                    response = await self.client.get(url)
                except CurlError as e:
                    logger.warning(
                        f"Request failed: {e}; Retry {_ + 1}/{config.retries}"
                    )

                    last_text_error = str(e)
                    continue

                if response.ok:
                    return response.text

                await sleep(config.sleep_duration)

            raise RuntimeError(last_text_error)

    async def close(self):
        await self.client.close()
