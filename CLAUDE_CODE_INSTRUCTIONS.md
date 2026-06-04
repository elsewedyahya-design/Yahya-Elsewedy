# Claude Code — Merge Instructions
## Turning MASTER_TEMPLATE.docx into the pixel-perfect generator

**Read first:** `BLUEPRINT.md` (full system spec + decisions) and open `FULL_OFFER.docx` (visual target for the redesigned sections). This file is the precise, ordered task list for merging the redesigned sections INTO the real master while keeping it pixel-perfect.

**Golden rule:** NEVER rebuild the cover, contact page, or document shell. Only edit *contents* in place. Pixel-fidelity is lost the instant anything is reconstructed from scratch. Work on the unpacked XML, validate after every change, keep the original under version control so any broken section can be reverted.

**Environment note:** the doc is a deeply NESTED layout-table structure (~14,000 lines). The `<w:tbl>` that contains "Bus Way Rating" is ~452,000 chars / 75 rows / 290 cells — it wraps far more than the spec table. Do NOT blanket-replace a `<w:tbl>`. Parse the XML into a tree (e.g. python-docx / lxml), locate nodes by content, and replace the minimal node. Brand font is **Montserrat**; match it in every new run.

---

### TASK 0 — Unpack & baseline
1. `python scripts/office/unpack.py MASTER_TEMPLATE.docx unpacked/`
2. Confirm it validates and renders identically to the original (cover pixel-perfect).
3. Commit as baseline.

### TASK 1 — Fix `{{PROJECT_NAME}}` (HIGHEST PRIORITY, verified-broken)
- The project name is inside a **Title-bound `<w:sdt>` content control**, NOT a plain run. A text/token swap does NOT update it (verified failing twice — it still shows "KUWAIT DIRECT INVESTMENT PROMOTION AUTHORITY (KDIPA)").
- Two occurrences exist (two cover render paths) — BOTH must update.
- Fix: either (a) replace the `<w:sdtContent>` inner text for both sdts and clear any bound data source, or (b) unwrap the sdt into a plain run carrying `{{PROJECT_NAME}}`. Then the fill step replaces it like the other tokens.
- Verify: fill with a test name, render page 1, confirm the cover shows the test name in correct Montserrat styling.

### TASK 2 — Token fill engine
- Tokens already in master: `{{CLIENT_NAME}}`, `{{DATE}}`, `{{REFERENCE}}`, `{{REVISION}}`, `{{VALIDITY}}`, `{{WARRANTY_MONTHS}}`, plus `{{PROJECT_NAME}}` (after Task 1) and `{{LME_BASELINE}}` (add where the escalation baseline appears).
- Build a fill function: input dict -> exact string replace across document.xml (and headers if present). Cover tokens appear x2 — replace ALL.
- `{{DATE}}` auto-fills today as "04 June 2026" style, but is overridable by user input.

### TASK 3 — Technical Specification: replace messy table with two-zone design
- Locate the spec `<w:tbl>` (contains "Bus Way Rating"). Identify its exact node (the inner spec table, not the outer layout wrapper).
- Replace with the **two-zone** layout (see FULL_OFFER.docx p.6 and BLUEPRINT §4.3):
  - Zone 1 Product Guarantees band (constants lifted out).
  - Zone 2 Selected Ratings table — ROWS = selected ratings (variable count), columns per the product's template.
- Remove the original problems: stray "Rating" tab, ALL yellow highlight shading, the 14-column squeeze, flat grid, and the "Impedence" -> "Impedance" typo.
- For multi-product offers: repeat as a red sub-block per product inside ONE combined section.
- Match Montserrat + brand tokens (BLUEPRINT §9).

### TASK 4 — Product Overview: per-product blocks + placeholders
- One self-contained block per product: red subtitle, summary, diagram, certifications.
- Diagram/certs come from the Product Library; if absent -> dashed placeholder sized to footprint (BLUEPRINT §7).
- Certs: real composite strip is `image6.png`, split into 4 cards. SPINE/PowerLink have certs; PowerCast/PowerTrack on placeholders until artwork arrives.

### TASK 5 — Table of Contents: nested, field-based, page numbers
- Insert a Word field TOC (`headingStyleRange 1-2`) after the cover. Tag section headings as Heading 1, sub-items as Heading 2 so it auto-builds.
- Nested entries, page numbers on every entry, dot leaders, red title rule (FULL_OFFER.docx p.2 shows the target; note a field TOC only populates when opened in Word — acceptable, or pre-compute on generation).

### TASK 6 — Terms & Conditions: four-way + escalation
- Build the FOUR variants (material x Local/Export) per BLUEPRINT §5.
- Conditions of Sale cleanup: nested "does not include" sub-bullets; cancellation schedule with bold-red % anchors; clean dash bullets elsewhere. **Apply grammar fixes** ("within one month week" -> "within one month", "All submitted rating is normal rating" -> "All submitted ratings are normal ratings", "Impedence" -> "Impedance").
- Escalation formula box (copper-export AND aluminium-export): Latin Modern Roman, italic variables, left-red-bar box. Copper uses Cu1/Cu0; aluminium uses Al1/Al0; coefficient 0.7 both; baseline = `{{LME_BASELINE}}` (typed). Confirm Latin Modern on target machines or EMBED the font.

### TASK 7 — Price Breakdown ingestion
- Parse pasted Excel BOQ by HEADER NAME (Item, Type, Description, QTY, Unit, Unit Price, Total Price), not position.
- One consolidated table, grouped by product, grand total. Flag missing/renamed/extra columns; warn on bad totals or leftover "xxx".

### TASK 8 — Data model + Product Library
- Two tiers: Product (family) -> Ratings (rows). Seed the four products with real data from BLUEPRINT §2 and the source files.
- Three spec-table templates: Sandwich, Cast, Track. (Track = PowerTrack dual AC/DC + tap-off, the one bespoke shape.)

### TASK 9 — Admin screen
- Role-gated. Manage Products / Manage Ratings (the "300 A" path — easiest action) / Manage standard text. Image upload. Validation: flag missing/extra columns, missing images, retiring referenced products.

### TASK 10 — Handover Guide
- Non-technical, screenshots: how to add a product, add a rating, edit standard text, swap in real artwork.

---

### Validation discipline (every task)
- After each edit: `python scripts/office/pack.py unpacked/ out.docx --original MASTER_TEMPLATE.docx` (validates).
- Render to PDF/JPG and eyeball the changed page AND the cover (ensure no collateral damage).
- Commit per passing task so any regression is revertible.

### Open decisions to confirm with user during build
- Spec columns: LEAN (resistance @20° + voltage drop) vs FULL (R35, reactance, full impedance, all PFs).
- PowerTrack Track-table exact layout.
- TOC: field (blank until opened in Word) vs pre-computed page numbers.
