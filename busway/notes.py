"""Technical Notes composition (blueprint §4.2 / Task 4b).

Note 1 is VARIABLE — auto-composed from a product's selections. Notes 2-8
are fixed boilerplate stored in standard_text.json and returned verbatim.
"""
from __future__ import annotations

from .models import Product

NOTE1_PREFIX = "Offered Elsewedy Compact Busway System"


def compose_note1(product: Product) -> str:
    """Auto-compose Technical Note 1 for a single product.

    e.g. "Offered Elsewedy Compact Busway System, Spine Type, Aluminium
    Conductor, Aluminium Housing, Class B, Tin Plated on Joint."

    Empty fields are skipped so the sentence stays clean for products whose
    library record is not yet fully filled.
    """
    n = product.note1_fields
    parts: list[str] = [NOTE1_PREFIX]
    if n.product_type:
        parts.append(n.product_type)
    if product.conductor_material:
        parts.append(f"{product.conductor_material} Conductor")
    if n.housing:
        parts.append(n.housing)
    if n.rating_class:
        parts.append(n.rating_class)
    if n.plating:
        parts.append(n.plating)
    return ", ".join(parts) + "."


def compose_note1_multi(products: list[Product]) -> str:
    """For a multi-product offer, one Note-1 sentence per product, joined."""
    return " ".join(compose_note1(p) for p in products)
