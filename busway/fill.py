"""Token fill engine (blueprint Tasks 1 & 2).

Replaces {{TOKENS}} across an UNPACKED template directory: document.xml, all
header*/footer*.xml, and docProps/core.xml. The last is essential -- the cover
project-name is shown via a Title content control data-bound to core.xml's
<dc:title>, so the bound source must carry the token too or Word repaints the
old value (the "{{PROJECT_NAME}} won't stick" bug).

Order of operations for a fill:
    1. harden_cover_title(dir)   # once: tokenize the bound title source
    2. fill_tokens(dir, values)  # replace every {{TOKEN}} everywhere

We operate on raw part text with plain string replacement. Tokens in the
master are intact (not split across runs); a split-run repair pass is applied
defensively before replacement.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

TOKEN_RE = re.compile(r"\{\{([A-Z_]+)\}\}")

# Parts a token may legitimately appear in.
def _target_parts(unpacked: Path) -> list[Path]:
    word = unpacked / "word"
    parts = [word / "document.xml"]
    parts += sorted(word.glob("header*.xml"))
    parts += sorted(word.glob("footer*.xml"))
    core = unpacked / "docProps" / "core.xml"
    if core.is_file():
        parts.append(core)
    return [p for p in parts if p.is_file()]


def date_today(fmt: str = "%d %B %Y") -> str:
    """Cover date, e.g. '04 June 2026' (spelled month; editable by user)."""
    return _dt.date.today().strftime(fmt)


def default_values() -> dict[str, str]:
    return {"DATE": date_today()}


# --- split-run repair -------------------------------------------------------
# Word sometimes fragments a typed token across runs, e.g.
#   <w:t>{{</w:t>...<w:t>PROJECT_NAME</w:t>...<w:t>}}</w:t>
# Stitch the literal braces back so a plain replace can find the token. This
# only collapses the XML *between* a "{{" <w:t> and the matching "}}" when the
# intervening text (stripped of tags) spells a valid TOKEN -- conservative.
_SPLIT_RE = re.compile(
    r"\{\{((?:(?!\{\{|\}\}).)*?)\}\}", re.S
)


def _repair_split_tokens(xml: str) -> str:
    def _join(m: str) -> str:
        inner = m.group(1)
        text_only = re.sub(r"<[^>]+>", "", inner)  # drop tags between braces
        if re.fullmatch(r"[A-Z_]+", text_only):
            return "{{" + text_only + "}}"
        return m.group(0)
    return _SPLIT_RE.sub(_join, xml)


def harden_cover_title(unpacked: str | Path) -> bool:
    """Tokenize the bound cover-title source in docProps/core.xml.

    Sets <dc:title> to 'PROJECT NAME: {{PROJECT_NAME}}' so the data-bound
    Title content control fills consistently with document.xml. Idempotent.
    Returns True if a change was made.
    """
    core = Path(unpacked) / "docProps" / "core.xml"
    if not core.is_file():
        return False
    xml = core.read_text(encoding="utf-8")
    target = "PROJECT NAME: {{PROJECT_NAME}}"
    new = re.sub(
        r"<dc:title>.*?</dc:title>",
        f"<dc:title>{target}</dc:title>",
        xml,
        count=1,
        flags=re.S,
    )
    if "<dc:title>" not in xml:  # no title element -> nothing bound
        return False
    if new != xml:
        core.write_text(new, encoding="utf-8")
        return new != xml
    return False


def fill_tokens(unpacked: str | Path, values: dict[str, str]) -> dict[str, int]:
    """Replace every {{TOKEN}} across the template parts.

    `values` maps TOKEN name (without braces) -> replacement string. Missing
    DATE is auto-filled with today's date. Returns a {token: count} report of
    replacements actually made (handy for verification / warnings).
    """
    vals = dict(default_values())
    vals.update({k: ("" if v is None else str(v)) for k, v in values.items()})

    report: dict[str, int] = {}
    unpacked = Path(unpacked)
    for part in _target_parts(unpacked):
        xml = part.read_text(encoding="utf-8")
        xml = _repair_split_tokens(xml)
        for token, replacement in vals.items():
            needle = "{{" + token + "}}"
            n = xml.count(needle)
            if n:
                xml = xml.replace(needle, replacement)
                report[token] = report.get(token, 0) + n
        part.write_text(xml, encoding="utf-8")
    return report


def remaining_tokens(unpacked: str | Path) -> set[str]:
    """Tokens still present after a fill (for warnings)."""
    found: set[str] = set()
    for part in _target_parts(Path(unpacked)):
        found.update(TOKEN_RE.findall(part.read_text(encoding="utf-8")))
    return found
