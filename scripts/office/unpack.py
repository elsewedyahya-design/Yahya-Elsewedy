"""Unpack a .docx (zip of XML) into a folder, preserving raw bytes.

Pixel-fidelity rule: we do NOT parse/reserialize anything here. Every part is
extracted byte-for-byte so the only changes to the document are the targeted
edits made later. A manifest records the original zip entry order and metadata
so pack.py can rebuild an identical archive.

Usage:
    python scripts/office/unpack.py MASTER_TEMPLATE.docx unpacked/
"""
import json
import sys
import zipfile
from pathlib import Path


def unpack(docx_path: str, out_dir: str) -> None:
    src = Path(docx_path)
    dst = Path(out_dir)
    if not src.is_file():
        sys.exit(f"error: {src} not found")
    dst.mkdir(parents=True, exist_ok=True)

    manifest = []
    with zipfile.ZipFile(src) as zf:
        if zf.testzip() is not None:
            sys.exit("error: source zip is corrupt")
        for info in zf.infolist():
            is_dir = info.is_dir()
            if not is_dir:
                data = zf.read(info.filename)
                target = dst / info.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            manifest.append(
                {
                    "name": info.filename,
                    "is_dir": is_dir,
                    "compress_type": info.compress_type,
                    "date_time": list(info.date_time),
                    "external_attr": info.external_attr,
                    "create_system": info.create_system,
                }
            )

    (dst / ".docx_manifest.json").write_text(
        json.dumps({"source": src.name, "entries": manifest}, indent=2)
    )
    print(f"unpacked {len(manifest)} parts -> {dst}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python unpack.py <in.docx> <out_dir>")
    unpack(sys.argv[1], sys.argv[2])
