English · [Русский](README.RU.md)

<p align="center">
  <img src="assets/logo.svg" width="128" alt="Inscrap logo">
</p>

# Inscrap

[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.3.0-green)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

**Export a product catalog from any [InSales](https://www.insales.ru/) store to JSON, CSV, XLSX, or TXT with a single command.**

Inscrap reads product URLs from the store's `sitemap.xml`, fetches each product
through its JSON endpoint, and saves titles, descriptions, prices, stock levels,
images, and variants to a file. It can run on a schedule and install itself as a
systemd user service on Linux.

## Contents

- [Quick start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Scheduled runs and autostart](#scheduled-runs-and-autostart)
- [Exported data](#exported-data)
- [How it works](#how-it-works)
- [Development](#development)

## Quick start

Requirements: Python 3.13+ and [uv](https://docs.astral.sh/uv/) (recommended).

From a cloned repository, no installation needed:

```bash
uv run inscrap run https://shop.example.com -o products.xlsx
```

You can pass the sitemap URL instead of the store URL:

```bash
uv run inscrap run https://shop.example.com/sitemap.xml
```

Without `-o`, the result is saved to `output.json` in the current directory.

## Installation

Install as a global `uv` tool to run `inscrap` from any directory:

```bash
uv tool install .
inscrap run --help   # verify
```

Or build a wheel and install it:

```bash
uv build
uv tool install dist/insales_scraper-1.3.0-py3-none-any.whl
```

Uninstall:

```bash
uv tool uninstall insales-scraper
```

## Usage

```bash
inscrap run URL [OPTIONS]
inscrap transport                 # list available HTTP transports
inscrap install-service URL [OPTIONS]   # run as a systemd user service (Linux)
inscrap uninstall                 # remove that service
```

The output format follows the file extension:

```bash
inscrap run https://shop.example.com -o products.json
inscrap run https://shop.example.com -o products.csv
inscrap run https://shop.example.com -o products.xlsx
inscrap run https://shop.example.com -o products.txt
```

> [!NOTE]
> The output directory must already exist (`mkdir -p data`).

### Options

`run` and `install-service` accept the same options.

| Option | Description | Default |
| --- | --- | --- |
| `-o`, `--output` | Output path. Format is chosen by the `.json`, `.csv`, `.xlsx`, or `.txt` extension. | `output.json` |
| `-c`, `--concurrency` | Maximum simultaneous product requests, 1–50. | `5` |
| `-r`, `--retries` | Maximum request attempts per URL, including the first one, 1–50. | `5` |
| `-t`, `--transport` | HTTP client: `httpx` or `curl_cffi`. See `inscrap transport`. | `httpx` |
| `-f`, `--fail-fast` | Abort the whole run after the first product request fails. | off |
| `-p`, `--proxy` | Proxy URL for HTTP requests. | none |
| `--interval` | Seconds to wait between runs, minimum 1. | `15` |
| `--count` | Number of runs, minimum 1. | `1` |

For large catalogs, raise concurrency gradually to avoid overloading the store:

```bash
inscrap run https://shop.example.com -c 10 -r 3 -o catalog.csv
```

## Scheduled runs and autostart

`--count` runs the scrape several times in a row, waiting `--interval` seconds
between runs. **Each run overwrites the output file**, so the file always holds
the latest snapshot:

```bash
inscrap run https://shop.example.com -o data/catalog.json --count 24 --interval 3600
```

On Linux with systemd, `install-service` takes the same arguments as `run` and
writes a user unit to `~/.config/systemd/user/inscrap.service`. It enables and
starts the unit right away. The command must be on `PATH`, so install the tool
with `uv tool install .` first.

```bash
inscrap install-service https://shop.example.com -o data/catalog.csv --count 24 --interval 3600
inscrap uninstall
```

The unit restarts on failure. Both commands call `systemctl --user`.

## Exported data

Each product has an ID, title, description, URL, availability, images, and
variants. Each variant has its own ID, title, SKU, barcode, availability,
quantity, price, and old price.

| Format | Layout |
| --- | --- |
| JSON | Full nested structure: products with their variants. |
| CSV / XLSX | One row per variant; product fields repeat on each row. Images are joined with `; `. |
| TXT | Text representation of each product. |

## How it works

1. Opens the given `sitemap.xml` (for a store URL, appends `/sitemap.xml`).
2. Keeps links containing `/product/`.
3. Requests each product's JSON by appending `.json` to its URL.
4. Saves the loaded products. Failed products are skipped by default and counted in the final summary; use `--fail-fast` to abort instead.

## Development

```bash
uv sync
uv run pytest
make fmt   # ruff format + check --fix
make chk   # fmt, then pytest
```

Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://github.com/Textualize/rich) (CLI),
[httpx](https://www.python-httpx.org/) / [curl-cffi](https://github.com/lexiforest/curl_cffi) (HTTP),
and [polars](https://pola.rs/) / [xlsxwriter](https://xlsxwriter.readthedocs.io/) (export).

## License

[MIT](LICENSE)
