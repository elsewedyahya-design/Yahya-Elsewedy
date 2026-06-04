"""One-time master-template hardening (BLUEPRINT TASK 1).

The cover's project-name lives in two Title plain-text content controls whose
runs already carry the {{PROJECT_NAME}} token. The breakage: each control has a
<w:dataBinding> pointing at the document's core-properties <dc:title>. On open,
Word repopulates the control from that bound value -- which still reads
"PROJECT NAME: KUWAIT DIRECT INVESTMENT PROMOTION AUTHORITY (KDIPA)" -- wiping
the token. A plain text/token swap therefore appears to "not work".

Fix (surgical, pixel-safe):
  1. Delete the <w:dataBinding .../> element from both sdtPr. The controls keep
     their exact styling/runs but no longer refresh from an external source, so
     the literal {{PROJECT_NAME}} token survives for the fill engine.
  2. Tokenize <dc:title> in docProps/core.xml to {{PROJECT_NAME}} so document
     metadata is consistent and fillable (and the stale KDIPA string is gone).

Operates in place on an unpacked tree. Idempotent.

Usage:
    python scripts/office/fix_template.py unpacked/
"""
import re
import sys
from pathlib import Path

DATA_BINDING = (
    '<w:dataBinding w:prefixMappings="xmlns:ns0=\'http://purl.org/dc/elements/1.1/\' '
    'xmlns:ns1=\'http://schemas.openxmlformats.org/package/2006/metadata/core-properties\' " '
    'w:xpath="/ns1:coreProperties[1]/ns0:title[1]" '
    'w:storeItemID="{6C3C8BC8-F283-45AE-878A-BAB7291924A1}"/>'
)


def fix(unpacked: str) -> None:
    root = Path(unpacked)
    doc = root / "word" / "document.xml"
    core = root / "docProps" / "core.xml"

    # 1. strip both dataBindings
    dx = doc.read_text(encoding="utf-8")
    n = dx.count(DATA_BINDING)
    dx = dx.replace(DATA_BINDING, "")
    doc.write_text(dx, encoding="utf-8")
    print(f"document.xml: removed {n} <w:dataBinding> element(s)")

    # 2. tokenize dc:title
    cx = core.read_text(encoding="utf-8")
    new_cx, k = re.subn(
        r"<dc:title>.*?</dc:title>",
        "<dc:title>{{PROJECT_NAME}}</dc:title>",
        cx,
        flags=re.DOTALL,
    )
    core.write_text(new_cx, encoding="utf-8")
    print(f"core.xml: tokenized {k} <dc:title> element(s)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python fix_template.py <unpacked_dir>")
    fix(sys.argv[1])
