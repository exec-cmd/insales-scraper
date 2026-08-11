# Repository Guide

## Overview

`insales-scraper` is a Python 3.13 CLI that discovers InSales product URLs from a sitemap, fetches product JSON, and exports results.

## Layout

- `src/insales_scraper/cli.py`: Typer commands and CLI options.
- `scraper.py`: sitemap parsing and product collection.
- `transports/`: asynchronous HTTP transport implementations.
- `exporter.py`: JSON, CSV, XLSX, and TXT output.

## Development

Use `uv sync` to install dependencies. Run the CLI with `uv run inscrap run --help`; run tests with `uv run pytest` when tests are present. Keep changes focused, preserve public CLI behavior, and add tests for new behavior where practical.
