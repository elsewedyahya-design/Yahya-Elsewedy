"""Tests for BOQ ingestion (header matching + validation)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from busway.boq import parse_pasted, parse_rows  # noqa: E402


def test_standard_paste_parses():
    text = (
        "Item\tType\tDescription\tQTY\tUnit\tUnit Price\tTotal Price\n"
        "1\tSPINE\t800A busway run\t10\tm\t100\t1000\n"
        "2\tSPINE\t90° elbow\t2\tpc\t250\t500\n"
    )
    res = parse_pasted(text)
    assert res.ok
    items = [r for r in res.rows if not r["is_group_header"]]
    assert len(items) == 2
    assert items[0]["description"] == "800A busway run"
    assert res.warnings == []


def test_header_matched_not_position():
    # reordered + synonym headers still map correctly
    text = (
        "Description\tQuantity\tUOM\tRate\tAmount\tNo\n"
        "800A run\t10\tm\t100\t1000\t1\n"
    )
    res = parse_pasted(text)
    assert res.ok
    assert set(res.columns) >= {"description", "qty", "unit", "unit_price",
                                "total_price", "item"}


def test_missing_required_column_errors():
    text = "Item\tDescription\tQTY\n1\tfoo\t2\n"
    res = parse_pasted(text)
    assert not res.ok
    assert any("missing required" in e for e in res.errors)


def test_group_header_detected():
    text = (
        "Item\tDescription\tQTY\tUnit\tUnit Price\tTotal Price\n"
        "A\tSPINE BUSWAY\t\t\t\t\n"
        "1\t800A run\t10\tm\t100\t1000\n"
    )
    res = parse_pasted(text)
    assert res.ok
    assert res.rows[0]["is_group_header"] is True
    assert res.rows[1]["is_group_header"] is False


def test_bad_total_and_xxx_warn():
    text = (
        "Item\tDescription\tQTY\tUnit\tUnit Price\tTotal Price\n"
        "1\t800A run\t10\tm\t100\t9999\n"          # 10*100 != 9999
        "2\txxx pending\t1\tpc\txxx\txxx\n"        # leftover placeholder
    )
    res = parse_pasted(text)
    assert res.ok
    assert any("!=" in w for w in res.warnings)
    assert any("xxx" in w.lower() for w in res.warnings)


def test_unrecognised_column_warns():
    text = (
        "Item\tDescription\tQTY\tUnit\tUnit Price\tTotal Price\tColour\n"
        "1\trun\t10\tm\t100\t1000\tred\n"
    )
    res = parse_pasted(text)
    assert res.ok
    assert any("unrecognised" in w for w in res.warnings)
