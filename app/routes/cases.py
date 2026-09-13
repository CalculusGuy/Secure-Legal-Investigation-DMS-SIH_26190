"""
Case management blueprint.
"""
from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, abort
)
from flask_login import login_required, current_user
from app import db
from app.models import Case, Document
from app.ledger.chain import AuditLedger
from flask import current_app

cases_bp = Blueprint("cases", __name__, url_prefix="/cases")


def _ledger():
    return AuditLedger(current_app.config["LEDGER_PATH"])


@cases_bp.route("/")
@login_required
def list_cases():
    cases = Case.query.order_by(Case.created_at.desc()).all()
    return render_template("cases.html", cases=cases)


@cases_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if not current_user.can_upload():
        abort(403)

    if request.method == "POST":
        number = request.form.get("case_number", "").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not number or not title:
            flash("Case number and title are required.", "error")
            return redirect(url_for("cases.new"))

        if Case.query.filter_by(case_number=number).first():
            flash("Case number already exists.", "error")
            return redirect(url_for("cases.new"))

        c = Case(
            case_number=number,
            title=title,
            description=description,
            status="OPEN",
            created_by=current_user.id,
        )
        db.session.add(c)
        db.session.commit()

        _ledger().append(
            event_type="CASE_CREATED",
            payload={"case_id": c.id, "case_number": number, "title": title},
            actor=current_user.username,
        )

        flash("Case '{}' created.".format(number), "success")
        return redirect(url_for("cases.detail", case_id=c.id))

    return render_template("case_new.html")


@cases_bp.route("/<int:case_id>")
@login_required
def detail(case_id):
    c = Case.query.get_or_404(case_id)
    docs = Document.query.filter_by(case_id=c.id).order_by(Document.created_at.desc()).all()
    return render_template("case_detail.html", case=c, documents=docs)