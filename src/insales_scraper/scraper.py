import asyncio
import json
import logging
from json.decoder import JSONDecodeError
from xml.etree import ElementTree

from rich.progress import track

from .config import config
from .console import console
from .models import Product, Variant
from .transports import TRANSPORT_VARIANTS, Transport

logger = logging.getLogger(__name__)


class Scraper:
    def __init__(self):
        transport_cls = TRANSPORT_VARIANTS[config.transport]

        self.transport: Transport = transport_cls()

    async def scrape(self, url) -> list[Product]:
        async with self.transport:
            urls = await self._get_all_urls_products(url)

            if not urls:
                return []

            console.print("\n")  # Empty String for spacing

            products = [
                await task
                for task in track(
                    asyncio.as_completed(
                        self._get_product(product_url) for product_url in urls
                    ),
                    total=len(urls),
                    description="Загрузка товаров",
                    console=console,
                )
            ]  # Progress Bar

            empty_products = [p for p in products if p is None]
            products = [p for p in products if p is not None]

            console.print(f"\n\n[green]✓ Найдено товаров:[/green] {len(products)}")
            console.print(
                f"[yellow]⚠ Пропущено из-за ошибок:[/yellow] {len(empty_products)}"
            )

        return products

    async def _get_all_urls_products(self, url: str) -> list[str]:
        if not url:
            return []

        url = url.rstrip("/")
        if not url.endswith("xml"):
            url += "/sitemap.xml"

        response = await self.transport.request(url)
        xml_data = response

        list_urls_products = self._get_products_from_sitemap(xml_data)
        logger.info(f"Found {len(list_urls_products)} products in sitemap")

        return list_urls_products

    async def _get_product(self, product_url: str) -> Product | None:
        api_url = product_url.rstrip("/") + ".json"

        try:
            response = await self.transport.request(api_url)
        except Exception as e:
            logger.error(f"Failed to get product {product_url}: {e}")

            if config.fatalist:
                raise

            return None

        try:
            data = json.loads(response)["product"]
        except (JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse product {product_url}: {e}")
            return None

        try:
            variants = self._get_variants(data["variants"])

            if variants is None:
                raise KeyError("No variants found")

            product = Product(
                id=data["id"],
                title=data["title"],
                description=data["description"],
                url=product_url,
                available=data["available"],
                images=[image["original_url"] for image in data["images"]],
                variants=variants,
            )
        except KeyError as e:
            logger.error(f"Failed to parse product {product_url}: {e}")
            return None

        return product

    def _get_variants(self, variants_data: list[dict]) -> list[Variant] | None:
        variants = []

        try:
            for data in variants_data:
                variant = Variant(
                    id=data["id"],
                    title=data["title"],
                    sku=data["sku"],
                    barcode=data["barcode"],
                    available=data["available"],
                    quantity=data["quantity"],
                    price=data["price"],
                    old_price=data["old_price"],
                )

                variants.append(variant)
        except KeyError as e:
            logger.error(f"Failed to parse variants: {e}")
            return None

        return variants

    def _get_products_from_sitemap(self, xml: str) -> list[str]:
        try:
            root = ElementTree.fromstring(xml)

            return [
                element.text.strip()
                for element in root.iter()
                if element.tag.split("}")[-1] == "loc"
                and element.text
                and "/product/" in element.text
            ]
        except ElementTree.ParseError as e:
            logger.error(f"Failed to parse sitemap: {e}")
            return []
