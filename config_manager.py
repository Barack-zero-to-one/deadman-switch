"""
Dead Man's Switch — Config Manager
Encrypted JSON configuration stored in ~/.deadman/vault.enc
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from crypto import decrypt_config, encrypt_config

_VAULT_DIR: Path = Path.home() / ".deadman"
_VAULT_FILE: Path = _VAULT_DIR / "vault.enc"

_DEFAULT_CONFIG: Dict[str, Any] = {
    "interval_days": 7,
    "last_checkin": None,
    "deadline": None,
    "smtp": {
        "host": "",
        "port": 587,
        "user": "",
        "password": "",
    },
    "recipients": [],
    "messages": [],
}


def config_exists() -> bool:
    """Return True if a vault file already exists on disk."""
    return _VAULT_FILE.exists()


def load_config(password: str) -> Dict[str, Any]:
    """
    Read and decrypt the vault file, returning the config as a dict.

    Raises:
        FileNotFoundError: if no vault exists yet.
        ValueError: if the password is wrong or the file is corrupted.
    """
    if not _VAULT_FILE.exists():
        raise FileNotFoundError("No vault found. Run the setup wizard first.")
    blob = _VAULT_FILE.read_bytes()
    raw = decrypt_config(blob, password)
    return json.loads(raw.decode("utf-8"))


def save_config(cfg: Dict[str, Any], password: str) -> None:
    """
    Encrypt and atomically write the config dict to the vault file.

    Uses tempfile + os.replace so a crash during write never corrupts the vault.
    """
    _VAULT_DIR.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(cfg, ensure_ascii=False, indent=2).encode("utf-8")
    blob = encrypt_config(raw, password)

    fd, tmp_path = tempfile.mkstemp(dir=_VAULT_DIR, suffix=".tmp")
    try:
        os.write(fd, blob)
    finally:
        os.close(fd)
    os.replace(tmp_path, _VAULT_FILE)


def default_config() -> Dict[str, Any]:
    """Return a fresh default config dict."""
    import copy
    return copy.deepcopy(_DEFAULT_CONFIG)
