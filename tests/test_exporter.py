import json
import zipfile
from pathlib import Path

import polars as pl
import pytest

from insales_scraper.exporter import Exporter
from insales_scraper.models import Product

from .conftest import make_product, make_variant

exporter = Exporter()


@pytest.mark.parametrize("suffix", [".json", ".csv", ".txt", ".xlsx"])
def test_save_creates_file(tmp_path: Path, product: Product, suffix: str):
    path = tmp_path / f"out{suffix}"

    exporter.save(path, [product])

    assert path.stat().st_size > 0


@pytest.mark.parametrize("name", ["out.xml", "out", "out.CSV", "out.json.bak"])
def test_save_unsupported_format(tmp_path: Path, product: Product, name: str):
    path = tmp_path / name

    with pytest.raises(ValueError, match="Unsupported"):
        exporter.save(path, [product])

    assert not path.exists()


def test_json_roundtrip(tmp_path: Path, product: Product):
    path = tmp_path / "out.json"

    exporter.save(path, [product])

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data[0]["title"] == "Товар"
    assert data[0]["variants"][0]["price"] == 100.0


def test_json_keeps_cyrillic(tmp_path: Path, product: Product):
    path = tmp_path / "out.json"

    exporter.save(path, [product])

    assert "Товар" in path.read_text(encoding="utf-8")


def test_json_empty(tmp_path: Path):
    path = tmp_path / "out.json"

    exporter.save(path, [])

    assert json.loads(path.read_text(encoding="utf-8")) == []


def test_json_product_without_variants(tmp_path: Path):
    path = tmp_path / "out.json"

    exporter.save(path, [make_product(variants=[])])

    assert json.loads(path.read_text(encoding="utf-8"))[0]["variants"] == []


def test_csv_row_per_variant(tmp_path: Path):
    path = tmp_path / "out.csv"
    variants = [make_variant(id=1), make_variant(id=2), make_variant(id=3)]

    exporter.save(path, [make_product(variants=variants)])

    df = pl.read_csv(path)
    assert df["variant_id"].to_list() == [1, 2, 3]
    assert df["product_id"].unique().to_list() == [1]


def test_csv_images_joined(tmp_path: Path, product: Product):
    path = tmp_path / "out.csv"

    exporter.save(path, [product])

    assert (
        pl.read_csv(path)["images"][0]
        == "https://shop.test/1.jpg; https://shop.test/2.jpg"
    )


def test_csv_no_images(tmp_path: Path):
    path = tmp_path / "out.csv"

    exporter.save(path, [make_product(images=[])])

    assert pl.read_csv(path)["images"][0] in ("", None)


def test_csv_none_fields(tmp_path: Path):
    path = tmp_path / "out.csv"
    variant = make_variant(sku=None, barcode=None, quantity=None, old_price=None)

    exporter.save(path, [make_product(description=None, variants=[variant])])

    row = pl.read_csv(path).row(0, named=True)
    assert row["description"] is None
    assert row["sku"] is None
    assert row["old_price"] is None


def test_csv_special_characters(tmp_path: Path):
    path = tmp_path / "out.csv"
    text = 'Строка, с "кавычками"\nи переводом строки'

    exporter.save(path, [make_product(description=text)])

    assert pl.read_csv(path)["description"][0] == text


def test_csv_empty(tmp_path: Path):
    path = tmp_path / "out.csv"

    exporter.save(path, [])

    assert path.exists()


def _xlsx_strings(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return archive.read("xl/sharedStrings.xml").decode("utf-8")


def test_xlsx_content(tmp_path: Path, product: Product):
    path = tmp_path / "out.xlsx"

    exporter.save(path, [product])

    assert "Товар" in _xlsx_strings(path)


def test_xlsx_url_stays_string(tmp_path: Path, product: Product):
    path = tmp_path / "out.xlsx"

    exporter.save(path, [product])

    with zipfile.ZipFile(path) as archive:
        assert b"<hyperlink" not in archive.read("xl/worksheets/sheet1.xml")


def test_xlsx_empty(tmp_path: Path):
    path = tmp_path / "out.xlsx"

    exporter.save(path, [])

    assert path.exists()


def test_txt_line_per_product(tmp_path: Path):
    path = tmp_path / "out.txt"
    products = [make_product(id=1), make_product(id=2)]

    exporter.save(path, products)

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "id=1" in lines[0]


def test_txt_empty(tmp_path: Path):
    path = tmp_path / "out.txt"

    exporter.save(path, [])

    assert path.read_text(encoding="utf-8") == ""


def test_save_overwrites(tmp_path: Path, product: Product):
    path = tmp_path / "out.json"
    path.write_text("old")

    exporter.save(path, [product])

    assert path.read_text(encoding="utf-8") != "old"
