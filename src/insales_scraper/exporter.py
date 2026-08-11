import json
from dataclasses import asdict
from pathlib import Path

import polars as pl
import xlsxwriter

from .models import Product


class Exporter:
    def save(self, path: Path, content: list[Product]):
        if path.suffix == ".xlsx":
            self._save_to_excel(path, content)
        elif path.suffix == ".csv":
            self._save_to_csv(path, content)
        elif path.suffix == ".json":
            self._save_to_json(path, content)
        elif path.suffix == ".txt":
            self._save_to_txt(path, content)
        else:
            raise ValueError(f"Unsupported file format: {path}")

    def _save_to_excel(self, path: Path, content: list[Product]):
        with xlsxwriter.Workbook(path, {"strings_to_urls": False}) as workbook:
            self._to_dataframe(content).write_excel(workbook)

    def _save_to_csv(self, path: Path, content: list[Product]):
        self._to_dataframe(content).write_csv(path)

    def _save_to_json(self, path: Path, content: list[Product]):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(
                [asdict(product) for product in content],
                file,
                ensure_ascii=False,
                indent=4,
            )

    def _save_to_txt(self, path: Path, content: list[Product]):
        with open(path, "w", encoding="utf-8") as file:
            file.writelines(f"{product}\n" for product in content)

    def _to_dataframe(self, content: list[Product]) -> pl.DataFrame:
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
