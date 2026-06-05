"""JSON-backed product library + standard-text store (blueprint §6).

Single source of truth both roles point at. Plain JSON on disk so it is
human-inspectable, version-controllable, and outlives any one person. The
Admin screen is just a friendly editor over these files.
"""
from __future__ import annotations

import json
from pathlib import Path

from .models import Product

# Repo-root/data by default.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LIBRARY_PATH = DATA_DIR / "library.json"
STANDARD_TEXT_PATH = DATA_DIR / "standard_text.json"


class Library:
    """In-memory product set with load/save and CRUD helpers."""

    def __init__(self, products: list[Product] | None = None,
                 path: Path = LIBRARY_PATH):
        self.path = Path(path)
        self.products: list[Product] = products or []

    # -- persistence ----------------------------------------------------
    @classmethod
    def load(cls, path: Path = LIBRARY_PATH) -> "Library":
        path = Path(path)
        if not path.is_file():
            return cls([], path)
        raw = json.loads(path.read_text(encoding="utf-8"))
        products = [Product.from_dict(p) for p in raw.get("products", [])]
        return cls(products, path)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"products": [p.to_dict() for p in self.products]}
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # -- queries --------------------------------------------------------
    def get(self, product_id: str) -> Product | None:
        return next((p for p in self.products if p.id == product_id), None)

    def active(self) -> list[Product]:
        """Products selectable in the generator (not retired)."""
        return [p for p in self.products if not p.retired]

    # -- mutations (Admin) ----------------------------------------------
    def upsert(self, product: Product) -> None:
        for i, p in enumerate(self.products):
            if p.id == product.id:
                self.products[i] = product
                return
        self.products.append(product)

    def retire(self, product_id: str) -> bool:
        p = self.get(product_id)
        if p:
            p.retired = True
            return True
        return False

    # -- validation -----------------------------------------------------
    def validate(self) -> list[str]:
        problems: list[str] = []
        seen: set[str] = set()
        for p in self.products:
            if p.id in seen:
                problems.append(f"duplicate product id: {p.id}")
            seen.add(p.id)
            problems.extend(p.validate())
        return problems


class StandardText:
    """Editable default-filled fields and fixed boilerplate (blueprint §6.3).

    Keeps "mostly the same, occasionally changes" values out of code:
    validity/warranty defaults, the fixed Technical Notes 2-8, and terms
    boilerplate.
    """

    def __init__(self, data: dict, path: Path = STANDARD_TEXT_PATH):
        self.path = Path(path)
        self.data = data

    @classmethod
    def load(cls, path: Path = STANDARD_TEXT_PATH) -> "StandardText":
        path = Path(path)
        if not path.is_file():
            return cls({}, path)
        return cls(json.loads(path.read_text(encoding="utf-8")), path)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def get(self, key: str, default=None):
        return self.data.get(key, default)
