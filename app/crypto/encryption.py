"""
AES-256-GCM encryption at rest.

The 32-byte master key is taken from config. In production this should be
derived per-user from a passphrase via Argon2id; for the prototype we use
a single app master key (rotated via env var).
"""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


NONCE_LEN = 12   # 96-bit nonce, standard for GCM


def _key_bytes(master_hex):
    raw = bytes.fromhex(master_hex)
    if len(raw) != 32:
        raise ValueError("Master key must be 32 bytes (64 hex chars)")
    return raw


def encrypt_bytes(plaintext, master_hex):
    """Return nonce || ciphertext || tag."""
    key = _key_bytes(master_hex)
    nonce = os.urandom(NONCE_LEN)
    aes = AESGCM(key)
    ct = aes.encrypt(nonce, plaintext, associated_data=None)
    return nonce + ct


def decrypt_bytes(blob, master_hex):
    """Inverse of encrypt_bytes."""
    key = _key_bytes(master_hex)
    if len(blob) < NONCE_LEN + 16:
        raise ValueError("Ciphertext too short")
    nonce = blob[:NONCE_LEN]
    ct = blob[NONCE_LEN:]
    aes = AESGCM(key)
    return aes.decrypt(nonce, ct, associated_data=None)
