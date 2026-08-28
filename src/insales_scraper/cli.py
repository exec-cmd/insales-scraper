import asyncio
import logging
from pathlib import Path

from rich.table import Table
from typer import Argument, Option, Typer

from .config import Config, default_config
from .console import console
from .exporter import Exporter
from .scraper import Scraper
from .transports import TRANSPORT_VARIANTS

logger = logging.getLogger(__name__)

URL_flag = Argument(..., help="URL to scrape")
Output_flag = Option(Path("products.json"), "-o", "--output", help="Output file path")
Concurrency_flag = Option(
    default_config.concurrency,
    "-c",
    "--concurrency",
    min=1,
    max=50,
    help="Number of concurrent workers",
)
Retries_flag = Option(
    default_config.retries, "-r", "--retries", min=1, max=50, help="Number of retries"
)
Transport_flag = Option(
    default_config.transport, "-t", "--transport", help="Transport layer"
)
Fatalist_flag = Option(
    default_config.fatalist, "-f", "--fatalist", help="Stop on first request error"
)
Proxy_flag = Option(default_config.proxy, "-p", "--proxy", help="Proxy URL")


app = Typer()


@app.command(no_args_is_help=True)
def run(
    url: str = URL_flag,
    output: Path = Output_flag,
    concurrency: int = Concurrency_flag,
    retries: int = Retries_flag,
    transport: str = Transport_flag,
    fatalist: bool = Fatalist_flag,
    proxy: str = Proxy_flag,
):
    logger.info(
        f"url: {url}, output: {output}, concurrency: {concurrency}, retries: {retries}, transport: {transport}, proxy: {bool(proxy)}"
    )

    console.print(f"[italic]Начинаем парсинг {url} ...[/italic]")

    config = Config(
        concurrency=concurrency,
        retries=retries,
        transport=transport,
        fatalist=fatalist,
        proxy=proxy,
    )

    content = asyncio.run(scrape(url, config))

    export(output, content)

    console.print("[italic]Парсинг завершен [green]✔[/green][/italic]")


async def scrape(url: str, config=default_config):
    scraper = Scraper(config)
    products = await scraper.scrape(url)

    return products


def export(path, content: list):
    console.print(f"\n\n[italic]Сохраняем результаты в {path} ...[/italic]")

    exporter = Exporter()
    exporter.save(path, content)


@app.command()
def transport():
    table = Table()

    table.add_column("Название", style="cyan")
    table.add_column("Статус", style="green")

    for name in TRANSPORT_VARIANTS:
        status = "по умолчанию" if name == default_config.transport else ""
        table.add_row(name, status)

    console.print(table)
