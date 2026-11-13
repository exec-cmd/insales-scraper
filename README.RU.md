[English](README.md) · Русский

<p align="center">
  <img src="assets/logo.svg" width="128" alt="Логотип Inscrap">
</p>

# Inscrap

[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![Версия](https://img.shields.io/badge/версия-1.3.0-green)](pyproject.toml)
[![Лицензия: MIT](https://img.shields.io/badge/лицензия-MIT-lightgrey)](LICENSE)

**Выгрузка каталога любого магазина на [InSales](https://www.insales.ru/) в JSON, CSV, XLSX или TXT одной командой.**

Inscrap берёт ссылки на товары из `sitemap.xml` магазина, запрашивает каждый
товар через его JSON-эндпоинт и сохраняет названия, описания, цены, остатки,
изображения и варианты в файл. Выгрузку можно запускать по расписанию, а в Linux
установить как пользовательский сервис systemd.

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Установка](#установка)
- [Использование](#использование)
- [Расписание и автозапуск](#расписание-и-автозапуск)
- [Что попадёт в выгрузку](#что-попадёт-в-выгрузку)
- [Как это работает](#как-это-работает)
- [Разработка](#разработка)

## Быстрый старт

Нужны Python 3.13+ и, желательно, [uv](https://docs.astral.sh/uv/).

Из клонированного репозитория, без установки:

```bash
uv run inscrap run https://shop.example.com -o products.xlsx
```

Вместо адреса магазина можно передать ссылку на sitemap:

```bash
uv run inscrap run https://shop.example.com/sitemap.xml
```

Без `-o` результат сохранится в `output.json` в текущем каталоге.

## Установка

Установка как глобального инструмента `uv` — `inscrap` будет доступен из любого каталога:

```bash
uv tool install .
inscrap run --help   # проверка
```

Либо соберите wheel и установите его:

```bash
uv build
uv tool install dist/insales_scraper-1.3.0-py3-none-any.whl
```

Удаление:

```bash
uv tool uninstall insales-scraper
```

## Использование

```bash
inscrap run URL [OPTIONS]
inscrap transport                        # список доступных HTTP-транспортов
inscrap install-service URL [OPTIONS]    # запуск как сервис systemd (Linux)
inscrap uninstall                        # удалить этот сервис
```

Формат результата определяется расширением файла:

```bash
inscrap run https://shop.example.com -o products.json
inscrap run https://shop.example.com -o products.csv
inscrap run https://shop.example.com -o products.xlsx
inscrap run https://shop.example.com -o products.txt
```

> [!NOTE]
> Каталог для выходного файла должен существовать заранее (`mkdir -p data`).

### Параметры

`run` и `install-service` принимают одни и те же параметры.

| Параметр | Что делает | По умолчанию |
| --- | --- | --- |
| `-o`, `--output` | Путь к результату. Формат задаётся расширением `.json`, `.csv`, `.xlsx` или `.txt`. | `output.json` |
| `-c`, `--concurrency` | Одновременных запросов товаров, 1–50. | `5` |
| `-r`, `--retries` | Максимум попыток запроса на один адрес, включая первую, 1–50. | `5` |
| `-t`, `--transport` | HTTP-клиент: `httpx` или `curl_cffi`. Список — `inscrap transport`. | `httpx` |
| `-f`, `--fail-fast` | Прервать всю выгрузку после первой ошибки запроса товара. | выкл. |
| `-p`, `--proxy` | URL прокси-сервера для HTTP-запросов. | не задан |
| `--interval` | Пауза между запусками в секундах, минимум 1. | `15` |
| `--count` | Количество запусков, минимум 1. | `1` |

Для большого каталога повышайте параллелизм постепенно, чтобы не перегружать магазин:

```bash
inscrap run https://shop.example.com -c 10 -r 3 -o catalog.csv
```

## Расписание и автозапуск

`--count` выполняет выгрузку несколько раз подряд с паузой `--interval` секунд.
**Каждый запуск перезаписывает выходной файл**, поэтому в нём всегда последний снимок:

```bash
inscrap run https://shop.example.com -o data/catalog.json --count 24 --interval 3600
```

В Linux с systemd `install-service` принимает те же аргументы, что и `run`, и
записывает пользовательский юнит в `~/.config/systemd/user/inscrap.service`.
Сразу после этого юнит включается и запускается. Команда `inscrap` должна быть в `PATH`,
поэтому сначала установите инструмент через `uv tool install .`.

```bash
inscrap install-service https://shop.example.com -o data/catalog.csv --count 24 --interval 3600
inscrap uninstall
```

Юнит перезапускается при сбое. Обе команды вызывают `systemctl --user`.

## Что попадёт в выгрузку

Для каждого товара сохраняются идентификатор, название, описание, ссылка,
наличие, изображения и варианты. У варианта — свои идентификатор, название,
SKU, штрихкод, наличие, остаток, цена и старая цена.

| Формат | Структура |
| --- | --- |
| JSON | Полная вложенная структура: товары с вариантами. |
| CSV / XLSX | Одна строка на вариант; поля товара повторяются в каждой строке. Изображения объединены через `; `. |
| TXT | Текстовое представление каждого товара. |

## Как это работает

1. Открывает переданный `sitemap.xml` (для адреса магазина добавляет `/sitemap.xml`).
2. Оставляет ссылки, содержащие `/product/`.
3. Запрашивает JSON каждого товара, добавляя `.json` к его URL.
4. Сохраняет загруженные товары. Товары с ошибками по умолчанию пропускаются и учитываются в итоговой статистике; с `--fail-fast` выгрузка прерывается.

## Разработка

```bash
uv sync
uv run pytest
make fmt   # ruff format + check --fix
make chk   # fmt, затем pytest
```

Стек: [Typer](https://typer.tiangolo.com/) и [Rich](https://github.com/Textualize/rich) (CLI),
[httpx](https://www.python-httpx.org/) / [curl-cffi](https://github.com/lexiforest/curl_cffi) (HTTP),
[polars](https://pola.rs/) и [xlsxwriter](https://xlsxwriter.readthedocs.io/) (экспорт).

## Лицензия

[MIT](LICENSE)
