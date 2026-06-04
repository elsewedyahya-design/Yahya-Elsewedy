"""Replace FULL_OFFER's 4 placeholder cert cards with the 4 real cards split
from the master's image6.png.

- copies cert1..cert4.png into word/media/
- adds 4 image relationships (rId13..rId16) to document.xml.rels
- repoints the 4 sequential rId11 blip embeds to rId13..rId16
- registers the new media parts in .docx_manifest.json
- removes the now-orphaned placeholder (rId11 rel + its media file + manifest)
"""
import json
import re
import shutil
import sys
from pathlib import Path

UNPACKED = Path("unpacked_fulloffer")
CERTS = Path("._certs")
PLACEHOLDER = "2e497a00a52109715824c4e35121f1df89b3516b.png"
NEW = [(f"rId{13+i}", f"cert{i+1}.png") for i in range(4)]


def main() -> None:
    media = UNPACKED / "word" / "media"
    for _, fn in NEW:
        shutil.copy(CERTS / fn, media / fn)

    # rels: drop placeholder rId11, add the 4 new image rels
    rels_path = UNPACKED / "word" / "_rels" / "document.xml.rels"
    rels = rels_path.read_text(encoding="utf-8")
    rels = re.sub(r'<Relationship Id="rId11"[^>]*/>', "", rels)
    add = "".join(
        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/'
        f'officeDocument/2006/relationships/image" Target="media/{fn}"/>'
        for rid, fn in NEW
    )
    rels = rels.replace("</Relationships>", add + "</Relationships>")
    rels_path.write_text(rels, encoding="utf-8")

    # document.xml: repoint the 4 sequential rId11 embeds
    doc_path = UNPACKED / "word" / "document.xml"
    doc = doc_path.read_text(encoding="utf-8")
    if doc.count('r:embed="rId11"') != 4:
        sys.exit(f"expected 4 rId11 embeds, found {doc.count('r:embed=\"rId11\"')}")
    counter = {"i": 0}

    def repl(_m):
        rid = NEW[counter["i"]][0]
        counter["i"] += 1
        return f'r:embed="{rid}"'

    doc = re.sub(r'r:embed="rId11"', repl, doc)
    doc_path.write_text(doc, encoding="utf-8")

    # manifest: add 4 new media parts (mirror an existing media entry's attrs),
    # remove the placeholder entry
    man_path = UNPACKED / ".docx_manifest.json"
    man = json.loads(man_path.read_text())
    template = next(
        e for e in man["entries"] if e["name"].endswith(".png") and not e.get("is_dir")
    )
    entries = [e for e in man["entries"] if not e["name"].endswith(PLACEHOLDER)]
    for _, fn in NEW:
        e = dict(template)
        e["name"] = f"word/media/{fn}"
        entries.append(e)
    man["entries"] = entries
    man_path.write_text(json.dumps(man, indent=2))

    # delete orphaned placeholder file
    (media / PLACEHOLDER).unlink(missing_ok=True)
    print(f"integrated 4 real cert cards; removed placeholder {PLACEHOLDER}")


if __name__ == "__main__":
    main()
