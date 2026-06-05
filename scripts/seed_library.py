"""Seed data/library.json and data/standard_text.json from BLUEPRINT §2.

Run:  python scripts/seed_library.py

Populates the four products with their identity, conductor, spec-table
shape, family-wide guarantee bands, Technical-Note-1 fields, and the full
list of rated currents. The per-rating electrical VALUES (Icw, Ipk, R,
voltage drop, W/H/Weight) are scaffolded with empty strings: the column
KEYS are present (so validation passes) but the numbers must still be
entered via the Admin screen or extracted from the source spec tables
(FULL_OFFER_final.docx + PowerCast/PowerTrack tech-table docs).

  TODO(data): fill real electrical values per rating.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from busway.models import (  # noqa: E402
    Product, Rating, GuaranteeItem, Note1Fields, SpecShape, columns_for,
)
from busway.library import Library, StandardText  # noqa: E402


def blank_rating(shape: SpecShape, in_amps: float, variant: str = "") -> Rating:
    values = {c.key: "" for c in columns_for(shape)}
    return Rating(in_amps=in_amps, values=values, variant=variant)


def g(label: str, value: str) -> GuaranteeItem:
    return GuaranteeItem(label=label, value=value)


def build_products() -> list[Product]:
    products: list[Product] = []

    # 2.1 SPINE — Aluminium Bi-Metal Conductor — Sandwich
    spine = Product(
        id="spine",
        name="SPINE",
        subtitle="Aluminium Bi-Metal Conductor — Sandwich Busway",
        conductor_material="Aluminium",
        summary_paragraph="",
        spec_shape=SpecShape.SANDWICH,
        guarantees_band=[
            g("Standard", "IEC 61439-1 & 6"),
            g("Protection", "IP55 / IP65"),
            g("Frequency", "50 / 60 Hz"),
            g("Temperature", "-5 / +55 °C"),
            g("Rated insulation voltage (Ui)", "1000 V"),
            g("Rated operational voltage (Ue)", "1000 V"),
            g("Impact protection", "IK10"),
            g("Plating", "Tin / Silver"),
            g("Insulation", "Epoxy / Mylar"),
        ],
        note1_fields=Note1Fields(
            product_type="Spine Type",
            housing="Aluminium Housing",
            rating_class="Class B",
            plating="Tin Plated on Joint",
        ),
    )
    for a in [800, 1000, 1250, 1600, 2000, 2500, 3200, 4000, 5000, 6300]:
        spine.ratings.append(blank_rating(SpecShape.SANDWICH, a))
    products.append(spine)

    # 2.2 POWERLINK — Pure Copper Conductor — Sandwich
    powerlink = Product(
        id="powerlink",
        name="PowerLink",
        subtitle="Pure Copper Conductor — Sandwich Busway",
        conductor_material="Copper",
        spec_shape=SpecShape.SANDWICH,
        guarantees_band=[
            g("Standard", "IEC 61439-1 & 6"),
            g("Protection", "IP55 / IP65"),
            g("Frequency", "50 / 60 Hz"),
            g("Temperature", "-5 / +55 °C"),
            g("Rated insulation voltage (Ui)", "1000 V"),
            g("Rated operational voltage (Ue)", "1000 V"),
            g("Impact protection", "IK10"),
        ],
        note1_fields=Note1Fields(
            product_type="PowerLink Type",
            housing="Aluminium Housing",
            rating_class="Class B",
            plating="Tin Plated on Joint",
        ),
    )
    for a in [800, 1000, 1250, 1600, 2000, 2500, 3200, 3500, 4000, 6000, 6300]:
        powerlink.ratings.append(blank_rating(SpecShape.SANDWICH, a))
    # Two 5000 A variants (blueprint §2.2).
    powerlink.ratings.append(blank_rating(SpecShape.SANDWICH, 5000, variant="A"))
    powerlink.ratings.append(blank_rating(SpecShape.SANDWICH, 5000, variant="B"))
    products.append(powerlink)

    # 2.3 POWERCAST — Pure Copper (Cast Resin) — Cast
    powercast = Product(
        id="powercast",
        name="PowerCast",
        subtitle="Pure Copper Conductor — Cast Resin Busway",
        conductor_material="Copper",
        spec_shape=SpecShape.CAST,
        guarantees_band=[
            g("Standard", "IEC 439-2"),
            g("Protection", "IP68"),
            g("Frequency", "50 / 60 Hz"),
            g("Temperature", "-50 / +40 °C"),
            g("Rated insulation voltage (Ui)", "690 / 1000 V"),
            g("Rated operational voltage (Ue)", "400 – 690 V"),
            g("Tank colour", "Light grey / yellow"),
            g("Installation", "Horizontal hoisting / vertical installation"),
        ],
        note1_fields=Note1Fields(
            product_type="PowerCast Type",
            housing="Cast Resin Housing",
            rating_class="Class B",
            plating="Tin Plated on Joint",
        ),
    )
    for a in [400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000, 5000, 6300]:
        powercast.ratings.append(blank_rating(SpecShape.CAST, a))
    products.append(powercast)

    # 2.4 POWERTRACK — Pure Copper (Track / Data-Centre) — Track (bespoke)
    powertrack = Product(
        id="powertrack",
        name="PowerTrack",
        subtitle="Pure Copper Conductor — Track Busway (Data Centre)",
        conductor_material="Copper",
        spec_shape=SpecShape.TRACK,
        guarantees_band=[
            g("Standard", "IEC 61439-1 & 6"),
            g("Conductor", "Pure Copper"),
        ],
        note1_fields=Note1Fields(
            product_type="PowerTrack Type",
            housing="Track Housing",
            rating_class="Class A",
            plating="Tin Plated on Joint",
        ),
        # Bespoke shape: dual AC/DC current classes + tap-off sub-table.
        # Structure to be finalised (blueprint §11). Scaffolded here.
        track_data={
            "ac_classes": [],   # e.g. [{"class":"A","in":"250", ...}]
            "dc_classes": [],
            "tap_off": {
                "height": "", "width": "", "length": "",
                "intelligent_module_options": [],
                "output_channels": "", "output_form": "",
                "installation_form": "",
            },
            "note": "PowerTrack table layout pending design (blueprint §11).",
        },
    )
    products.append(powertrack)

    return products


def build_standard_text() -> dict:
    return {
        "defaults": {
            "validity": "5 working days",
            "warranty_months": "12",
        },
        # Fixed Technical Notes 2-8 (Note 1 is auto-composed per offer).
        # Verbatim wording to be confirmed against source files.
        "technical_notes_fixed": [
            "The above Bill of Quantities is based on the documents received at "
            "the time of quotation.",
            "The final Bill of Quantities will be issued according to the "
            "approved shop drawings.",
            "Accessories lengths are calculated based on standard lengths.",
            "Adaptation boxes for transformers/generators are excluded unless "
            "otherwise stated.",
            "All submitted ratings are normal ratings for indoor installation.",
            "The following are excluded: fire barriers, civil works, seismic "
            "supports, spare parts, training, and monitoring systems.",
            "For PowerTrack and PowerCast, joints are provided per 3-metre "
            "standard length.",
        ],
        # TODO(text): paste verbatim boilerplate from source files for the
        # four-way terms variants; placeholders below mark the slots.
        "terms": {
            "warranty": "The equipment is guaranteed for {{WARRANTY_MONTHS}} "
                        "months from date of delivery against manufacturing "
                        "defects.",
            "factory_test": "Routine factory tests are carried out in "
                            "accordance with the relevant IEC standards.",
        },
    }


def main() -> None:
    lib = Library(build_products())
    problems = lib.validate()
    if problems:
        print("VALIDATION PROBLEMS:")
        for p in problems:
            print("  -", p)
        raise SystemExit(1)
    lib.save()
    print(f"wrote {lib.path} ({len(lib.products)} products, "
          f"{sum(len(p.ratings) for p in lib.products)} ratings)")

    st = StandardText(build_standard_text())
    st.save()
    print(f"wrote {st.path}")


if __name__ == "__main__":
    main()
