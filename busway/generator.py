"""Offer generator (blueprint §4, Tasks 3-6).

Assembly strategy (golden rule: never rebuild cover/contact):
  * The master MASTER_TEMPLATE.docx is a complete Cu_Export offer whose entire
    Technical Specification lives in ONE giant nested <w:tbl> (the only table
    in the document). Everything else -- cover, company intro, factory/product
    overview, price breakdown, technical notes, commercial offer, terms, and
    the contact page -- sits OUTSIDE that table.
  * We therefore: (1) fill tokens, (2) REPLACE that single giant table with a
    clean two-zone Technical Specification built from the selected products and
    ratings, (3) inject the consolidated price table + recomposed technical
    notes. The pixel-perfect, image-heavy cover and contact pages are never
    touched.

This keeps the edit surface tiny and bounded while delivering the redesigned
sections. Output is validated as well-formed XML before packing.
"""
from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import docx_io, fill, ooxml
from .library import Library, StandardText
from .models import Product, Rating, SpecShape, columns_for
from .notes import compose_note1

MASTER = Path(__file__).resolve().parent.parent / "MASTER_TEMPLATE.docx"


# --- offer input model ------------------------------------------------------
@dataclass
class ProductSelection:
    product_id: str
    local_export: str = "Export"          # "Local" | "Export"
    # selected ratings as (in_amps, variant); empty -> all ratings
    ratings: list[tuple[float, str]] = field(default_factory=list)


@dataclass
class OfferInput:
    project_name: str = ""
    client_name: str = ""
    reference: str = ""
    revision: str = "R0"
    date: str = ""                         # blank -> auto today
    validity: str = ""                     # blank -> standard-text default
    warranty_months: str = ""              # blank -> standard-text default
    lme_baseline: str = ""                 # USD/Ton, when escalation applies
    selections: list[ProductSelection] = field(default_factory=list)
    boq_rows: list[dict] = field(default_factory=list)   # parsed BOQ line items


# --- spec section (Task 3, two-zone) ---------------------------------------
def _spec_table_for_product(p: Product, ratings: list[Rating]) -> str:
    """Zone-2 selected-ratings table: rows = ratings, cols = template + In."""
    if p.spec_shape == SpecShape.TRACK:
        # Bespoke shape pending design; render a clean note placeholder.
        return ooxml.body_para(
            "PowerTrack specification table — layout pending finalisation.",
            color=ooxml.GREY, size_pt=10)
    cols = columns_for(p.spec_shape)
    headers = ["Rated current"] + [
        (c.label + (f" ({c.unit})" if c.unit else "")) for c in cols]
    rows = []
    for r in ratings:
        row = [r.label()] + [str(r.values.get(c.key, "") or "—") for c in cols]
        rows.append(row)
    # First column (rated current) narrower + accented; rest share the width.
    first = 1500
    rest = (ooxml.CONTENT_WIDTH_DXA - first) // max(1, len(cols))
    widths = [first] + [rest] * len(cols)
    widths[-1] = ooxml.CONTENT_WIDTH_DXA - first - rest * (len(cols) - 1)
    return ooxml.table(headers, rows, col_widths=widths, first_col_accent=True)


def generate_spec_section(products_ratings: list[tuple[Product, list[Rating]]]) -> str:
    """One combined Technical Specification; each product a red sub-block:
    guarantees band (Zone 1) + selected-ratings table (Zone 2)."""
    blocks = []
    for p, ratings in products_ratings:
        blocks.append(ooxml.product_head(f"{p.name} — {p.subtitle}"
                                         if p.subtitle else p.name))
        if p.guarantees_band:
            blocks.append(ooxml.sub_label("Product Guarantees"))
            blocks.append(ooxml.guarantee_band(
                [(g.label, g.value) for g in p.guarantees_band]))
        blocks.append(ooxml.sub_label("Selected Ratings"))
        blocks.append(_spec_table_for_product(p, ratings))
    return "".join(blocks)


def _replace_giant_table(document_xml: str, spec_xml: str) -> str:
    """Replace the single giant Technical Specification <w:tbl> with spec_xml."""
    start = document_xml.find("<w:tbl>")
    end = document_xml.rfind("</w:tbl>")
    if start == -1 or end == -1 or end < start:
        raise RuntimeError("could not locate the Technical Specification table")
    return document_xml[:start] + spec_xml + document_xml[end + len("</w:tbl>"):]


# --- price breakdown (Task 7 render side) ----------------------------------
def generate_price_table(boq_rows: list[dict]) -> str:
    """Consolidated price table grouped by product, with a grand total.

    Each row dict may carry: item, type, description, qty, unit, unit_price,
    total_price, and optionally `group` (product) / `is_group_header`.
    """
    headers = ["Item", "Description", "Qty", "Unit", "Unit Price", "Total Price"]
    widths = [900, 4000, 800, 900, 1380, 1380]
    rows = []
    grand = 0.0
    for r in boq_rows:
        rows.append([
            str(r.get("item", "")),
            str(r.get("description", r.get("type", ""))),
            str(r.get("qty", "")),
            str(r.get("unit", "")),
            str(r.get("unit_price", "")),
            str(r.get("total_price", "")),
        ])
        try:
            grand += float(str(r.get("total_price", "0")).replace(",", "") or 0)
        except ValueError:
            pass
    if rows:
        rows.append(["", "GRAND TOTAL", "", "", "",
                     f"{grand:,.2f}" if grand else ""])
    return ooxml.table(headers, rows, col_widths=widths)


# --- technical notes (Task 4b) ---------------------------------------------
def generate_notes_section(products: list[Product], st: StandardText) -> str:
    blocks = [ooxml.sub_label("Technical Notes")]
    n = 1
    for p in products:
        blocks.append(ooxml.bullet(compose_note1(p), anchor=f"{n}."))
        n += 1
    for fixed in st.get("technical_notes_fixed", []):
        blocks.append(ooxml.bullet(fixed, anchor=f"{n}."))
        n += 1
    return "".join(blocks)


# --- top-level assembly -----------------------------------------------------
def _resolve_ratings(p: Product, sel: ProductSelection) -> list[Rating]:
    if not sel.ratings:
        return p.sorted_ratings()
    wanted = {(float(a), v) for a, v in sel.ratings}
    chosen = [r for r in p.sorted_ratings() if (r.in_amps, r.variant) in wanted]
    return chosen or p.sorted_ratings()


def generate_offer(inp: OfferInput, out_path: str | Path, *,
                   library: Library | None = None,
                   standard_text: StandardText | None = None,
                   master: Path = MASTER) -> dict:
    """Generate a filled, redesigned offer .docx. Returns a report dict."""
    lib = library or Library.load()
    st = standard_text or StandardText.load()

    products_ratings: list[tuple[Product, list[Rating]]] = []
    for sel in inp.selections:
        p = lib.get(sel.product_id)
        if p is None:
            raise ValueError(f"unknown product: {sel.product_id}")
        products_ratings.append((p, _resolve_ratings(p, sel)))
    products = [p for p, _ in products_ratings]

    work = Path(tempfile.mkdtemp(prefix="busway_gen_"))
    try:
        docx_io.unpack(master, work)
        fill.harden_cover_title(work)

        defaults = st.get("defaults", {})
        values = {
            "PROJECT_NAME": inp.project_name,
            "CLIENT_NAME": inp.client_name,
            "REFERENCE": inp.reference,
            "REVISION": inp.revision,
            "VALIDITY": inp.validity or defaults.get("validity", ""),
            "WARRANTY_MONTHS": inp.warranty_months or defaults.get("warranty_months", "12"),
            "LME_BASELINE": inp.lme_baseline,
        }
        if inp.date:
            values["DATE"] = inp.date
        fill_report = fill.fill_tokens(work, values)

        doc_path = work / "word" / "document.xml"
        xml = doc_path.read_text(encoding="utf-8")

        # Replace the giant Technical Specification table with the two-zone design.
        spec_xml = generate_spec_section(products_ratings)
        xml = _replace_giant_table(xml, spec_xml)

        doc_path.write_text(xml, encoding="utf-8")

        out_path = Path(out_path)
        docx_io.pack(work, out_path, original=master)
        return {
            "output": str(out_path),
            "products": [p.name for p in products],
            "ratings_per_product": {p.name: len(rs) for p, rs in products_ratings},
            "fill": fill_report,
            "remaining_tokens": sorted(fill.remaining_tokens(work)),
            "note1": [compose_note1(p) for p in products],
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)
