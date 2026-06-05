"""Byte-preserving .docx unpack/pack wrappers (blueprint golden rule).

Thin wrappers over the proven scripts/office/unpack.py + pack.py so the rest
of the package imports a clean API. We never parse/reserialise the whole
document -- only targeted string edits on specific parts -- so the cover and
contact pages stay pixel-perfect.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_OFFICE = Path(__file__).resolve().parent.parent / "scripts" / "office"


def _load(mod_name: str):
    spec = importlib.util.spec_from_file_location(mod_name, _OFFICE / f"{mod_name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_unpack_mod = _load("unpack")
_pack_mod = _load("pack")


def unpack(docx_path: str | Path, out_dir: str | Path) -> Path:
    _unpack_mod.unpack(str(docx_path), str(out_dir))
    return Path(out_dir)


def pack(src_dir: str | Path, out_path: str | Path,
         original: str | Path | None = None) -> Path:
    _pack_mod.pack(str(src_dir), str(out_path),
                   str(original) if original else None)
    return Path(out_path)
