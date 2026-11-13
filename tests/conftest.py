import pytest

from insales_scraper.models import Product, Variant


def make_variant(**kwargs) -> Variant:
    defaults = {
        "id": 1,
        "title": "Default",
        "sku": "SKU-1",
        "barcode": "123",
        "available": True,
        "quantity": 5,
        "price": 100.0,
        "old_price": 150.0,
    }
    return Variant(**(defaults | kwargs))


def make_product(**kwargs) -> Product:
    defaults = {
        "id": 1,
        "title": "Товар",
        "description": "Описание",
        "url": "https://shop.test/product/one",
        "available": True,
        "images": ["https://shop.test/1.jpg", "https://shop.test/2.jpg"],
        "variants": [make_variant()],
    }
    return Product(**(defaults | kwargs))


@pytest.fixture
def product() -> Product:
    return make_product()
