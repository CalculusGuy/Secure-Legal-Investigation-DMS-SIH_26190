"""
Audit log blueprint: view and verify the tamper-evident chain.
"""
from flask import Blueprint, render_template, current_app
from flask_login import login_required
from app.ledger.chain import AuditLedger

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


@audit_bp.route("/")
@login_required
def index():
    ledger = AuditLedger(current_app.config["LEDGER_PATH"])
    entries = list(reversed(ledger.all()))
    status = ledger.verify()
    return render_template("audit.html", entries=entries, status=status)