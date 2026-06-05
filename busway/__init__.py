"""Busway Offer Generator.

A local app that generates pixel-perfect, editable Microsoft Word (.docx)
offer documents for Elsewedy Electric busway products, from a structured
product library plus per-quote inputs.

Package layout (built incrementally):
  models.py    - data model: Product, Rating, spec-table templates
  library.py   - JSON-backed product library + standard-text store (CRUD)
  docx_io.py   - byte-preserving unpack/pack wrappers (Phase 1)
  fill.py      - token fill engine incl. the {{PROJECT_NAME}} sdt fix (Phase 1)
  generator.py - assemble body sections from library + inputs (Phase 3)
  boq.py       - Excel BOQ ingestion by header name (Phase 4)
  webapp/      - local Flask web UI: User + Admin (Phases 5-6)
"""

__version__ = "0.1.0"
