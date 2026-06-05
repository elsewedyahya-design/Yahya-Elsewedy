# Elsewedy Busway Offer Generator — Handover Guide

A plain-English guide for everyday use. No coding needed to run it.

---

## 1. What this app does

It turns your product library plus a few quote details into a finished,
**editable Microsoft Word offer** — with the pixel-perfect Elsewedy cover and
contact pages kept exactly as in the master template.

- Pick one or more busway products, choose their ratings, set Local/Export.
- Paste the Bill of Quantities straight from Excel (optional).
- Click **Generate** → a Word `.docx` downloads, ready to review and send.

A single product gives a clean single-product offer; several products repeat
the specification section per product.

---

## 2. Starting the app

1. Open a terminal in the project folder (`Master Template`).
2. First time only, install the requirements:
   ```
   python -m pip install -r requirements.txt
   ```
3. Run it:
   ```
   python -m busway.webapp
   ```
4. Open your browser at **http://127.0.0.1:5000**

To stop the app, press `Ctrl + C` in the terminal.

---

## 3. Generating an offer (the "Generate" page)

1. Fill in the project details: project name, client, reference, revision,
   date, validity, warranty, and the LME baseline (USD/ton) if escalation
   applies.
2. Tick the products you want. For each ticked product:
   - choose **Local** or **Export**,
   - tick the ratings to include (leave all unticked to include every rating).
3. (Optional) Paste the BOQ from Excel into the **Bill of Quantities** box.
   Columns are matched by name, so the order doesn't matter — you just need
   *Description, Qty, Unit Price, Total Price*. The app warns you about bad
   totals or leftover "xxx" placeholders.
4. Click **Generate offer (.docx)**. The file downloads automatically.

The validity and warranty boxes pre-fill from the standard defaults you set in
the Admin area, and the LME figure you enter replaces the baseline in the
Conditions of Sale.

---

## 4. The Admin area (managing products)

Click **Admin** in the top bar and log in.

- The default password is `admin`. To change it, set the
  `BUSWAY_ADMIN_PASSWORD` environment variable before starting the app.

What you can do:

- **Products** — add a new product (give it a short id like `spine`), edit its
  name, subtitle, conductor, spec-table shape, summary, the four Note-1 fields
  (which auto-compose Technical Note 1, shown live), and the guarantees band.
- **Ratings** — add or remove rated-current rows for a product. The page warns
  you if a rating is missing any of its template columns.
- **Images** — upload a product diagram or certificate images. Until a diagram
  is uploaded the offer shows a clean dashed "to be added" placeholder in its
  slot.
- **Standard text & defaults** — set the default validity, default warranty,
  and the fixed technical notes that appear in every offer.

Retiring a product hides it from the Generate page without deleting its data.

---

## 5. Where things are saved

- Product library and standard text: the `data/` folder (`library.json`,
  `standard_text.json`).
- Uploaded images: `data/media/`.
- The pixel-perfect master: `MASTER_TEMPLATE.docx` (don't edit by hand).

Everything is editable later through the Admin area — nothing is hard-coded
into the program.

---

## 6. Known follow-ups (for the developer)

These are documented so nothing is a surprise:

- **Electrical values per rating** are scaffolded but mostly empty
  (`TODO(data)` in `scripts/seed_library.py`). Fill them in via the Admin
  **Ratings** pages or by extracting from the source datasheets.
- **Embedding uploaded diagrams** into the generated spec section needs the
  Word package relationship plumbing; today the layout shows a labelled
  placeholder where the diagram will sit. Cover/contact images are unaffected.
- **PowerTrack** uses a bespoke spec layout that is still to be finalised.
- **Security:** the GitHub Personal Access Token used during the build appears
  in the chat transcript — please **revoke/rotate it** in GitHub settings.

---

## 7. Quick troubleshooting

- *"No module named flask"* → run `python -m pip install -r requirements.txt`.
- *Page won't load* → make sure the terminal still shows the app running and
  you're using `http://127.0.0.1:5000`.
- *A token like `{{PROJECT_NAME}}` shows in the offer* → that field was left
  blank on the Generate page; fill it and regenerate.
