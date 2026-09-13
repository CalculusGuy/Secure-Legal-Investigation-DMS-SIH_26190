"""
Admin blueprint: user management.
"""
from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, abort, current_app
)
from flask_login import login_required, current_user
from app import db
from app.models import User
from app.ledger.chain import AuditLedger

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _ledger():
    return AuditLedger(current_app.config["LEDGER_PATH"])


def _require_admin():
    if not current_user.is_authenticated or not current_user.is_admin():
        abort(403)


@admin_bp.route("/users")
@login_required
def users():
    _require_admin()
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=all_users)


@admin_bp.route("/users/new", methods=["POST"])
@login_required
def create_user():
    _require_admin()

    username  = request.form.get("username", "").strip()
    full_name = request.form.get("full_name", "").strip()
    password  = request.form.get("password", "")
    role      = request.form.get("role", "viewer")

    if not username or not full_name or not password:
        flash("All fields are required.", "error")
        return redirect(url_for("admin.users"))

    if role not in ("admin", "investigator", "viewer"):
        flash("Invalid role.", "error")
        return redirect(url_for("admin.users"))

    if User.query.filter_by(username=username).first():
        flash("Username already exists.", "error")
        return redirect(url_for("admin.users"))

    u = User(username=username, full_name=full_name, role=role)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()

    _ledger().append(
        event_type="USER_CREATED",
        payload={"username": username, "role": role, "created_by": current_user.username},
        actor=current_user.username,
    )

    flash("User '{}' created.".format(username), "success")
    return redirect(url_for("admin.users"))