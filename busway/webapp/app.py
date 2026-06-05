"""Flask routes for the Busway Offer Generator web UI."""
from __future__ import annotations

import os
import tempfile
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for, session,
    send_file, flash, abort,
)

from ..library import Library, StandardText, DATA_DIR
from ..models import Product, Rating, GuaranteeItem, Note1Fields, SpecShape, columns_for
from ..boq import parse_pasted
from ..generator import generate_offer, OfferInput, ProductSelection
from ..notes import compose_note1
from .. import fill

MEDIA_DIR = DATA_DIR / "media"


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("BUSWAY_SECRET", "busway-dev-secret-change-me")
    app.config["ADMIN_PASSWORD"] = os.environ.get("BUSWAY_ADMIN_PASSWORD", "admin")
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    # -- helpers -------------------------------------------------------
    def admin_required(f):
        @wraps(f)
        def wrapper(*a, **kw):
            if not session.get("is_admin"):
                return redirect(url_for("admin_login", next=request.path))
            return f(*a, **kw)
        return wrapper

    def lib() -> Library:
        return Library.load()

    def stext() -> StandardText:
        return StandardText.load()

    # =================================================================
    # USER — generator
    # =================================================================
    @app.route("/")
    def index():
        library = lib()
        st = stext()
        products = []
        for p in library.active():
            products.append({
                "id": p.id, "name": p.name, "subtitle": p.subtitle,
                "conductor": p.conductor_material,
                "shape": p.spec_shape.value,
                "ratings": [{"key": f"{r.in_amps}|{r.variant}", "label": r.label()}
                            for r in p.sorted_ratings()],
            })
        defaults = st.get("defaults", {})
        return render_template("generator.html", products=products,
                               defaults=defaults, today=fill.date_today())

    @app.route("/generate", methods=["POST"])
    def generate():
        f = request.form
        selected_ids = f.getlist("product")
        if not selected_ids:
            flash("Select at least one product.", "error")
            return redirect(url_for("index"))

        selections = []
        for pid in selected_ids:
            ratings = []
            for val in f.getlist(f"ratings__{pid}"):
                amps, _, variant = val.partition("|")
                try:
                    ratings.append((float(amps), variant))
                except ValueError:
                    pass
            selections.append(ProductSelection(
                product_id=pid,
                local_export=f.get(f"localexport__{pid}", "Export"),
                ratings=ratings,
            ))

        boq_text = f.get("boq", "").strip()
        boq_rows, boq_warnings, boq_errors = [], [], []
        if boq_text:
            res = parse_pasted(boq_text)
            boq_rows, boq_warnings, boq_errors = res.rows, res.warnings, res.errors
            if boq_errors:
                for e in boq_errors:
                    flash(f"BOQ: {e}", "error")
                return redirect(url_for("index"))

        inp = OfferInput(
            project_name=f.get("project_name", "").strip(),
            client_name=f.get("client_name", "").strip(),
            reference=f.get("reference", "").strip(),
            revision=f.get("revision", "R0").strip(),
            date=f.get("date", "").strip(),
            validity=f.get("validity", "").strip(),
            warranty_months=f.get("warranty_months", "").strip(),
            lme_baseline=f.get("lme_baseline", "").strip(),
            selections=selections,
            boq_rows=boq_rows,
        )
        tmp = Path(tempfile.mkdtemp(prefix="busway_out_"))
        safe = (inp.reference or inp.project_name or "offer").replace(" ", "_")[:40]
        out = tmp / f"Offer_{safe or 'busway'}.docx"
        try:
            report = generate_offer(inp, out)
        except Exception as exc:  # surface generation errors to the user
            flash(f"Generation failed: {exc}", "error")
            return redirect(url_for("index"))
        for w in boq_warnings:
            flash(f"BOQ warning: {w}", "warn")
        if report["remaining_tokens"]:
            flash("Some tokens were left unfilled: "
                  + ", ".join(report["remaining_tokens"]), "warn")
        return send_file(out, as_attachment=True, download_name=out.name)

    # =================================================================
    # ADMIN — auth
    # =================================================================
    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            if request.form.get("password") == app.config["ADMIN_PASSWORD"]:
                session["is_admin"] = True
                return redirect(request.args.get("next") or url_for("admin_index"))
            flash("Wrong password.", "error")
        return render_template("admin/login.html")

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("is_admin", None)
        return redirect(url_for("index"))

    # =================================================================
    # ADMIN — products & ratings
    # =================================================================
    @app.route("/admin")
    @admin_required
    def admin_index():
        library = lib()
        problems = library.validate()
        return render_template("admin/index.html", products=library.products,
                               problems=problems)

    @app.route("/admin/product/<pid>", methods=["GET", "POST"])
    @admin_required
    def admin_product(pid):
        library = lib()
        p = library.get(pid)
        is_new = p is None
        if is_new:
            p = Product(id=pid, name=pid, spec_shape=SpecShape.SANDWICH)
        if request.method == "POST":
            f = request.form
            p.name = f.get("name", p.name).strip()
            p.subtitle = f.get("subtitle", "").strip()
            p.conductor_material = f.get("conductor_material", "").strip()
            p.summary_paragraph = f.get("summary_paragraph", "").strip()
            p.spec_shape = SpecShape(f.get("spec_shape", p.spec_shape.value))
            p.note1_fields = Note1Fields(
                product_type=f.get("n1_product_type", "").strip(),
                housing=f.get("n1_housing", "").strip(),
                rating_class=f.get("n1_class", "").strip(),
                plating=f.get("n1_plating", "").strip(),
            )
            # guarantees band: parallel arrays
            labels = f.getlist("g_label")
            values = f.getlist("g_value")
            p.guarantees_band = [GuaranteeItem(l.strip(), v.strip())
                                 for l, v in zip(labels, values) if l.strip()]
            library.upsert(p)
            library.save()
            flash(f"Saved {p.name}.", "ok")
            return redirect(url_for("admin_product", pid=p.id))
        return render_template("admin/product.html", p=p, is_new=is_new,
                               shapes=[s.value for s in SpecShape],
                               note1_preview=compose_note1(p))

    @app.route("/admin/product/<pid>/retire", methods=["POST"])
    @admin_required
    def admin_retire(pid):
        library = lib()
        if library.retire(pid):
            library.save()
            flash(f"Retired {pid}.", "ok")
        return redirect(url_for("admin_index"))

    @app.route("/admin/product/<pid>/ratings", methods=["GET", "POST"])
    @admin_required
    def admin_ratings(pid):
        library = lib()
        p = library.get(pid)
        if not p:
            abort(404)
        cols = columns_for(p.spec_shape)
        if request.method == "POST":
            action = request.form.get("action")
            if action == "add":
                amps = request.form.get("in_amps", "").strip()
                variant = request.form.get("variant", "").strip()
                try:
                    in_amps = float(amps)
                except ValueError:
                    flash("Rated current must be a number.", "error")
                    return redirect(url_for("admin_ratings", pid=pid))
                values = {c.key: request.form.get(f"v_{c.key}", "").strip()
                          for c in cols}
                p.ratings.append(Rating(in_amps=in_amps, values=values,
                                        variant=variant))
                flash(f"Added {in_amps:g} A rating.", "ok")
            elif action == "delete":
                idx = int(request.form.get("idx", -1))
                if 0 <= idx < len(p.ratings):
                    removed = p.ratings.pop(idx)
                    flash(f"Removed {removed.label()}.", "ok")
            library.upsert(p)
            library.save()
            return redirect(url_for("admin_ratings", pid=pid))
        return render_template("admin/ratings.html", p=p, cols=cols,
                               problems=p.validate())

    @app.route("/admin/product/<pid>/image", methods=["POST"])
    @admin_required
    def admin_image(pid):
        library = lib()
        p = library.get(pid)
        if not p:
            abort(404)
        file = request.files.get("image")
        kind = request.form.get("kind", "diagram")
        if file and file.filename:
            ext = Path(file.filename).suffix.lower() or ".png"
            name = f"{pid}_{kind}_{len(p.cert_images) if kind == 'cert' else 'diagram'}{ext}"
            dest = MEDIA_DIR / name
            file.save(dest)
            if kind == "cert":
                p.cert_images.append(name)
            else:
                p.diagram_image = name
            library.upsert(p)
            library.save()
            flash(f"Uploaded {name}.", "ok")
        return redirect(url_for("admin_product", pid=pid))

    # =================================================================
    # ADMIN — standard text
    # =================================================================
    @app.route("/admin/text", methods=["GET", "POST"])
    @admin_required
    def admin_text():
        st = stext()
        if request.method == "POST":
            st.data.setdefault("defaults", {})
            st.data["defaults"]["validity"] = request.form.get("validity", "").strip()
            st.data["defaults"]["warranty_months"] = request.form.get(
                "warranty_months", "").strip()
            notes = [n.strip() for n in
                     request.form.get("notes", "").split("\n") if n.strip()]
            st.data["technical_notes_fixed"] = notes
            st.save()
            flash("Standard text saved.", "ok")
            return redirect(url_for("admin_text"))
        return render_template("admin/text.html", st=st.data)

    @app.route("/media/<path:name>")
    def media(name):
        path = MEDIA_DIR / name
        if not path.is_file():
            abort(404)
        return send_file(path)

    return app
