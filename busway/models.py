"""Data model for the Busway Offer Generator (blueprint §3).

Two tiers:
  * Product (the family) -- rarely changes.
  * Rating (per-size rows) -- grows over time; "add a 300 A rating" is the
    most common admin action and must be trivial.

Spec-table *shapes* (Sandwich / Cast / Track) define the ordered column set
every rating in a product must fill. The model VALIDATES that each rating
fills exactly the template's columns (flags missing/extra) rather than
silently misaligning -- per blueprint §3.2.

Values are stored as strings to preserve exact client-facing display
formatting (e.g. "0.70" must not become 0.7). `in_amps` is numeric so
ratings sort naturally.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum


class SpecShape(str, Enum):
    """The three spec-table shapes. New shape = one-time developer task."""
    SANDWICH = "sandwich"   # SPINE, PowerLink
    CAST = "cast"           # PowerCast
    TRACK = "track"         # PowerTrack (bespoke dual AC/DC + tap-off)


@dataclass(frozen=True)
class SpecColumn:
    """One column in a spec-table shape."""
    key: str        # stable id used as the key in Rating.values
    label: str      # client-facing header text
    unit: str = ""  # e.g. "kA", "mm", "mV/m"


# ---------------------------------------------------------------------------
# Spec-table shape column definitions.
#
# OPEN DECISION (blueprint §11): LEAN vs FULL column set. These are the LEAN
# client-facing sets; widening to FULL (R35, reactance, full impedance, all
# PFs) is a pure data-definition change here -- nothing else needs touching.
# ---------------------------------------------------------------------------
SANDWICH_COLUMNS: list[SpecColumn] = [
    SpecColumn("icw", "Short-time withstand (Icw)", "kA"),
    SpecColumn("ipk", "Peak withstand (Ipk)", "kA"),
    SpecColumn("r", "Resistance @20°C", "mΩ/m"),
    SpecColumn("vdrop", "Voltage drop", "mV/m"),
    SpecColumn("w", "Width", "mm"),
    SpecColumn("h", "Height", "mm"),
    SpecColumn("weight", "Weight", "kg/m"),
]

CAST_COLUMNS: list[SpecColumn] = [
    SpecColumn("icw", "Short-time withstand (Icw)", "kA"),
    SpecColumn("ipk", "Peak withstand (Ipk)", "kA"),
    SpecColumn("r", "Resistance @20°C", "mΩ/m"),
    # Cast carries voltage drop at 5 power factors (0.6–1.0); no W/H/Weight.
    SpecColumn("vd_pf06", "Voltage drop @ PF 0.6", "mV/m"),
    SpecColumn("vd_pf07", "Voltage drop @ PF 0.7", "mV/m"),
    SpecColumn("vd_pf08", "Voltage drop @ PF 0.8", "mV/m"),
    SpecColumn("vd_pf09", "Voltage drop @ PF 0.9", "mV/m"),
    SpecColumn("vd_pf10", "Voltage drop @ PF 1.0", "mV/m"),
]

# Track is structurally distinct (dual AC/DC classes + tap-off sub-table).
# It is the one bespoke shape; its detailed columns are defined when the
# PowerTrack layout is finalised (blueprint §11 open item). Until then a
# Track product carries its data in `Product.track_data` (free-form) and is
# not validated against a flat column set.
TRACK_COLUMNS: list[SpecColumn] = []

SPEC_COLUMNS: dict[SpecShape, list[SpecColumn]] = {
    SpecShape.SANDWICH: SANDWICH_COLUMNS,
    SpecShape.CAST: CAST_COLUMNS,
    SpecShape.TRACK: TRACK_COLUMNS,
}


def columns_for(shape: SpecShape) -> list[SpecColumn]:
    return SPEC_COLUMNS[shape]


@dataclass
class Rating:
    """A single rated-current row in a product's spec table.

    `in_amps` is the rated current (the row anchor, bold red on the left in
    the two-zone redesign). `values` maps each non-In column key -> display
    string. `variant` distinguishes same-In rows (e.g. PowerLink's two 5000 A
    variants).
    """
    in_amps: float
    values: dict[str, str] = field(default_factory=dict)
    variant: str = ""           # optional label, e.g. "Cu", "extended"

    def label(self) -> str:
        a = int(self.in_amps) if float(self.in_amps).is_integer() else self.in_amps
        base = f"{a} A"
        return f"{base} ({self.variant})" if self.variant else base


@dataclass
class GuaranteeItem:
    """One labelled constant in the Zone-1 Product Guarantees band."""
    label: str
    value: str


@dataclass
class Note1Fields:
    """Fields used to AUTO-COMPOSE Technical Note 1 (blueprint §4.2, Task 4b).

    e.g. "Offered Elsewedy Compact Busway System, Spine Type, Aluminium
    Conductor, Aluminium Housing, Class B, Tin Plated on Joint."
    """
    product_type: str = ""   # e.g. "Spine Type"
    housing: str = ""        # e.g. "Aluminium Housing"
    rating_class: str = ""   # e.g. "Class B"
    plating: str = ""        # e.g. "Tin Plated on Joint"


@dataclass
class Product:
    """A busway product family (blueprint §3.1)."""
    id: str
    name: str
    subtitle: str = ""
    conductor_material: str = ""          # "Copper" | "Aluminium"
    summary_paragraph: str = ""
    spec_shape: SpecShape = SpecShape.SANDWICH
    guarantees_band: list[GuaranteeItem] = field(default_factory=list)
    note1_fields: Note1Fields = field(default_factory=Note1Fields)
    diagram_image: str = ""               # path; "" -> placeholder
    cert_images: list[str] = field(default_factory=list)
    terms_overrides: dict = field(default_factory=dict)  # e.g. escalation flags
    ratings: list[Rating] = field(default_factory=list)
    track_data: dict = field(default_factory=dict)       # only for TRACK shape
    retired: bool = False

    # -- validation (blueprint §3.2) ------------------------------------
    def validate(self) -> list[str]:
        """Return a list of problems; empty == valid."""
        problems: list[str] = []
        if self.spec_shape == SpecShape.TRACK:
            return problems  # bespoke shape validated separately
        expected = {c.key for c in columns_for(self.spec_shape)}
        for r in self.ratings:
            got = set(r.values)
            missing = expected - got
            extra = got - expected
            if missing:
                problems.append(
                    f"{self.name} / {r.label()}: missing columns {sorted(missing)}"
                )
            if extra:
                problems.append(
                    f"{self.name} / {r.label()}: unexpected columns {sorted(extra)}"
                )
        return problems

    def sorted_ratings(self) -> list[Rating]:
        return sorted(self.ratings, key=lambda r: (r.in_amps, r.variant))

    # -- JSON (de)serialisation -----------------------------------------
    def to_dict(self) -> dict:
        d = asdict(self)
        d["spec_shape"] = self.spec_shape.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Product":
        d = dict(d)
        d["spec_shape"] = SpecShape(d.get("spec_shape", "sandwich"))
        d["guarantees_band"] = [GuaranteeItem(**g) for g in d.get("guarantees_band", [])]
        d["ratings"] = [Rating(**r) for r in d.get("ratings", [])]
        n1 = d.get("note1_fields") or {}
        d["note1_fields"] = Note1Fields(**n1)
        return cls(**d)
