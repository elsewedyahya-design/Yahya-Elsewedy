"""Splice the master's branded cover + back page into FULL_OFFER (unpacked_final).

Imports every cross-part dependency (images, theme, header/footer parts, styles,
rels, content-types, manifest) and remaps rIds to avoid collisions. Operates on
unpacked_final/ in place; pack.py then zips it to FULL_OFFER.final.docx.
"""
import json
import re
import shutil
from pathlib import Path

M_DIR = Path("unpacked")          # master (original)
F_DIR = Path("unpacked_final")    # working copy of FULL_OFFER (cert-integrated)

TOKENS = {
    "{{PROJECT_NAME}}": "CEER Automotive",
    "{{CLIENT_NAME}}": "XXXXXXX",
    "{{DATE}}": "22-10-2025",
    "{{REFERENCE}}": "240146SP-SAU-R2",
    "{{REVISION}}": "R2",
}

# --- new media (master name kept; no collision with FO hash-named files) ---
MEDIA = ["image1.jpeg", "image2.png", "image7.jpeg", "image8.jpeg"]

# --- header/footer parts: master file -> new FO file (renamed to avoid clobber) ---
HF = {
    "header1.xml": "header9.xml",
    "header2.xml": "header10.xml",
    "header3.xml": "header11.xml",
    "footer1.xml": "footer9.xml",
    "footer2.xml": "footer10.xml",
    "footer3.xml": "footer11.xml",
}

# --- rId remap (master rId -> new FO rId) ---
COVER_MAP = {"rId11": "rId101", "rId12": "rId102"}
BACK_MAP = {
    "rId12": "rId102", "rId21": "rId103",
    "rId17": "rId111", "rId18": "rId112", "rId19": "rId113", "rId20": "rId114",
    "rId22": "rId104", "rId23": "rId105", "rId24": "rId106",
    "rId25": "rId107", "rId26": "rId108", "rId27": "rId109",
}
SECT_MAP = {"rId22": "rId104", "rId23": "rId105", "rId24": "rId106",
            "rId25": "rId107", "rId26": "rId108", "rId27": "rId109"}

NEW_RELS = [
    ('rId101', 'image', 'media/image1.jpeg', None),
    ('rId102', 'image', 'media/image2.png', None),
    ('rId103', 'image', 'media/image7.jpeg', None),
    ('rId104', 'header', 'header9.xml', None),
    ('rId105', 'header', 'header10.xml', None),
    ('rId106', 'footer', 'footer9.xml', None),
    ('rId107', 'footer', 'footer10.xml', None),
    ('rId108', 'header', 'header11.xml', None),
    ('rId109', 'footer', 'footer11.xml', None),
    ('rId111', 'hyperlink', 'mailto:info-transformers@elsewedy.com', 'External'),
    ('rId112', 'hyperlink', 'http://www.elsewedyelectric.com', 'External'),
    ('rId113', 'hyperlink', 'mailto:info-transformers@elsewedy.com', 'External'),
    ('rId114', 'hyperlink', 'http://www.elsewedyelectric.com', 'External'),
    ('rId115', 'theme', 'theme/theme1.xml', None),
]
REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"


def remap(xml, mapping):
    for old, new in mapping.items():
        xml = xml.replace(f'="{old}"', f'="{new}"')
    return xml


def extract_style(styles_xml, sid):
    m = re.search(r'<w:style [^>]*w:styleId="' + re.escape(sid) + '"', styles_xml)
    if not m:
        return None
    s = styles_xml.rfind('<w:style ', 0, m.end())
    e = styles_xml.index('</w:style>', m.start()) + len('</w:style>')
    return styles_xml[s:e]


def main():
    M = (M_DIR / "word" / "document.xml").read_text(encoding="utf-8")
    cover = Path("._cover.xml").read_text(encoding="utf-8")
    back = Path("._back.xml").read_text(encoding="utf-8")

    # master final sectPr (props for cover + back sections)
    fsp = M.rindex("<w:sectPr")
    master_sect = M[fsp:M.index("</w:sectPr>", fsp) + len("</w:sectPr>")]

    # ---- build cover block ----
    # strip any dataBinding (defensive) + the trailing page break that ends the cover
    cover = re.sub(r'<w:dataBinding[^>]*/>', '', cover)
    pb = '<w:br w:type="page"/>'
    idx = cover.rfind(pb)   # remove the single cover-ending page break
    if idx != -1:
        cover = cover[:idx] + cover[idx + len(pb):]
    cover = remap(cover, COVER_MAP)
    for tok, val in TOKENS.items():
        cover = cover.replace(tok, val)

    # cover section break (master geometry), paragraph-level
    cover_sectpr = remap(master_sect, SECT_MAP)
    cover_sectpr_para = f"<w:p><w:pPr>{cover_sectpr}</w:pPr></w:p>"
    COVER_NEW = cover + cover_sectpr_para

    # ---- build back block ----
    back = remap(back, BACK_MAP)
    # force the back section onto its own page
    back = back.replace('<w:type w:val="continuous"/>', '<w:type w:val="nextPage"/>')

    # ---- edit FO document.xml ----
    F = (F_DIR / "word" / "document.xml").read_text(encoding="utf-8")
    body = F.index("<w:body>") + len("<w:body>")
    # FO flat cover = body start .. end of the first sectPr paragraph
    sp = F.index("<w:sectPr", body)
    spclose = F.index("</w:sectPr>", sp) + len("</w:sectPr>")
    cover_para_end = F.index("</w:p>", spclose) + len("</w:p>")
    assert F[body:].startswith("<w:p"), F[body:body + 20]
    F = F[:body] + COVER_NEW + F[cover_para_end:]

    # final body-level sectPr -> paragraph-level, then append back block
    final_fo_start = F.rindex("<w:sectPr")
    final_fo = F[final_fo_start:F.index("</w:sectPr>", final_fo_start) + len("</w:sectPr>")]
    final_fo_para = f"<w:p><w:pPr>{final_fo}</w:pPr></w:p>"
    assert F.count(final_fo + "</w:body>") == 1
    F = F.replace(final_fo + "</w:body>", final_fo_para + back + "</w:body>")
    (F_DIR / "word" / "document.xml").write_text(F, encoding="utf-8")

    # ---- copy media ----
    for fn in MEDIA:
        shutil.copy(M_DIR / "word" / "media" / fn, F_DIR / "word" / "media" / fn)

    # ---- copy header/footer parts (renamed) + their rels ----
    for src, dst in HF.items():
        shutil.copy(M_DIR / "word" / src, F_DIR / "word" / dst)
        rels_src = M_DIR / "word" / "_rels" / (src + ".rels")
        if rels_src.is_file():
            (F_DIR / "word" / "_rels" / (dst + ".rels")).write_text(
                rels_src.read_text(encoding="utf-8"), encoding="utf-8")

    # ---- copy theme ----
    (F_DIR / "word" / "theme").mkdir(exist_ok=True)
    shutil.copy(M_DIR / "word" / "theme" / "theme1.xml",
                F_DIR / "word" / "theme" / "theme1.xml")

    # ---- document.xml.rels ----
    rels_path = F_DIR / "word" / "_rels" / "document.xml.rels"
    rels = rels_path.read_text(encoding="utf-8")
    add = ""
    for rid, typ, target, mode in NEW_RELS:
        m = f' TargetMode="{mode}"' if mode else ""
        add += f'<Relationship Id="{rid}" Type="{REL_TYPE}{typ}" Target="{target}"{m}/>'
    rels = rels.replace("</Relationships>", add + "</Relationships>")
    rels_path.write_text(rels, encoding="utf-8")

    # ---- [Content_Types].xml ----
    ct_path = F_DIR / "[Content_Types].xml"
    ct = ct_path.read_text(encoding="utf-8")
    ov = ""
    wpml = "application/vnd.openxmlformats-officedocument.wordprocessingml."
    for dst in HF.values():
        kind = "header+xml" if dst.startswith("header") else "footer+xml"
        ov += f'<Override PartName="/word/{dst}" ContentType="{wpml}{kind}"/>'
    ov += ('<Override PartName="/word/theme/theme1.xml" ContentType='
           '"application/vnd.openxmlformats-officedocument.theme+xml"/>')
    ct = ct.replace("</Types>", ov + "</Types>")
    ct_path.write_text(ct, encoding="utf-8")

    # ---- styles.xml: add NoSpacing, NoSpacingChar, SWDDetails ----
    MS = (M_DIR / "word" / "styles.xml").read_text(encoding="utf-8")
    st_path = F_DIR / "word" / "styles.xml"
    st = st_path.read_text(encoding="utf-8")
    add_styles = ""
    for sid in ("NoSpacing", "NoSpacingChar", "SWDDetails"):
        if f'w:styleId="{sid}"' not in st:
            s = extract_style(MS, sid)
            if s:
                add_styles += s
    st = st.replace("</w:styles>", add_styles + "</w:styles>")
    st_path.write_text(st, encoding="utf-8")

    # ---- manifest ----
    man_path = F_DIR / ".docx_manifest.json"
    man = json.loads(man_path.read_text())
    entries = man["entries"]
    tmpl_xml = next(e for e in entries if e["name"].endswith("styles.xml"))
    tmpl_png = next(e for e in entries if e["name"].endswith(".png") and not e.get("is_dir"))
    tmpl_rel = next(e for e in entries if e["name"].endswith(".rels"))
    tmpl_dir = next(e for e in entries if e.get("is_dir"))

    def mk(tmpl, name):
        e = dict(tmpl)
        e["name"] = name
        return e

    have = {e["name"] for e in entries}
    new_parts = []
    new_parts.append(mk(tmpl_dir, "word/theme/"))
    for fn in MEDIA:
        new_parts.append(mk(tmpl_png, f"word/media/{fn}"))
    for dst in HF.values():
        new_parts.append(mk(tmpl_xml, f"word/{dst}"))
    for dst in HF.values():
        if (F_DIR / "word" / "_rels" / (dst + ".rels")).is_file():
            new_parts.append(mk(tmpl_rel, f"word/_rels/{dst}.rels"))
    new_parts.append(mk(tmpl_xml, "word/theme/theme1.xml"))
    for e in new_parts:
        if e["name"] not in have:
            entries.append(e)
    man["entries"] = entries
    man_path.write_text(json.dumps(man, indent=2))

    print("SPLICE OK")
    print("  cover_new bytes:", len(COVER_NEW))
    print("  back bytes:", len(back))
    print("  tokens replaced:", all(t not in F for t in TOKENS))
    print("  new parts added:", len(new_parts))


if __name__ == "__main__":
    main()
