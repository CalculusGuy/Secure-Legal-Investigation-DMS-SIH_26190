"""
Ed25519 digital signatures — used to bind each document to its uploader.
"""
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


def generate_keypair():
    """Return (private_bytes, public_bytes) in raw format."""
    priv = Ed25519PrivateKey.generate()
    priv_b = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_b = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return priv_b, pub_b


def sign(private_bytes, message):
    """Return the raw 64-byte signature."""
    priv = Ed25519PrivateKey.from_private_bytes(private_bytes)
    return priv.sign(message)


def verify(public_bytes, message, signature):
    """Return True if signature is valid, False otherwise."""
    try:
        pub = Ed25519PublicKey.from_public_bytes(public_bytes)
        pub.verify(signature, message)
        return True
    except Exception:
        return False
