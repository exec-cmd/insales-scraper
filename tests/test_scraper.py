import asyncio
import json

import pytest

from insales_scraper.config import Config
from insales_scraper.scraper import Scraper
from insales_scraper.transports import Transport, TransportError

SHOP = "https://shop.test"


class FakeTransport(Transport):
    def __init__(self, responses: dict[str, str | Exception]):
        super().__init__()
        self.responses = responses
        self.requested: list[str] = []
        self.closed = False

    async def request(self, url: str) -> str:
        self.requested.append(url)
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response

    async def close(self):
        self.closed = True


def make_scraper(responses: dict[str, str | Exception], **config) -> Scraper:
    scraper = Scraper(Config(**config))
    scraper.transport = FakeTransport(responses)
    return scraper


def sitemap(*urls: str) -> str:
    locs = "".join(f"<url><loc>{url}</loc></url>" for url in urls)
    return (
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locs}</urlset>'
    )


def product_json(**overrides) -> str:
    product = {
        "id": 1,
        "title": "Товар",
        "description": "Описание",
        "available": True,
        "images": [{"original_url": "https://shop.test/1.jpg"}],
        "variants": [
            {
                "id": 10,
                "title": "V",
                "sku": None,
                "barcode": None,
                "available": True,
                "quantity": None,
                "price": 99.5,
                "old_price": None,
            }
        ],
    }
    return json.dumps({"product": product | overrides})


def transport_error() -> TransportError:
    return TransportError("u", 1, status_code=500)


# --- sitemap ---


def test_sitemap_filters_products():
    scraper = make_scraper({})
    xml = sitemap(f"{SHOP}/product/a", f"{SHOP}/collection/b", f"{SHOP}/product/c")

    assert scraper._get_products_from_sitemap(xml) == [
        f"{SHOP}/product/a",
        f"{SHOP}/product/c",
    ]


def test_sitemap_without_namespace():
    scraper = make_scraper({})
    xml = f"<urlset><url><loc>{SHOP}/product/a</loc></url></urlset>"

    assert scraper._get_products_from_sitemap(xml) == [f"{SHOP}/product/a"]


def test_sitemap_strips_whitespace():
    scraper = make_scraper({})

    assert scraper._get_products_from_sitemap(sitemap(f"\n  {SHOP}/product/a  \n")) == [
        f"{SHOP}/product/a"
    ]


@pytest.mark.parametrize("xml", ["", "not xml", "<urlset><url>", sitemap()])
def test_sitemap_broken_or_empty(xml: str):
    assert make_scraper({})._get_products_from_sitemap(xml) == []


def test_sitemap_empty_loc():
    scraper = make_scraper({})

    assert scraper._get_products_from_sitemap("<urlset><loc/></urlset>") == []


# --- sitemap url ---


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (SHOP, f"{SHOP}/sitemap.xml"),
        (f"{SHOP}/", f"{SHOP}/sitemap.xml"),
        (f"{SHOP}/sitemap.xml", f"{SHOP}/sitemap.xml"),
        (f"{SHOP}/custom.xml", f"{SHOP}/custom.xml"),
    ],
)
def test_sitemap_url(url: str, expected: str):
    scraper = make_scraper({expected: sitemap()})

    asyncio.run(scraper._get_all_urls_products(url))

    assert scraper.transport.requested == [expected]


def test_empty_url_makes_no_request():
    scraper = make_scraper({})

    assert asyncio.run(scraper._get_all_urls_products("")) == []
    assert scraper.transport.requested == []


# --- product ---


def get_product(scraper: Scraper, url: str = f"{SHOP}/product/a"):
    return asyncio.run(scraper._get_product(url))


def test_product_parsed():
    scraper = make_scraper({f"{SHOP}/product/a.json": product_json()})

    product = get_product(scraper)

    assert product is not None
    assert product.title == "Товар"
    assert product.url == f"{SHOP}/product/a"
    assert product.images == ["https://shop.test/1.jpg"]
    assert product.variants[0].price == 99.5
    assert product.variants[0].sku is None


def test_product_trailing_slash():
    scraper = make_scraper({f"{SHOP}/product/a.json": product_json()})

    assert get_product(scraper, f"{SHOP}/product/a/") is not None


def test_product_no_images_and_no_variants():
    scraper = make_scraper(
        {f"{SHOP}/product/a.json": product_json(images=[], variants=[])}
    )

    product = get_product(scraper)

    assert product is not None
    assert product.images == []
    assert product.variants == []


@pytest.mark.parametrize(
    "body",
    [
        "",
        "not json",
        "{}",
        json.dumps({"product": {}}),
        json.dumps({"product": {"id": 1}}),
    ],
)
def test_product_malformed(body: str):
    scraper = make_scraper({f"{SHOP}/product/a.json": body})

    assert get_product(scraper) is None


@pytest.mark.parametrize("overrides", [{"variants": [{"id": 1}]}, {"images": [{}]}])
def test_product_broken_fields(overrides: dict):
    scraper = make_scraper({f"{SHOP}/product/a.json": product_json(**overrides)})

    assert get_product(scraper) is None


def test_product_null_variants():
    scraper = make_scraper({f"{SHOP}/product/a.json": product_json(variants=None)})

    assert get_product(scraper) is None


def test_product_transport_error_skipped():
    scraper = make_scraper({f"{SHOP}/product/a.json": transport_error()})

    assert get_product(scraper) is None


def test_product_transport_error_fail_fast():
    scraper = make_scraper(
        {f"{SHOP}/product/a.json": transport_error()}, fail_on_request_error=True
    )

    with pytest.raises(TransportError):
        get_product(scraper)


# --- scrape ---


def test_scrape_returns_products():
    scraper = make_scraper(
        {
            f"{SHOP}/sitemap.xml": sitemap(f"{SHOP}/product/a", f"{SHOP}/product/b"),
            f"{SHOP}/product/a.json": product_json(id=1),
            f"{SHOP}/product/b.json": product_json(id=2),
        }
    )

    products = asyncio.run(scraper.scrape(SHOP))

    assert sorted(p.id for p in products) == [1, 2]
    assert scraper.transport.closed


def test_scrape_empty_sitemap():
    scraper = make_scraper({f"{SHOP}/sitemap.xml": sitemap()})

    assert asyncio.run(scraper.scrape(SHOP)) == []
    assert scraper.transport.closed


def test_scrape_skips_failed_products():
    scraper = make_scraper(
        {
            f"{SHOP}/sitemap.xml": sitemap(
                f"{SHOP}/product/a", f"{SHOP}/product/b", f"{SHOP}/product/c"
            ),
            f"{SHOP}/product/a.json": product_json(id=1),
            f"{SHOP}/product/b.json": transport_error(),
            f"{SHOP}/product/c.json": "not json",
        }
    )

    products = asyncio.run(scraper.scrape(SHOP))

    assert [p.id for p in products] == [1]


def test_scrape_all_products_failed():
    scraper = make_scraper(
        {
            f"{SHOP}/sitemap.xml": sitemap(f"{SHOP}/product/a"),
            f"{SHOP}/product/a.json": transport_error(),
        }
    )

    assert asyncio.run(scraper.scrape(SHOP)) == []


def test_scrape_sitemap_failure_closes_transport():
    scraper = make_scraper({f"{SHOP}/sitemap.xml": transport_error()})

    with pytest.raises(TransportError):
        asyncio.run(scraper.scrape(SHOP))

    assert scraper.transport.closed


def test_scrape_fail_fast_closes_transport():
    scraper = make_scraper(
        {
            f"{SHOP}/sitemap.xml": sitemap(f"{SHOP}/product/a"),
            f"{SHOP}/product/a.json": transport_error(),
        },
        fail_on_request_error=True,
    )

    with pytest.raises(TransportError):
        asyncio.run(scraper.scrape(SHOP))

    assert scraper.transport.closed
