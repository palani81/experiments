"""Credential encryption for NAS Explorer.

Uses Fernet symmetric encryption with an auto-generated key stored
separately from the config file. This ensures passwords in
nas_connection.json are never stored in plaintext.

Key storage: data/.encryption_key (auto-created on first use)
"""
from __future__ import annotations

import os
import logging
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from .config import settings

logger = logging.getLogger("nas_explorer.crypto")

_fernet: Fernet | None = None
_ENCRYPTED_PREFIX = "enc:"


def _key_path() -> str:
    """Path to the encryption key file, next to the database."""
    data_dir = Path(settings.database_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / ".encryption_key")


def _get_fernet() -> Fernet:
    """Get or create the Fernet cipher. Generates a key on first use."""
    global _fernet
    if _fernet is not None:
        return _fernet

    path = _key_path()

    if os.path.exists(path):
        with open(path, "rb") as f:
            key = f.read().strip()
    else:
        key = Fernet.generate_key()
        # Write with restrictive permissions (owner-only read/write)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(key)
        logger.info("Generated new encryption key")

    _fernet = Fernet(key)
    return _fernet


def encrypt(plaintext: str) -> str:
    """Encrypt a string. Returns prefixed ciphertext."""
    if not plaintext:
        return plaintext
    f = _get_fernet()
    token = f.encrypt(plaintext.encode("utf-8"))
    return _ENCRYPTED_PREFIX + token.decode("ascii")


def decrypt(value: str) -> str:
    """Decrypt a value. If it's not encrypted (no prefix), returns as-is for migration."""
    if not value:
        return value
    if not value.startswith(_ENCRYPTED_PREFIX):
        # Plaintext — not yet migrated
        return value
    f = _get_fernet()
    try:
        token = value[len(_ENCRYPTED_PREFIX):].encode("ascii")
        return f.decrypt(token).decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt credential — key may have changed")
        raise ValueError("Decryption failed. The encryption key may have been deleted or changed.")


def is_encrypted(value: str) -> bool:
    """Check if a value is already encrypted."""
    return bool(value) and value.startswith(_ENCRYPTED_PREFIX)
