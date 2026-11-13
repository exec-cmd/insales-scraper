import json
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

import polars as pl
from xlsxwriter import Workbook

from .models import Product


def _to_dataframe(content: list[Product]) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "product_id": product.id,
                "product_title": product.title,
                "description": product.description,
                "url": product.url,
                "product_available": product.available,
                "images": "; ".join(product.images),
                "variant_id": variant.id,
                "variant_title": variant.title,
                "sku": variant.sku,
                "barcode": variant.barcode,
                "variant_available": variant.available,
                "quantity": variant.quantity,
                "price": variant.price,
                "old_price": variant.old_price,
            }
            for product in content
            for variant in product.variants
        ],
        infer_schema_length=None,
    )


class Exporter:
    def __init__(self):
        self._save_handlers: dict[str, Callable[[Path, list[Product]], None]] = {
            ".xlsx": self._save_to_excel,
            ".csv": self._save_to_csv,
            ".json": self._save_to_json,
            ".txt": self._save_to_txt,
        }

    def save(self, path: Path, content: list[Product]) -> None:
        if path.suffix in self._save_handlers:
            self._save_handlers[path.suffix](path, content)
        else:
            raise ValueError(f"Unsupported file format: {path}")

    def _save_to_excel(self, path: Path, content: list[Product]) -> None:
        with Workbook(path, {"strings_to_urls": False}) as workbook:
            _ = _to_dataframe(content).write_excel(workbook)

    def _save_to_csv(self, path: Path, content: list[Product]) -> None:
        _to_dataframe(content).write_csv(path)

    def _save_to_json(self, path: Path, content: list[Product]) -> None:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                [asdict(product) for product in content],
                file,
                ensure_ascii=False,
                indent=4,
            )

    def _save_to_txt(self, path: Path, content: list[Product]) -> None:
        with open(path, "w", encoding="utf-8") as file:
            file.writelines(f"{product}\n" for product in content)
