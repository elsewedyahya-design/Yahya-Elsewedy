# Elsewedy Busway — Offer Generator
## Complete System Blueprint & Build Specification

**Purpose:** Replace the hand-maintained Word offer sheets with one tool that generates a polished, pixel-perfect, on-brand, editable Word (.docx) offer from structured inputs. Built so non-technical staff can extend it (new products, new ratings) and so it outlives any single person.

**Target build environment:** Claude Code.
**Output:** Microsoft Word (.docx), editable, sent to clients on multi-million-dollar offers — professionalism and pixel-fidelity are non-negotiable.

---

## 1. System Overview

Two user roles sharing one data store, designed and built together as one project.

| Role | Does what |
|------|-----------|
| **User** (tendering) | Generates offer documents. Cannot change product definitions. |
| **Admin** | Manages the Product Library: add/edit/retire products, add/edit ratings, upload artwork, edit standard text. |

- **Product Library** = single source of truth both roles point at.
- **Master Template** = the real approved .docx whose fixed pages (cover, contact) pass through pixel-perfect.
- **Handover Guide** = non-technical "how to add a product / add a rating / edit text" doc shipped with the tool.

---

## 2. The Product Family (all four products)

The system covers a FAMILY of busway products. Each has its own title, summary, diagram, certs, spec-table shape, guarantees, and terms behaviour. A single offer may contain ONE or SEVERAL products.

### 2.1 SPINE — Aluminium Bi-Metal Conductor
- Sandwich non-ventilated busway. Conductor: Aluminium Bi-Metal.
- Spec-table shape: **Sandwich**.
- Ratings (A): 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000, 5000, 6300.
- Guarantees: IEC 61439-1&6 · IP55/IP65 · 50/60 Hz · -5/+55 C · Ui 1000 V · Ue 1000 V · IK10 · Plating Tin/Silver · Insulation Epoxy/Mylar.

### 2.2 POWERLINK — Pure Copper Conductor
- Sandwich non-ventilated busway. Conductor: Pure Copper.
- Spec-table shape: **Sandwich** (same columns as SPINE, different values; MORE ratings).
- Ratings (A): 800, 1000, 1250, 1600, 2000, 2500, 3200, 3500, 4000, 5000(x2 variants), 6000, 6300.
- Guarantees: IEC 61439-1&6 · IP55/65 · 50/60 Hz · -5/+55 C · Ui 1000 V · Ue 1000 V · IK10.

### 2.3 POWERCAST — Pure Copper (Cast Resin)
- Cast resin busway. Conductor: Pure Copper.
- Spec-table shape: **Cast** (own columns; 5 power factors 0.6–1.0; no W/H/Weight; tank colour + installation form in band).
- Ratings (A): 400, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000, 5000, 6300.
- Guarantees: IEC 439-2 · IP68 · 50/60 Hz · -50/+40 C · Ui 690/1000 V · Ue 400–690 V · Tank colour light grey/yellow · Horizontal hoisting / vertical installation.

### 2.4 POWERTRACK — Pure Copper (Track / Data-Centre)
- Track busway. Conductor: Pure Copper. **Structurally distinct table.**
- Spec-table shape: **Track** — has BOTH:
  - main table with **dual AC and DC current classes** (AC: 250–1000 A class A; DC: 315–1600 A), short-time/peak withstand, dual working/insulation voltages (with vs without tap-off unit), impulse withstand, weight, voltage drops at 5 power factors (1, 0.95, 0.9, 0.85, 0.8);
  - **tap-off-unit sub-table** (tap-off height/width/length, intelligent module options, output channels, output form, installation form).
- This is the ONE shape needing a one-time developer setup; thereafter reusable.

---

## 3. Data Model (two tiers)

### 3.1 Product (the family — rarely changes)
- id; name; subtitle; conductor_material (Copper/Aluminium); summary_paragraph;
- diagram_image (optional -> placeholder); cert_images (list, optional -> placeholder);
- guarantees_band (family-wide constants); spec_table_template (Sandwich/Cast/Track);
- terms_overrides (e.g. copper LME escalation block).

### 3.2 Rating (per-size rows — GROWS over time)
- In (rated current) + one value per column the product's template defines.
- **The "300 A sandwich" case = adding a RATING, not a product.** Most common admin action; must be easiest.
- Rule: within a product, every rating fills the SAME fixed column set. Admin assumes this but VALIDATES — flags missing/extra column rather than misaligning.

### 3.3 Spec-Table Templates (the shapes)
- **Sandwich** (SPINE, PowerLink): In, Icw, Ipk, R, voltage drop, W×H, Weight.
- **Cast** (PowerCast): In, Icw, Ipk, R, voltage drop (extra PFs); tank colour in band; no W/H/Weight.
- **Track** (PowerTrack): dual AC/DC classes + tap-off sub-table.
- New shape = one-time developer task -> becomes reusable template.

---

## 4. Offer Generator (User flow)

### 4.1 Inputs — every variable
Typed per quote:
- Project name; Client name; Reference number; Revision number.
- Validity (typed, pre-filled default — wording varies, e.g. "5 working days" / "7 working days").
- Warranty months (typed, default 12).
- LME baseline price USD/Ton (typed; appears when an escalation clause applies; for BOTH metals; NOT hard-coded 9000).
Auto-filled:
- Date — auto today's date, format "04 June 2026" (spelled month, unambiguous for cross-border), EDITABLE for post-dating to LC/issue date.
Selected (not typed):
- Product(s) — multi-select, 1..many.
- Per product: material (if applicable), Local/Export, Ratings (multi-select, 1..many — ANY count).
Pasted:
- Price breakdown (BOQ) from Excel.

### 4.2 Output document structure (assembled order)
1. **Cover** — pixel-perfect from master; project/client/date/reference/revision filled.
2. **Table of Contents** — nested (H1 + H2 sub-items), page numbers on EVERY entry, dot leaders, red title rule. Field-based; populates when opened in Word.
3. **Company Introduction** (+ Factory Overview) — fixed.
4. **Product Overview** — one self-contained block PER product: red subtitle, summary, diagram (or placeholder), certifications (or placeholders). Cert row auto-sizes to count. (DECISION: per-product blocks, confirmed.)
5. **Technical Specification** — ONE COMBINED section; each product a red sub-block: Product Guarantees band (constants lifted out of the grid) + Selected Ratings table (one row per selected rating; variable count; grows downward; two-zone redesign). (DECISION: combined, confirmed.)
6. **Price Breakdown** — ONE consolidated table from pasted BOQ, grouped by product, grand total. (DECISION: single consolidated table, confirmed.)
7. **Commercial Offer** — Payment, Delivery Period, Delivery Place, Price, Country of Origin, Specifications, Validity. Varies by Local/Export.
8. **Terms & Conditions** — Warranty, Conditions of Sale, Factory Test.
9. **Contact page** — "ELSEWEDY ELECTRIC for Electrical Products S.A.E" block — fixed from master, MUST be preserved.
10. **Footer on all body pages** — "BUSWAY SYSTEM" left, page number bottom-right in red, thin divider above.

### 4.3 Spec page — two-zone redesign (replaces the old messy table)
- Zone 1 **Product Guarantees**: family-wide constants in a clean labelled band (red mini-labels), lifted OUT of the data grid.
- Zone 2 **Selected Ratings**: rows = selected ratings (not columns). 1 rating = 1 tidy row; up to full family fits because it grows downward. Current rating bold red on left; then the client-facing numbers.
- Removes original problems: stray "Rating" tab, yellow highlighter marks, 14-column squeeze, flat grid, "Impedence" typo.

### 4.4 Price breakdown ingestion
- Pasted from Excel. Standard columns: Item, Type, Description, QTY, Unit, Unit Price, Total Price.
- Parser matches by HEADER NAME not position. Common case frictionless.
- Missing/renamed/extra column -> FLAG for confirmation, never ship a wrong table.
- Distinguishes group sub-header rows from line items; warns on totals that don't add up or leftover "xxx" placeholders.

### 4.5 Variable-count behaviour (critical)
- Ratings = rows -> any count 1..full family, never cramped, no landscape.
- Products -> each adds one overview block + one spec sub-block (+ grouped price rows). 1 = clean single; 3 = same unit repeated.
- Nothing in form or output assumes a fixed count.

---

## 5. Terms & Conditions — FOUR-WAY differentiation (material × Local/Export)

Verified from the real files. Terms are keyed to BOTH axes.

### 5.1 By Local vs Export
- **Local** (Cu & Alu identical in files): USD/LME price-alignment line; "no special adaptation for transformer/generator"; one-week shop drawings; cancellation fees clause; 1%-per-week transport fine.
- **Export**: detailed "does not include" group (Spare Parts / Type Test Repetition / Adaptation at site); site-coordination-workshop shop drawings + MOM; four-week approval cycle; 2%-per-month shipment-delay clause; full 10/30/60/80/100% cancellation schedule.

### 5.2 By material (the escalation clause)
- **Copper-Export** carries the LME escalation block: price-alignment WITH baseline figure, escalation paragraph, formula, 5 definition lines.
  - Formula: P1 = P0 [ 0.7 (Cu1 − Cu0) / Cu0 + 1 ]
  - Cu1 = new copper price (LME at manufacturing shop-drawing approval); Cu0 = baseline (typed); P1 new unit price; P0 old unit price.
  - Rendered in **Latin Modern Roman**, italic variables, in a left-red-bar formula box.
- **Aluminium-Export** escalation: SAME structure, coefficient **0.7** (same), variables **Al1/Al0**, baseline = typed `{{LME_BASELINE}}`. (Created by analogy — did not exist in source files; confirmed by user.)
- Baseline price is a TYPED field for both metals.

### 5.3 Conditions of Sale cleanup (visual only, wording preserved)
- Nested "does not include" group as indented sub-bullets.
- Cancellation schedule: each % bold red as anchor + condition beside it.
- Everything else clean dash bullets. NO wording changed in that pass.
- (Open: user later asked to FIX grammar quirks — see Open Items.)

---

## 6. Admin Screen (Admin flow)

Gated/separate from the everyday builder.

### 6.1 Manage Products
- Create/edit/retire. Fields: name, subtitle, material, summary, guarantees band, terms overrides.
- Upload diagram + cert images (drag-drop). Missing -> placeholder auto-used.
- Pick spec-table template (Sandwich/Cast/Track).
- Saved products appear in generator immediately.

### 6.2 Manage Ratings (the "300 A" path — most common)
- Open product -> ratings list -> "Add rating" -> enter In + template columns -> save -> instantly selectable.
- Edit/remove ratings. Validation per §3.2.

### 6.3 Manage standard text (default-filled fields)
- Edit validity default, warranty default, etc. — so "mostly the same, occasionally changes" values are editable without code.

### 6.4 Validation & safety
- Flag missing/extra spec columns. Flag missing images (which products fall back to placeholder). Confirm before retiring a referenced product.

### 6.5 Three levels of change (by rarity/difficulty)
1. Add/edit a RATING in an existing product — trivial, pure data entry (300 A case).
2. Add a NEW PRODUCT reusing an existing table shape — moderate (fields + template + ratings).
3. Add a product with a STRUCTURALLY NEW table (PowerTrack-style) — rare, one-time developer, then reusable.

---

## 7. Placeholder System

Any product missing a diagram or certs renders a clean dashed-border on-brand placeholder sized to the real asset's footprint ("PRODUCT DIAGRAM — [name] — image to be inserted"). Reads as intentional. Real artwork drops in later with ZERO layout shift. Cert placeholders hatched, count auto-sized. (PowerCast & PowerTrack currently have NO diagram/cert artwork in any file — they ship on placeholders until real renders arrive from product/marketing.)

---

## 8. Master Template & Token Map (CRITICAL build findings)

Pixel-perfect cover/contact come from templating the REAL source .docx, NOT rebuilding.
- Master = **Cu_Export** (richest; simpler variants = remove/swap, not add). Tokenized `MASTER_TEMPLATE.docx` prepared.
- **Brand font = Montserrat** (cover) — confirm installed on target machines or EMBED in the .docx.
- Cover hero image byte-identical across all four source files (verified by MD5) — shell is genuinely shared.

**Tokens placed in master:**
| Token | Field | Note |
|-------|-------|------|
| {{PROJECT_NAME}} | Cover project name | WARNING: in a Title-bound `<w:sdt>` content control — plain text/token swap does NOT update it. MUST update via content control (tag/binding) or rewrite the sdt. Verified failing twice. SOLVE FIRST. |
| {{CLIENT_NAME}} | Cover client | plain run, clean |
| {{DATE}} | Cover date | auto today, editable |
| {{REFERENCE}} | Cover reference | plain run |
| {{REVISION}} | Cover revision | plain run |
| {{VALIDITY}} | Validity clause | typed, default |
| {{WARRANTY_MONTHS}} | Warranty | typed, default 12 |
| {{LME_BASELINE}} | Escalation baseline | typed; both metals; feeds formula + definition line |

- **Cover fields are DUPLICATED in document.xml** (two render paths) — BOTH must update.
- **Certificates** = single composite strip (image6.png), splittable into 4 cards. (SPINE/PowerLink have real certs; PowerCast/PowerTrack do not yet.)

---

## 9. Design / Brand Tokens (locked from mocks)

- Brand red #C8102E (section rules, accents, percentages, page numbers, product subtitles).
- Dark #1A1A1A; Navy sub-labels #1F3864; Grey captions #6B7280.
- Table header band #2E2E2E white text; zebra #F4F6F8; hairlines #D0D5DB.
- Cover/brand font **Montserrat**; equation font **Latin Modern Roman** (italic variables).
- Section title = bold black ALL-CAPS over red bottom rule. Sub-label = bold navy. Product sub-block head = bold red.
- Page US Letter (12240 × 15840 DXA), ~1" margins, content width 9360 DXA.

---

## 10. Build Phases (suggested order)

1. Data model + Product Library (products -> ratings; the four products seeded; 3 templates).
2. Master-template engine — fill tokens; SOLVE {{PROJECT_NAME}} content-control FIRST; handle duplicated cover fields; preserve contact page.
3. Generator core — assemble body sections from library + inputs (two-zone spec, per-product overview, combined spec, consolidated price, four-way terms, footer, nested field TOC).
4. Excel BOQ ingestion — header-matching + validation.
5. Admin screen — products + ratings + standard-text management, image upload, validation, role gating.
6. Placeholder system wired through generator.
7. Handover Guide (non-technical, screenshots).

---

## 11. Open Items (decide during build)

- Spec columns: LEAN (resistance @20° + voltage drop) vs FULL (R35, reactance, full impedance, all power factors) for client output. **Still pending.**
- PowerTrack Track table: bespoke dual AC/DC + tap-off shape. **Needs design.**
- Local terms variants (Cu/Alu): apply same cleaned treatment as export pair. **Pending build.**
- Grammar fixes: user requested fixing quirks ("within one month week", "All submitted rating is normal rating", "Impedence"). Apply during build (distinct from the earlier "preserve wording" pass).
- Equation font: confirm Latin Modern present on target machines, else embed.
- Aluminium escalation baseline value: typed each offer (no default figure agreed).
- TOC renders blank until opened in Word (field) — expected; confirm acceptable or pre-compute.

---

## 12. Source Files (reference)

- Cu_Export.docx — MASTER (richest; copper LME escalation; full export terms).
- Alu_Export.docx — aluminium export (no escalation in source).
- Cu_Local_.docx / Alu_Local_.docx — local variants (identical terms to each other in files).
- PowerCast_New_Tech_Tables.docx — PowerCast spec tables (no images).
- PowerTrack_New_Tech_Tables.docx — PowerTrack spec tables incl. tap-off (no images).
- All four full offers share byte-identical cover hero + 8 media files.

---

*Complete record of decisions from the design sessions. Hand to Claude Code with MASTER_TEMPLATE.docx as the build specification.*
