# Inscrap

Inscrap is a small command-line tool for exporting product catalogs from
[InSales](https://www.insales.ru/) stores. It reads product URLs from a
`sitemap.xml`, fetches product data through the store's JSON API, and writes
the result to a file.

It is useful when you need to quickly collect product titles, descriptions,
prices, stock levels, images, and variants without browsing the catalog
manually.

[Русская версия](README_RU.md)

## Quick start

Requirements: Python 3.13 or newer and, preferably, [uv](https://docs.astral.sh/uv/).

Run Inscrap directly from a cloned repository:

```bash
uv run inscrap run https://shop.example.com -o products.xlsx
```

You can pass a sitemap URL instead of the store URL:

```bash
uv run inscrap run https://shop.example.com/sitemap.xml
```

Without `-o`, the result is saved as `products.json` in the current directory.

## Installation

Install Inscrap as a global `uv` tool to use it from any directory:

```bash
uv tool install .
```

Check the installation:

```bash
inscrap run --help
```

You can also build and install a wheel:

```bash
uv build
uv tool install dist/insales_scraper-1.1.0-py3-none-any.whl
```

Or install a wheel from a specific path:

```bash
uv tool install /path/to/insales_scraper-1.0-py3-none-any.whl
```

Remove the global installation with:

```bash
uv tool uninstall insales-scraper
```

## Usage

After installation, the command is:

```bash
inscrap run URL [OPTIONS]
```

Choose the output format by changing the file extension:

```bash
inscrap run https://shop.example.com -o products.json
inscrap run https://shop.example.com -o products.csv
inscrap run https://shop.example.com -o products.xlsx
inscrap run https://shop.example.com -o products.txt
```

The output directory must already exist:

```bash
mkdir -p data
inscrap run https://shop.example.com -o data/catalog.xlsx
```

### Request options

| Option | Description | Default |
| --- | --- | --- |
| `-o`, `--output` | Output path. The format is selected by the `.json`, `.csv`, `.xlsx`, or `.txt` extension. | `products.json` |
| `-c`, `--concurrency` | Number of concurrent requests, from 1 to 50. | `5` |
| `-r`, `--retries` | Number of retry attempts after a request error. | `5` |
| `-t`, `--transport` | HTTP transport: `httpx` or `curl_cffi`. | `httpx` |
| `-f`, `--fatalist` | Stop the export after the first product request error. | disabled |
| `-p`, `--proxy` | Proxy URL used for HTTP requests. | not set |

For a large catalog, increase concurrency gradually so you do not put
unnecessary load on the store:

```bash
inscrap run https://shop.example.com -c 10 -r 3 -o catalog.csv
```

List the available HTTP transports with:

```bash
inscrap transport
```

## Exported data

Each product includes its ID, title, description, URL, availability, images,
and variants. Each variant includes its own ID, title, SKU, barcode,
availability, quantity, current price, and old price.

| Format | Data layout |
| --- | --- |
| JSON | The complete nested structure with products and their variants. |
| CSV / XLSX | One row per variant. Product fields are repeated for each of its variants. |
| TXT | A text representation of the scraped products. |

## How it works

1. Inscrap opens the provided `sitemap.xml`. If you pass a store URL, it adds `/sitemap.xml`.
2. It keeps sitemap links that contain `/product/`.
3. It requests the JSON version of each product page by adding `.json` to the product URL.
4. It saves successfully loaded products to the selected file. By default, products with errors are skipped, and their number is included in the final statistics.

## Built with

`Typer` and `Rich` power the CLI. HTTP requests use `httpx` or `curl-cffi`,
and exports use `polars` and `xlsxwriter`.
