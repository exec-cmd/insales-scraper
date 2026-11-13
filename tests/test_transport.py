import asyncio

import httpx
import pytest

from insales_scraper.config import Config
from insales_scraper.transports import HTTPXTransport, TransportError


def make_transport(handler, attempts: int = 3) -> HTTPXTransport:
    transport = HTTPXTransport(
        Config(max_request_attempts=attempts, retry_delay_seconds=0)
    )
    transport.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return transport


def request(transport: HTTPXTransport, url: str = "https://shop.test/") -> str:
    async def run() -> str:
        async with transport:
            return await transport.request(url)

    return asyncio.run(run())


def test_request_success():
    transport = make_transport(lambda _: httpx.Response(200, text="ok"))

    assert request(transport) == "ok"


def test_request_retries_on_bad_status():
    statuses = iter([500, 503, 200])
    transport = make_transport(lambda _: httpx.Response(next(statuses), text="ok"))

    assert request(transport) == "ok"


def test_request_exhausted_status():
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        return httpx.Response(404)

    with pytest.raises(TransportError) as info:
        request(make_transport(handler, attempts=3))

    assert len(calls) == 3
    assert info.value.attempts == 3
    assert info.value.status_code == 404
    assert info.value.cause is None


def test_request_retries_on_network_error():
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        if len(calls) < 2:
            raise httpx.ConnectError("boom")
        return httpx.Response(200, text="ok")

    assert request(make_transport(handler)) == "ok"


def test_request_exhausted_network_error():
    def handler(req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    with pytest.raises(TransportError) as info:
        request(make_transport(handler, attempts=2))

    assert info.value.status_code is None
    assert isinstance(info.value.cause, httpx.ConnectError)
    assert "ConnectError" in str(info.value)


def test_request_single_attempt():
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append(req)
        return httpx.Response(500)

    with pytest.raises(TransportError):
        request(make_transport(handler, attempts=1))

    assert len(calls) == 1


def test_error_message_without_optionals():
    error = TransportError("https://x", 2)

    assert str(error) == "Request failed for https://x after 2 attempts"


def test_error_message_with_status():
    assert "HTTP 500" in str(TransportError("https://x", 2, status_code=500))
