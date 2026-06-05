"""Tests for OOXML builders and the offer generator (no Word required)."""
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import xml.etree.ElementTree as ET  # noqa: E402

from busway import ooxml  # noqa: E402
from busway.generator import (  # noqa: E402
    generate_offer, generate_spec_section, generate_price_table,
    OfferInput, ProductSelection,
)
from busway.library import Library  # noqa: E402
from busway.models import SpecShape, columns_for  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def _wrap(frag: str) -> ET.Element:
    """Parse an OOXML fragment by wrapping it in a namespaced root."""
    ns = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
          'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"')
    return ET.fromstring(f"<root {ns}>{frag}</root>")


def test_ooxml_fragments_are_well_formed():
    _wrap(ooxml.section_title("Technical Specification"))
    _wrap(ooxml.product_head("SPINE"))
    _wrap(ooxml.guarantee_band([("Standard", "IEC 61439"), ("IP", "IP55")]))
    _wrap(ooxml.table(["A", "B"], [["1", "2"], ["3", "4"]], first_col_accent=True))
    _wrap(ooxml.bullet("a cancellation term", anchor="10%"))


def test_spec_section_well_formed_and_lists_ratings():
    lib = Library.load(REPO / "data" / "library.json")
    spine = lib.get("spine")
    ratings = spine.sorted_ratings()[:3]
    frag = generate_spec_section([(spine, ratings)])
    _wrap(frag)  # must parse
    assert "Product Guarantees" in frag
    assert "Selected Ratings" in frag


def test_price_table_grand_total():
    rows = [
        {"item": "1", "description": "Busway run", "qty": "10", "unit": "m",
         "unit_price": "100", "total_price": "1000"},
        {"item": "2", "description": "Elbow", "qty": "2", "unit": "pc",
         "unit_price": "250", "total_price": "500"},
    ]
    frag = generate_price_table(rows)
    _wrap(frag)
    assert "GRAND TOTAL" in frag
    assert "1,500.00" in frag


def test_generate_offer_produces_valid_docx(tmp_path):
    out = tmp_path / "offer.docx"
    inp = OfferInput(
        project_name="TEST TOWER", client_name="Test Client",
        reference="EE-T-1", revision="R0",
        selections=[ProductSelection("spine", "Export",
                                     ratings=[(800, ""), (1600, "")])],
    )
    report = generate_offer(inp, out)
    assert out.is_file()
    assert report["remaining_tokens"] == []
    assert report["fill"]["PROJECT_NAME"] == 3  # 2 doc + 1 core title
    # valid zip, no leftover tokens in document.xml
    with zipfile.ZipFile(out) as zf:
        assert zf.testzip() is None
        doc = zf.read("word/document.xml").decode("utf-8")
        assert "{{" not in doc
        # exactly the generated spec tables remain (cover/contact untouched)
        assert "TEST TOWER" in doc


def test_generate_offer_injects_price_table_and_lme(tmp_path):
    """A pasted BOQ fills the Price Breakdown section; the LME baseline in the
    Conditions of Sale is aligned to this quote's figure."""
    out = tmp_path / "offer.docx"
    boq_rows = [
        {"item": "1", "description": "800A busway run", "qty": "10",
         "unit": "m", "unit_price": "100", "total_price": "1000"},
    ]
    inp = OfferInput(
        project_name="DC ALPHA", reference="EE-T-2",
        lme_baseline="9500",
        selections=[ProductSelection("spine", "Export", ratings=[(800, "")])],
        boq_rows=boq_rows,
    )
    generate_offer(inp, out)
    with zipfile.ZipFile(out) as zf:
        assert zf.testzip() is None
        doc = zf.read("word/document.xml").decode("utf-8")
    # price table landed and totalled
    assert "GRAND TOTAL" in doc
    assert "800A busway run" in doc
    # LME baseline aligned, exemplar figure gone
    assert "9500 USD per Ton" in doc
    assert "9000 USD per Ton" not in doc
