from dataclasses import dataclass


@dataclass
class Variant:
    id: int
    title: str
    sku: str | None
    barcode: str | None
    available: bool
    quantity: int | None
    price: float
    old_price: float | None


@dataclass
class Product:
    id: int
    title: str
    description: str | None
    url: str
    available: bool
    images: list[str]
    variants: list[Variant]
