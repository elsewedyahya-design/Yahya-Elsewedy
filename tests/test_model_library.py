"""Tests for the data model, library persistence, and Note-1 composer."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from busway.models import (  # noqa: E402
    Product, Rating, SpecShape, columns_for, Note1Fields,
)
from busway.library import Library  # noqa: E402
from busway.notes import compose_note1  # noqa: E402


def test_rating_validation_flags_missing_and_extra():
    cols = columns_for(SpecShape.SANDWICH)
    good = Rating(800, {c.key: "x" for c in cols})
    missing = Rating(1000, {c.key: "x" for c in cols[:-1]})  # drop one
    extra = Rating(1250, {**{c.key: "x" for c in cols}, "bogus": "1"})
    p = Product(id="t", name="T", spec_shape=SpecShape.SANDWICH,
                ratings=[good, missing, extra])
    problems = p.validate()
    assert any("missing" in s for s in problems)
    assert any("unexpected" in s for s in problems)
    # The fully-correct rating produces no problem line.
    assert not any("800 A" in s for s in problems)


def test_library_json_round_trip(tmp_path):
    cols = columns_for(SpecShape.SANDWICH)
    p = Product(id="spine", name="SPINE", conductor_material="Aluminium",
                spec_shape=SpecShape.SANDWICH,
                ratings=[Rating(800, {c.key: "1" for c in cols})])
    lib = Library([p], path=tmp_path / "library.json")
    lib.save()
    reloaded = Library.load(tmp_path / "library.json")
    assert len(reloaded.products) == 1
    rp = reloaded.products[0]
    assert rp.id == "spine"
    assert rp.spec_shape == SpecShape.SANDWICH
    assert rp.ratings[0].in_amps == 800
    assert reloaded.validate() == []


def test_variant_ratings_sort_and_label():
    cols = columns_for(SpecShape.SANDWICH)
    v = {c.key: "" for c in cols}
    p = Product(id="pl", name="PowerLink", spec_shape=SpecShape.SANDWICH,
                ratings=[Rating(5000, v, "B"), Rating(5000, v, "A"),
                         Rating(800, v)])
    labels = [r.label() for r in p.sorted_ratings()]
    assert labels == ["800 A", "5000 A (A)", "5000 A (B)"]


def test_compose_note1_matches_blueprint_example():
    p = Product(id="spine", name="SPINE", conductor_material="Aluminium",
                note1_fields=Note1Fields("Spine Type", "Aluminium Housing",
                                         "Class B", "Tin Plated on Joint"))
    assert compose_note1(p) == (
        "Offered Elsewedy Compact Busway System, Spine Type, "
        "Aluminium Conductor, Aluminium Housing, Class B, "
        "Tin Plated on Joint."
    )


def test_compose_note1_skips_empty_fields():
    p = Product(id="x", name="X", conductor_material="Copper",
                note1_fields=Note1Fields(product_type="Track Type"))
    # housing/class/plating empty -> skipped, sentence still clean.
    assert compose_note1(p) == (
        "Offered Elsewedy Compact Busway System, Track Type, Copper Conductor."
    )


def test_seeded_library_loads_and_validates():
    """The committed data/library.json must always be valid."""
    repo = Path(__file__).resolve().parent.parent
    lib = Library.load(repo / "data" / "library.json")
    assert len(lib.products) == 4
    assert lib.validate() == []
    assert {p.id for p in lib.products} == {
        "spine", "powerlink", "powercast", "powertrack"}
