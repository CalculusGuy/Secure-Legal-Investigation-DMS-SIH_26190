"""
SAT-DMS Configuration
Central settings for the Secure Digital Document Management System.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Flask ---
    SECRET_KEY = os.environ.get("SAT_DMS_SECRET", "dev-change-me-in-production")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "sat-dms.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Storage ---
    STORAGE_ENCRYPTED = os.path.join(BASE_DIR, "storage", "encrypted")
    STORAGE_KEYS      = os.path.join(BASE_DIR, "storage", "keys")
    LEDGER_PATH       = os.path.join(BASE_DIR, "instance", "audit_chain.json")

    # --- Upload limits ---
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024   # 50 MB

    # --- Crypto ---
    APP_MASTER_KEY_HEX = os.environ.get(
        "SAT_DMS_MASTER_KEY",
        "0" * 64,
    )
