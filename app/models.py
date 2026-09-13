"""
Database models for SAT-DMS.
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True, nullable=False, index=True)
    full_name     = db.Column(db.String(128), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(16), nullable=False, default="viewer")
    active        = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    @property
    def is_active(self):
        return self.active

    def is_admin(self):
        return self.role == "admin"

    def can_upload(self):
        return self.role in ("admin", "investigator")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Case(db.Model):
    __tablename__ = "cases"

    id          = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    title       = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text)
    status      = db.Column(db.String(32), default="OPEN")
    created_by  = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    documents = db.relationship("Document", backref="case", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "case_number": self.case_number,
            "title": self.title,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "document_count": len(self.documents),
        }


class Document(db.Model):
    __tablename__ = "documents"

    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(256), nullable=False)
    description     = db.Column(db.Text)
    case_id         = db.Column(db.Integer, db.ForeignKey("cases.id"))
    uploaded_by     = db.Column(db.Integer, db.ForeignKey("users.id"))

    # Cryptographic anchors
    sha256_hash     = db.Column(db.String(64), nullable=False, index=True)
    signature       = db.Column(db.Text, nullable=False)
    signer_pubkey   = db.Column(db.Text, nullable=False)

    # Encrypted blob
    encrypted_path  = db.Column(db.String(512), nullable=False)
    original_size   = db.Column(db.Integer, nullable=False)

    version         = db.Column(db.Integer, default=1)
    parent_id       = db.Column(db.Integer, db.ForeignKey("documents.id"))

    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship("User", foreign_keys=[uploaded_by])

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "case_id": self.case_id,
            "uploaded_by": self.uploaded_by,
            "sha256_hash": self.sha256_hash,
            "signature": self.signature[:32] + "..." if self.signature else "",
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "size": self.original_size,
        }