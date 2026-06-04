"""Re-zip an unpacked folder back into a .docx and validate it.

Rebuilds the archive using the order/metadata captured by unpack.py so the
only differences from the original are the bytes we deliberately edited.

Validation performed:
  * every part well-formed XML (xml parts only)
  * [Content_Types].xml present
  * resulting zip opens and testzip() passes
  * optional structural diff against --original (which parts changed)

Usage:
    python scripts/office/pack.py unpacked/ out.docx [--original MASTER_TEMPLATE.docx]
"""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def _validate_xml(parts_dir: Path) -> list[str]:
    problems = []
    for p in parts_dir.rglob("*"):
        if p.suffix.lower() not in (".xml", ".rels"):
            continue
        try:
            ET.parse(p)
        except ET.ParseError as e:
            problems.append(f"  malformed XML: {p.relative_to(parts_dir)} -> {e}")
    return problems


def pack(src_dir: str, out_path: str, original: str | None = None) -> None:
    src = Path(src_dir)
    manifest_path = src / ".docx_manifest.json"
    if not manifest_path.is_file():
        sys.exit("error: .docx_manifest.json missing; re-run unpack.py")
    manifest = json.loads(manifest_path.read_text())

    problems = _validate_xml(src)
    if problems:
        print("XML validation FAILED:")
        print("\n".join(problems))
        sys.exit(1)

    if not (src / "[Content_Types].xml").is_file():
        sys.exit("error: [Content_Types].xml missing")

    out = Path(out_path)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for entry in manifest["entries"]:
            name = entry["name"]
            info = zipfile.ZipInfo(name, date_time=tuple(entry["date_time"]))
            info.compress_type = entry["compress_type"]
            info.external_attr = entry["external_attr"]
            info.create_system = entry["create_system"]
            if entry.get("is_dir"):
                zf.writestr(info, b"")
                continue
            fp = src / name
            if not fp.is_file():
                sys.exit(f"error: part listed in manifest is missing: {name}")
            zf.writestr(info, fp.read_bytes())

    with zipfile.ZipFile(out) as zf:
        if zf.testzip() is not None:
            sys.exit("error: produced zip is corrupt")

    print(f"packed -> {out} ({len(manifest['entries'])} parts, validated)")

    if original:
        _diff(Path(original), src, manifest)


def _diff(original: Path, src: Path, manifest: dict) -> None:
    print(f"\nchanged parts vs {original.name}:")
    changed = 0
    with zipfile.ZipFile(original) as zf:
        orig_names = set(zf.namelist())
        for entry in manifest["entries"]:
            if entry.get("is_dir"):
                continue
            name = entry["name"]
            new_bytes = (src / name).read_bytes()
            if name in orig_names:
                old = hashlib.md5(zf.read(name)).hexdigest()
                new = hashlib.md5(new_bytes).hexdigest()
                if old != new:
                    print(f"  M {name}")
                    changed += 1
            else:
                print(f"  + {name}")
                changed += 1
    if not changed:
        print("  (none — byte-identical content)")


if __name__ == "__main__":
    args = sys.argv[1:]
    original = None
    if "--original" in args:
        i = args.index("--original")
        original = args[i + 1]
        del args[i : i + 2]
    if len(args) != 2:
        sys.exit("usage: python pack.py <src_dir> <out.docx> [--original <ref.docx>]")
    pack(args[0], args[1], original)
