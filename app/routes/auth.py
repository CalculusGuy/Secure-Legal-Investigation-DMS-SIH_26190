"""
Authentication blueprint: login, logout, first-run admin setup.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.ledger.chain import AuditLedger
from flask import current_app
import os

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _ledger():
    return AuditLedger(current_app.config["LEDGER_PATH"])


@auth_bp.route("/setup", methods=["GET", "POST"])
def setup():
    """One-time setup to create the first admin if none exists."""
    if User.query.count() > 0:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")

        if not username or not password or not full_name:
            flash("All fields are required.", "error")
            return redirect(url_for("auth.setup"))

        u = User(username=username, full_name=full_name, role="admin")
        u.set_password(password)
        db.session.add(u)
        db.session.commit()

        _ledger().append(
            event_type="USER_CREATED",
            payload={"username": username, "role": "admin"},
            actor="system:setup",
        )

        flash("Admin account created. Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("setup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("documents.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            _ledger().append(
                event_type="USER_LOGIN",
                payload={"username": username, "ip": request.remote_addr},
                actor=username,
            )
            flash("Signed in successfully.", "success")
            return redirect(url_for("documents.dashboard"))
        else:
            flash("Invalid credentials.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    _ledger().append(
        event_type="USER_LOGOUT",
        payload={"username": current_user.username},
        actor=current_user.username,
    )
    logout_user()
    flash("Signed out.", "success")
    return redirect(url_for("auth.login"))