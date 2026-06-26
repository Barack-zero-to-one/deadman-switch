"""
Dead Man's Switch — Crypto Layer
AES-256-GCM encryption for local config storage, keyed via PBKDF2HMAC.
"""

from __future__ import annotations

import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_BACKEND = default_backend()
_SALT_BYTES: int = 16
_NONCE_BYTES: int = 12
_KEY_BYTES: int = 32
_ITERATIONS: int = 480_000


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a master password using PBKDF2HMAC-SHA256."""
    if not password:
        raise ValueError("Master password must not be empty.")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=_KEY_BYTES,
        salt=salt,
        iterations=_ITERATIONS,
        backend=_BACKEND,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_config(data: bytes, password: str) -> bytes:
    """
    Encrypt data with AES-256-GCM using a password-derived key.

    Wire format:
        [16 B] salt   — random, unique per encryption
        [12 B] nonce  — random GCM nonce
        [ N B] ciphertext + 16-byte GCM authentication tag
    """
    salt = os.urandom(_SALT_BYTES)
    nonce = os.urandom(_NONCE_BYTES)
    key = derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, data, None)
    return salt + nonce + ciphertext


def decrypt_config(blob: bytes, password: str) -> bytes:
    """
    Decrypt a blob produced by encrypt_config.

    Raises:
        ValueError: if the password is wrong or the data is corrupted.
    """
    min_size = _SALT_BYTES + _NONCE_BYTES + 16
    if len(blob) < min_size:
        raise ValueError("Vault file is too short or corrupted.")

    salt = blob[:_SALT_BYTES]
    nonce = blob[_SALT_BYTES : _SALT_BYTES + _NONCE_BYTES]
    ciphertext = blob[_SALT_BYTES + _NONCE_BYTES :]
    key = derive_key(password, salt)

    try:
        return AESGCM(key).decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError(
            "Decryption failed — wrong master password or corrupted vault."
        ) from exc
