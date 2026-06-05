"""OOXML fragment builders for generated sections (brand tokens, blueprint §9).

These emit WordprocessingML `<w:...>` strings that splice into the unpacked
document.xml. They reuse the namespaces already declared on the document root,
so fragments need no xmlns of their own. Design principle: MINIMALISM — clean,
airy, Montserrat, generous spacing, no clutter (blueprint §9).

All output is well-formed XML (validated by pack.py before a .docx is built).
"""
from __future__ import annotations

from xml.sax.saxutils import escape

# --- brand tokens (locked, blueprint §9) -----------------------------------
RED = "C8102E"        # section rules, accents, percentages, page numbers
DARK = "1A1A1A"
NAVY = "1F3864"       # sub-labels
GREY = "6B7280"       # captions
HEADER_BAND = "2E2E2E"  # table header band, white text
ZEBRA = "F4F6F8"      # alternating row fill
HAIRLINE = "D0D5DB"   # table borders
WHITE = "FFFFFF"

FONT = "Montserrat"
CONTENT_WIDTH_DXA = 9360  # ~content width at 1" margins on US Letter


def _sz(pt: float) -> str:
    """Word stores size in half-points."""
    return str(int(round(pt * 2)))


def run(text: str, *, bold=False, italic=False, caps=False, color: str | None = None,
        size_pt: float = 11, font: str = FONT) -> str:
    rpr = ['<w:rFonts w:ascii="%s" w:hAnsi="%s"/>' % (font, font)]
    if bold:
        rpr.append("<w:b/>")
    if italic:
        rpr.append("<w:i/>")
    if caps:
        rpr.append("<w:caps/>")
    if color:
        rpr.append('<w:color w:val="%s"/>' % color)
    rpr.append('<w:sz w:val="%s"/><w:szCs w:val="%s"/>' % (_sz(size_pt), _sz(size_pt)))
    return "<w:r><w:rPr>%s</w:rPr><w:t xml:space=\"preserve\">%s</w:t></w:r>" % (
        "".join(rpr), escape(text))


def para(runs: str | list[str], *, space_before=0, space_after=120,
         bottom_rule: str | None = None, align: str | None = None,
         keep_next=False) -> str:
    if isinstance(runs, list):
        runs = "".join(runs)
    ppr = ['<w:spacing w:before="%d" w:after="%d"/>' % (space_before, space_after)]
    if bottom_rule:
        ppr.append(
            '<w:pBdr><w:bottom w:val="single" w:sz="18" w:space="4" '
            'w:color="%s"/></w:pBdr>' % bottom_rule)
    if align:
        ppr.append('<w:jc w:val="%s"/>' % align)
    if keep_next:
        ppr.append("<w:keepNext/>")
    return "<w:p><w:pPr>%s</w:pPr>%s</w:p>" % ("".join(ppr), runs)


def section_title(text: str) -> str:
    """Bold black ALL-CAPS heading over a red bottom rule (Heading 1)."""
    p = ('<w:p><w:pPr><w:pStyle w:val="Heading1"/>'
         '<w:spacing w:before="240" w:after="120"/>'
         '<w:pBdr><w:bottom w:val="single" w:sz="18" w:space="6" w:color="%s"/>'
         '</w:pBdr></w:pPr>%s</w:p>')
    return p % (RED, run(text.upper(), bold=True, caps=True, color=DARK, size_pt=16))


def sub_label(text: str) -> str:
    """Bold navy sub-heading (Heading 2 so it nests in the TOC)."""
    return ('<w:p><w:pPr><w:pStyle w:val="Heading2"/>'
            '<w:spacing w:before="180" w:after="80"/></w:pPr>%s</w:p>') % run(
        text, bold=True, color=NAVY, size_pt=13)


def product_head(text: str) -> str:
    """Bold red product sub-block head (Heading 2 for TOC nesting)."""
    return ('<w:p><w:pPr><w:pStyle w:val="Heading2"/>'
            '<w:spacing w:before="180" w:after="80"/></w:pPr>%s</w:p>') % run(
        text, bold=True, color=RED, size_pt=13)


def body_para(text: str, *, color=DARK, size_pt=11, space_after=120) -> str:
    return para(run(text, color=color, size_pt=size_pt), space_after=space_after)


def bullet(text: str, *, color=DARK, indent=360, anchor: str | None = None) -> str:
    """A clean dash bullet. `anchor` (e.g. a bold-red %) leads the line."""
    runs = []
    if anchor:
        runs.append(run(anchor + "  ", bold=True, color=RED))
    runs.append(run(text, color=color))
    ppr = ('<w:spacing w:before="20" w:after="40"/>'
           '<w:ind w:left="%d" w:hanging="180"/>' % indent)
    dash = run("–  ", color=color)
    return "<w:p><w:pPr>%s</w:pPr>%s%s</w:p>" % (ppr, dash, "".join(runs))


# --- tables -----------------------------------------------------------------
def _cell(content: str, *, width: int, fill: str | None = None) -> str:
    tcpr = ['<w:tcW w:w="%d" w:type="dxa"/>' % width]
    if fill:
        tcpr.append('<w:shd w:val="clear" w:color="auto" w:fill="%s"/>' % fill)
    tcpr.append('<w:vAlign w:val="center"/>')
    return "<w:tc><w:tcPr>%s</w:tcPr>%s</w:tc>" % ("".join(tcpr), content)


def table(headers: list[str], rows: list[list[str]], *,
          col_widths: list[int] | None = None,
          first_col_accent=False) -> str:
    """A clean branded table: dark header band + white text, zebra body rows,
    hairline borders. `first_col_accent` renders the leading cell bold red
    (the rated-current anchor in the two-zone spec table)."""
    ncols = len(headers)
    if col_widths is None:
        w = CONTENT_WIDTH_DXA // ncols
        col_widths = [w] * ncols
        col_widths[-1] = CONTENT_WIDTH_DXA - w * (ncols - 1)

    borders = (
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:color="%s"/>'
        '<w:left w:val="none" w:sz="0" w:color="auto"/>'
        '<w:bottom w:val="single" w:sz="4" w:color="%s"/>'
        '<w:right w:val="none" w:sz="0" w:color="auto"/>'
        '<w:insideH w:val="single" w:sz="4" w:color="%s"/>'
        '<w:insideV w:val="none" w:sz="0" w:color="auto"/>'
        '</w:tblBorders>' % (HAIRLINE, HAIRLINE, HAIRLINE))
    grid = "".join('<w:gridCol w:w="%d"/>' % c for c in col_widths)
    tblpr = ('<w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
             '%s<w:tblCellMar><w:top w:w="60" w:type="dxa"/>'
             '<w:left w:w="100" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/>'
             '<w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr>' % (
                 CONTENT_WIDTH_DXA, borders))

    # header row
    hcells = [
        _cell(para(run(h, bold=True, color=WHITE, size_pt=10), space_after=0,
                   align="center" if i else "left"),
              width=col_widths[i], fill=HEADER_BAND)
        for i, h in enumerate(headers)]
    head_row = ('<w:tr><w:trPr><w:tblHeader/></w:trPr>%s</w:tr>'
                % "".join(hcells))

    body_rows = []
    for ri, row in enumerate(rows):
        fill = ZEBRA if ri % 2 else None
        cells = []
        for ci, val in enumerate(row):
            if ci == 0 and first_col_accent:
                content = para(run(val, bold=True, color=RED, size_pt=11),
                               space_after=0)
            else:
                content = para(run(val, color=DARK, size_pt=10),
                               space_after=0, align="center" if ci else "left")
            cells.append(_cell(content, width=col_widths[ci], fill=fill))
        body_rows.append("<w:tr>%s</w:tr>" % "".join(cells))

    return ("<w:tbl><w:tblGrid>%s</w:tblGrid>%s%s%s</w:tbl>"
            % (grid, tblpr, head_row, "".join(body_rows)))


def placeholder_box(text: str) -> str:
    """A dashed-border, grey, centred placeholder box (blueprint §Phase 7).

    Used where a product diagram or certificate image will go but none has
    been uploaded yet — so the layout clearly shows the slot rather than
    silently collapsing.
    """
    borders = (
        '<w:tblBorders>'
        '<w:top w:val="dashed" w:sz="6" w:space="0" w:color="%s"/>'
        '<w:left w:val="dashed" w:sz="6" w:space="0" w:color="%s"/>'
        '<w:bottom w:val="dashed" w:sz="6" w:space="0" w:color="%s"/>'
        '<w:right w:val="dashed" w:sz="6" w:space="0" w:color="%s"/>'
        '</w:tblBorders>' % (HAIRLINE, HAIRLINE, HAIRLINE, HAIRLINE))
    tblpr = ('<w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
             '%s<w:tblCellMar><w:top w:w="240" w:type="dxa"/>'
             '<w:left w:w="100" w:type="dxa"/><w:bottom w:w="240" w:type="dxa"/>'
             '<w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr>'
             % (CONTENT_WIDTH_DXA, borders))
    grid = '<w:gridCol w:w="%d"/>' % CONTENT_WIDTH_DXA
    content = para(run(text, italic=True, color=GREY, size_pt=10),
                   space_after=0, align="center")
    cell = _cell(content, width=CONTENT_WIDTH_DXA)
    return ("<w:tbl><w:tblGrid>%s</w:tblGrid>%s<w:tr>%s</w:tr></w:tbl>"
            % (grid, tblpr, cell))


def guarantee_band(items: list[tuple[str, str]]) -> str:
    """Zone-1 Product Guarantees: family-wide constants as red mini-labels +
    values, laid out as a clean 3-column borderless grid (airy, minimal)."""
    cols = 3
    cell_w = CONTENT_WIDTH_DXA // cols
    grid = "".join('<w:gridCol w:w="%d"/>' % cell_w for _ in range(cols))
    tblpr = ('<w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
             '<w:tblCellMar><w:top w:w="40" w:type="dxa"/>'
             '<w:left w:w="80" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/>'
             '<w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr>'
             % CONTENT_WIDTH_DXA)
    rows = []
    for i in range(0, len(items), cols):
        chunk = items[i:i + cols]
        cells = []
        for label, value in chunk:
            content = (para(run(label.upper(), bold=True, color=RED, size_pt=8),
                            space_after=0)
                       + para(run(value, color=DARK, size_pt=10), space_after=0))
            cells.append(_cell(content, width=cell_w))
        while len(cells) < cols:
            cells.append(_cell(para("", space_after=0), width=cell_w))
        rows.append("<w:tr>%s</w:tr>" % "".join(cells))
    return "<w:tbl><w:tblGrid>%s</w:tblGrid>%s%s</w:tbl>" % (grid, tblpr, "".join(rows))
