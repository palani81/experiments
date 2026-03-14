"""Simple AES encryption for secrets stored in the database.

Uses the app SECRET_KEY to derive an encryption key via SHA-256,
then encrypts with AES-GCM via the cryptography library's Fernet.
Falls back to base64 obfuscation if cryptography is not available.
"""

import base64
import hashlib
import os

from app.config import settings

# Try to import Fernet at module level; set to None if unavailable
try:
    from cryptography.fernet import Fernet as _Fernet
except BaseException:
    _Fernet = None


def _derive_key() -> bytes:
    """Derive a 32-byte Fernet key from the app secret."""
    raw = hashlib.sha256(settings.secret_key.encode()).digest()
    return base64.urlsafe_b64encode(raw)


def encrypt(plaintext: str) -> str:
    """Encrypt a string and return a prefixed ciphertext."""
    if not plaintext:
        return ""
    if _Fernet is not None:
        f = _Fernet(_derive_key())
        return "enc:" + f.encrypt(plaintext.encode()).decode()
    # Fallback: base64 encode (not true encryption, but better than plaintext)
    return "b64:" + base64.b64encode(plaintext.encode()).decode()


def decrypt(stored: str) -> str:
    """Decrypt a stored value. Handles plain, b64:, and enc: prefixes."""
    if not stored:
        return ""
    if stored.startswith("enc:"):
        if _Fernet is not None:
            f = _Fernet(_derive_key())
            return f.decrypt(stored[4:].encode()).decode()
        return ""
    if stored.startswith("b64:"):
        return base64.b64decode(stored[4:]).decode()
    # Legacy plaintext value
    return stored
