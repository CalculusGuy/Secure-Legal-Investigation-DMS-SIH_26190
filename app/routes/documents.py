"""
Document blueprint: upload, list, view, download, verify, search, version.
"""
import os
import hashlib
import base64
from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, send_file, current_app, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_

from app import db
from app.models import Document, Case, User
from app.ledger.chain import AuditLedger
from app.crypto.encryption import encrypt_bytes, decrypt_bytes
from app.crypto.signatures import generate_keypair, sign, verify

documents_bp = Blueprint("documents", __name__, url_prefix="/documents")


def _ledger():
    return AuditLedger(current_app.config["LEDGER_PATH"])


def _user_keypair(user):
    """Load-or-create a persistent Ed25519 keypair per user, stored on disk."""
    keydir = current_app.config["STORAGE_KEYS"]
    os.makedirs(keydir, exist_ok=True)
    priv_path = os.path.join(keydir, "user_{}_private.key".format(user.id))
    pub_path  = os.path.join(keydir, "user_{}_public.key".format(user.id))

    if not (os.path.exists(priv_path) and os.path.exists(pub_path)):
        priv_b, pub_b = generate_keypair()
        with open(priv_path, "wb") as f:
            f.write(priv_b)
        with open(pub_path, "wb") as f:
            f.write(pub_b)
        try:
            os.chmod(priv_path, 0o600)
        except Exception:
            pass

    with open(priv_path, "rb") as f:
        priv_b = f.read()
    with open(pub_path, "rb") as f:
        pub_b = f.read()
    return priv_b, pub_b


@documents_bp.route("/")
@login_required
def dashboard():
    docs = Document.query.order_by(Document.created_at.desc()).limit(20).all()
    cases = Case.query.order_by(Case.created_at.desc()).limit(20).all()

    ledger = _ledger()
    ledger_status = ledger.verify()

    return render_template(
        "dashboard.html",
        documents=docs,
        cases=cases,
        ledger_status=ledger_status,
    )


@documents_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if not current_user.can_upload():
        abort(403)

    cases = Case.query.order_by(Case.case_number).all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        case_id = request.form.get("case_id") or None
        description = request.form.get("description", "").strip()
        file = request.files.get("file")

        if not title or not file or file.filename == "":
            flash("Title and file are required.", "error")
            return redirect(url_for("documents.upload"))

        raw = file.read()
        if not raw:
            flash("Uploaded file is empty.", "error")
            return redirect(url_for("documents.upload"))

        # Integrity anchor
        sha256 = hashlib.sha256(raw).hexdigest()

        # Sign with the uploader's Ed25519 key
        priv_b, pub_b = _user_keypair(current_user)
        sig = sign(priv_b, raw)

        # Encrypt at rest
        ciphertext = encrypt_bytes(raw, current_app.config["APP_MASTER_KEY_HEX"])

        # Persist ciphertext
        fname = "{}_{}.enc".format(int(datetime.utcnow().timestamp()), secure_filename(file.filename))
        enc_path = os.path.join(current_app.config["STORAGE_ENCRYPTED"], fname)
        with open(enc_path, "wb") as f:
            f.write(ciphertext)

        doc = Document(
            title=title,
            description=description,
            case_id=int(case_id) if case_id else None,
            uploaded_by=current_user.id,
            sha256_hash=sha256,
            signature=base64.b64encode(sig).decode(),
            signer_pubkey=base64.b64encode(pub_b).decode(),
            encrypted_path=enc_path,
            original_size=len(raw),
            version=1,
        )
        db.session.add(doc)
        db.session.commit()

        _ledger().append(
            event_type="DOCUMENT_UPLOADED",
            payload={
                "document_id": doc.id,
                "title": doc.title,
                "sha256": sha256,
                "case_id": doc.case_id,
            },
            actor=current_user.username,
        )

        flash("Document '{}' uploaded and sealed.".format(title), "success")
        return redirect(url_for("documents.view", doc_id=doc.id))

    return render_template("upload.html", cases=cases)


@documents_bp.route("/search")
@login_required
def search():
    """Search documents by title, description, case number, uploader, or hash."""
    q = request.args.get("q", "").strip()
    results = []

    if q:
        like = "%{}%".format(q)
        results = (
            Document.query
            .outerjoin(Case, Document.case_id == Case.id)
            .outerjoin(User, Document.uploaded_by == User.id)
            .filter(or_(
                Document.title.ilike(like),
                Document.description.ilike(like),
                Document.sha256_hash.ilike(like),
                Case.case_number.ilike(like),
                Case.title.ilike(like),
                User.username.ilike(like),
            ))
            .order_by(Document.created_at.desc())
            .limit(100)
            .all()
        )

    _ledger().append(
        event_type="DOCUMENT_SEARCH",
        payload={"query": q, "results": len(results)},
        actor=current_user.username,
    )

    return render_template("search.html", query=q, results=results)


@documents_bp.route("/<int:doc_id>")
@login_required
def view(doc_id):
    doc = Document.query.get_or_404(doc_id)
    children = Document.query.filter_by(parent_id=doc.id).order_by(Document.version).all()
    return render_template("document_detail.html", doc=doc, children=children)


@documents_bp.route("/<int:doc_id>/download")
@login_required
def download(doc_id):
    doc = Document.query.get_or_404(doc_id)

    with open(doc.encrypted_path, "rb") as f:
        ciphertext = f.read()

    try:
        plaintext = decrypt_bytes(ciphertext, current_app.config["APP_MASTER_KEY_HEX"])
    except Exception as e:
        flash("Decryption failed: {}".format(e), "error")
        return redirect(url_for("documents.view", doc_id=doc.id))

    # Verify integrity before returning
    computed = hashlib.sha256(plaintext).hexdigest()
    if computed != doc.sha256_hash:
        flash("INTEGRITY FAILURE: document hash mismatch.", "error")
        return redirect(url_for("documents.view", doc_id=doc.id))

    _ledger().append(
        event_type="DOCUMENT_DOWNLOADED",
        payload={"document_id": doc.id, "sha256": computed},
        actor=current_user.username,
    )

    tmp_path = os.path.join(current_app.config["STORAGE_ENCRYPTED"], "_dl_{}.bin".format(doc.id))
    with open(tmp_path, "wb") as f:
        f.write(plaintext)

    return send_file(tmp_path, as_attachment=True, download_name="{}.bin".format(doc.title))


@documents_bp.route("/<int:doc_id>/verify")
@login_required
def verify_doc(doc_id):
    """Re-verify integrity and signature on demand."""
    doc = Document.query.get_or_404(doc_id)
    result = {"hash_ok": False, "signature_ok": False, "notes": []}

    try:
        with open(doc.encrypted_path, "rb") as f:
            ciphertext = f.read()
        plaintext = decrypt_bytes(ciphertext, current_app.config["APP_MASTER_KEY_HEX"])

        computed = hashlib.sha256(plaintext).hexdigest()
        result["hash_ok"] = (computed == doc.sha256_hash)
        if not result["hash_ok"]:
            result["notes"].append("Hash mismatch: file has been modified.")

        sig = base64.b64decode(doc.signature)
        pub_b = base64.b64decode(doc.signer_pubkey)
        result["signature_ok"] = verify(pub_b, plaintext, sig)
        if not result["signature_ok"]:
            result["notes"].append("Signature invalid: signer or content altered.")

    except Exception as e:
        result["notes"].append("Verification error: {}".format(e))

    _ledger().append(
        event_type="DOCUMENT_VERIFIED",
        payload={
            "document_id": doc.id,
            "hash_ok": result["hash_ok"],
            "signature_ok": result["signature_ok"],
        },
        actor=current_user.username,
    )

    return render_template("verify.html", doc=doc, result=result)


@documents_bp.route("/<int:doc_id>/new-version", methods=["GET", "POST"])
@login_required
def new_version(doc_id):
    """Upload a new version of an existing document, preserving the chain."""
    if not current_user.can_upload():
        abort(403)

    parent = Document.query.get_or_404(doc_id)

    if request.method == "POST":
        file = request.files.get("file")
        note = request.form.get("note", "").strip()

        if not file or file.filename == "":
            flash("A file is required.", "error")
            return redirect(url_for("documents.new_version", doc_id=doc_id))

        raw = file.read()
        if not raw:
            flash("Uploaded file is empty.", "error")
            return redirect(url_for("documents.new_version", doc_id=doc_id))

        sha256 = hashlib.sha256(raw).hexdigest()
        priv_b, pub_b = _user_keypair(current_user)
        sig = sign(priv_b, raw)
        ciphertext = encrypt_bytes(raw, current_app.config["APP_MASTER_KEY_HEX"])

        fname = "{}_{}.enc".format(int(datetime.utcnow().timestamp()), secure_filename(file.filename))
        enc_path = os.path.join(current_app.config["STORAGE_ENCRYPTED"], fname)
        with open(enc_path, "wb") as f:
            f.write(ciphertext)

        new_doc = Document(
            title=parent.title,
            description=(note or parent.description or ""),
            case_id=parent.case_id,
            uploaded_by=current_user.id,
            sha256_hash=sha256,
            signature=base64.b64encode(sig).decode(),
            signer_pubkey=base64.b64encode(pub_b).decode(),
            encrypted_path=enc_path,
            original_size=len(raw),
            version=(parent.version or 1) + 1,
            parent_id=parent.id,
        )
        db.session.add(new_doc)
        db.session.commit()

        _ledger().append(
            event_type="DOCUMENT_VERSION_CREATED",
            payload={
                "parent_id": parent.id,
                "new_document_id": new_doc.id,
                "new_version": new_doc.version,
                "sha256": sha256,
                "note": note,
            },
            actor=current_user.username,
        )

        flash("Version v{} created for '{}'.".format(new_doc.version, parent.title), "success")
        return redirect(url_for("documents.view", doc_id=new_doc.id))

    return render_template("new_version.html", parent=parent)