import asyncio
import logging
import platform
import shutil
import time
from pathlib import Path
from typing import Annotated

from rich.table import Table
from typer import Argument, Option, Typer

from insales_scraper import systemd
from insales_scraper.models import Product

from .config import Config, default_config
from .console import console
from .exporter import Exporter
from .scraper import Scraper
from .transports import TRANSPORT_VARIANTS

logger = logging.getLogger(__name__)
app = Typer()


@app.command(no_args_is_help=True)
def run(
    url: Annotated[str, Argument(help="URL to scrape")],
    output: Annotated[
        Path,
        Option("-o", "--output", help="Path to the output file"),
    ] = default_config.output_file_path,
    concurrency: Annotated[
        int,
        Option(
            "-c",
            "--concurrency",
            min=1,
            max=50,
            help="Maximum number of simultaneous product requests (1–50)",
        ),
    ] = default_config.max_concurrent_requests,
    retries: Annotated[
        int,
        Option(
            "-r",
            "--retries",
            min=1,
            max=50,
            help="Maximum request attempts, including the first attempt (1–50)",
        ),
    ] = default_config.max_request_attempts,
    transport: Annotated[
        str,
        Option("-t", "--transport", help="HTTP client used to send requests"),
    ] = default_config.transport_backend,
    fail_fast: Annotated[
        bool,
        Option(
            "-f", "--fail-fast", help="Abort the scrape after a product request fails"
        ),
    ] = default_config.fail_on_request_error,
    proxy: Annotated[
        str | None,
        Option("-p", "--proxy", help="Proxy URL for HTTP requests"),
    ] = default_config.proxy_url,
    interval: Annotated[
        float,
        Option("--interval", min=1, help="Seconds to wait between runs (minimum 1)"),
    ] = default_config.interval_between_runs_seconds,
    count: Annotated[
        int, Option("--count", min=1, help="Number of scrape runs (minimum 1)")
    ] = default_config.number_of_runs,
) -> None:
    logger.info(
        f"url: {url}, output: {output}, max concurrent requests: {concurrency}, max request attempts: {retries}, transport: {transport}, proxy configured: {bool(proxy)}, interval between runs: {interval} seconds; number of runs: {count}"
    )

    console.print(f"[italic]Начинаем выгрузку товаров из {url}…[/italic]")

    config = Config(
        max_concurrent_requests=concurrency,
        max_request_attempts=retries,
        transport_backend=transport,
        fail_on_request_error=fail_fast,
        proxy_url=proxy,
        output_file_path=output,
        interval_between_runs_seconds=interval,
        number_of_runs=count,
    )

    for i in range(config.number_of_runs):
        console.print(
            f"\n\n[bold]Запуск {i + 1} из {config.number_of_runs}[/bold]"
            if config.number_of_runs > 1
            else "",
        )

        content = asyncio.run(scrape(url, config))

        export(output, content)

        console.print("[italic]Выгрузка завершена [green]✔[/green][/italic]")

        if i + 1 == config.number_of_runs:
            if config.number_of_runs > 1:
                console.print("\n\n[bold]Все запуски завершены[/bold]")
            break

        console.print(
            f"\n\n[italic]Следующий запуск через {config.interval_between_runs_seconds} с…[/italic]"
        )

        time.sleep(config.interval_between_runs_seconds)


async def scrape(url: str, config: Config = default_config) -> list[Product]:
    scraper = Scraper(config)
    products = await scraper.scrape(url)

    return products


def export(path: Path, content: list[Product]) -> None:
    console.print(f"\n\n[italic]Сохраняем результаты в {path} ...[/italic]")

    exporter = Exporter()
    exporter.save(path, content)


@app.command()
def transport():
    table = Table()

    table.add_column("Название", style="cyan")
    table.add_column("Статус", style="green")

    for name in TRANSPORT_VARIANTS:
        status = "по умолчанию" if name == default_config.transport_backend else ""
        table.add_row(name, status)

    console.print(table)


@app.command()
def install_service(
    url: Annotated[str, Argument(help="URL to scrape")],
    output: Annotated[
        Path,
        Option("-o", "--output", help="Path to the output file"),
    ] = default_config.output_file_path,
    concurrency: Annotated[
        int,
        Option(
            "-c",
            "--concurrency",
            min=1,
            max=50,
            help="Maximum number of simultaneous product requests (1–50)",
        ),
    ] = default_config.max_concurrent_requests,
    retries: Annotated[
        int,
        Option(
            "-r",
            "--retries",
            min=1,
            max=50,
            help="Maximum request attempts, including the first attempt (1–50)",
        ),
    ] = default_config.max_request_attempts,
    transport: Annotated[
        str,
        Option("-t", "--transport", help="HTTP client used to send requests"),
    ] = default_config.transport_backend,
    fail_fast: Annotated[
        bool,
        Option(
            "-f", "--fail-fast", help="Abort the scrape after a product request fails"
        ),
    ] = default_config.fail_on_request_error,
    proxy: Annotated[
        str | None,
        Option("-p", "--proxy", help="Proxy URL for HTTP requests"),
    ] = default_config.proxy_url,
    interval: Annotated[
        float,
        Option("--interval", min=1, help="Seconds to wait between runs (minimum 1)"),
    ] = default_config.interval_between_runs_seconds,
    count: Annotated[
        int, Option("--count", min=1, help="Number of scrape runs (minimum 1)")
    ] = default_config.number_of_runs,
):
    if platform.system() != "Linux":
        console.print("[red]Для этой функции поддерживается только Linux-системы[/red]")
        return
    if not shutil.which("systemctl"):
        console.print(
            "[red]Systemd нету в системе, без него эта функция не поддерживается[/red]"
        )
        return

    try:
        systemd.install_service(
            url,
            output,
            concurrency,
            retries,
            transport,
            fail_fast,
            proxy,
            interval,
            count,
        )
    except RuntimeError:
        console.print(
            "[red]Вероятно команда inscrap не найдена. Установите проект в окружение[/red]"
        )


@app.command()
def uninstall():
    if platform.system() != "Linux":
        console.print("[red]Для этой функции поддерживается только Linux-системы[/red]")
        return
    if not shutil.which("systemctl"):
        console.print(
            "[red]Systemd нету в системе, без него эта функция не поддерживается[/red]"
        )
        return

    try:
        systemd.uninstall_service()
    except RuntimeError:
        console.print("[red]Вероятно у вас не был установлен сервис[/red]")
