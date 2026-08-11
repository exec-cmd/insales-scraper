# Inscrap — Insales Scraper

`Inscrap` — CLI-утилита для выгрузки товаров с сайтов на платформе [InSales](https://www.insales.ru/). Она находит товарные страницы в `sitemap.xml`, загружает сведения о каждом товаре через JSON API и сохраняет результат в файл.

## Возможности

- Сбор названий, описаний, ссылок, наличия, изображений и вариантов товаров.
- Экспорт в JSON, CSV, XLSX и TXT.
- Настройка параллельных запросов, повторных попыток и HTTP-транспорта.

## Требования

- Python 3.13 или новее.
- Рекомендуемый менеджер пакетов: [uv](https://docs.astral.sh/uv/).

## Глобальная установка

Глобальная установка делает команду `inscrap` доступной из любого каталога. Выберите один из способов ниже.

### Из исходного кода

Из корневой директории клонированного репозитория выполните:

```bash
uv tool install .
```

### Из wheel-пакета (`.whl`)

Сначала соберите дистрибутив:

```bash
uv build
```

Команда создаст wheel-файл в каталоге `dist/`, например `dist/insales_scraper-1.0-py3-none-any.whl`. Установите его как глобальный инструмент:

```bash
uv tool install dist/insales_scraper-1.0-py3-none-any.whl
```

Если wheel-файл уже получен отдельно, укажите путь к нему:

```bash
uv tool install /path/to/insales_scraper-1.0-py3-none-any.whl
```

После установки проверьте команду:

```bash
inscrap run --help
```

### Удаление глобальной установки

```bash
uv tool uninstall insales-scraper
```

## Использование

Передайте адрес главной страницы магазина или прямой адрес его sitemap:

```bash
inscrap run https://shop.example.com
inscrap run https://shop.example.com/sitemap.xml
```

По умолчанию результат будет записан в `products.json` в текущей директории. Путь и формат определяются параметром `-o` / `--output`:

```bash
inscrap run https://shop.example.com -o data/products.json
inscrap run https://shop.example.com -o data/products.csv
inscrap run https://shop.example.com -o data/products.xlsx
inscrap run https://shop.example.com -o data/products.txt
```

Для запуска без глобальной установки используйте `uv run`:

```bash
uv run inscrap run https://shop.example.com -o products.xlsx
```

### Параметры

| Параметр | Описание | По умолчанию |
| --- | --- | --- |
| `-o`, `--output` | Путь к выходному файлу (`.json`, `.csv`, `.xlsx` или `.txt`) | `products.json` |
| `-c`, `--concurrency` | Число одновременных запросов (1–50) | `5` |
| `-r`, `--retries` | Число попыток запроса | `5` |
| `-t`, `--transport` | HTTP-транспорт: `httpx` или `curl_cffi` | `httpx` |
| `-f`, `--fatalist` | Остановить обработку при первой ошибке запроса товара | выключен |

Просмотреть доступные транспорты:

```bash
inscrap transport
```

## Форматы данных

JSON сохраняет полную вложенную структуру товаров и вариантов. CSV и XLSX содержат по одной строке на вариант товара; поля товара при этом повторяются для каждого варианта.

## Технологии

- CLI: `Typer`, `Rich`
- HTTP: `httpx`, `curl-cffi`
- Экспорт: `polars`, `xlsxwriter`
