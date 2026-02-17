"""Tests for the credential encryption module."""

import os
import pytest
from app.crypto import encrypt, decrypt, is_encrypted, _key_path, _ENCRYPTED_PREFIX
from app import crypto


class TestEncryptDecrypt:
    def test_round_trip(self):
        """Encrypt then decrypt should return original."""
        original = "my_secret_password"
        encrypted = encrypt(original)
        assert decrypt(encrypted) == original

    def test_encrypted_has_prefix(self):
        enc = encrypt("test")
        assert enc.startswith(_ENCRYPTED_PREFIX)

    def test_is_encrypted_true(self):
        enc = encrypt("hello")
        assert is_encrypted(enc) is True

    def test_is_encrypted_false_plaintext(self):
        assert is_encrypted("plaintext") is False

    def test_is_encrypted_false_empty(self):
        assert is_encrypted("") is False
        assert is_encrypted(None) is False

    def test_decrypt_plaintext_passthrough(self):
        """Plaintext values (no prefix) should pass through for migration."""
        assert decrypt("plain_password") == "plain_password"

    def test_encrypt_empty_string(self):
        assert encrypt("") == ""

    def test_encrypt_none(self):
        assert encrypt(None) is None

    def test_decrypt_empty_string(self):
        assert decrypt("") == ""

    def test_decrypt_none(self):
        assert decrypt(None) is None

    def test_different_encryptions_differ(self):
        """Same plaintext encrypted twice should produce different ciphertexts (Fernet uses random IV)."""
        a = encrypt("same_value")
        b = encrypt("same_value")
        assert a != b  # Different tokens due to timestamp/IV

    def test_unicode_roundtrip(self):
        original = "pässwörd_with_üñíçödé"
        assert decrypt(encrypt(original)) == original

    def test_long_value(self):
        original = "x" * 10_000
        assert decrypt(encrypt(original)) == original

    def test_special_characters(self):
        original = "p@$$w0rd!#%^&*(){}[]|\\:\";<>?/~`"
        assert decrypt(encrypt(original)) == original


class TestKeyManagement:
    def test_key_file_created(self):
        """Encrypting should create the key file."""
        encrypt("trigger_key_creation")
        assert os.path.exists(_key_path())

    def test_key_file_permissions(self):
        """Key file should have restricted permissions (0o600)."""
        encrypt("trigger")
        path = _key_path()
        mode = os.stat(path).st_mode & 0o777
        assert mode == 0o600

    def test_key_persistence(self):
        """Same key should be used across calls."""
        enc1 = encrypt("test_value")
        # Reset in-memory cache to force re-read from file
        crypto._fernet = None
        assert decrypt(enc1) == "test_value"

    def test_wrong_key_fails(self):
        """Decrypting with a different key should fail."""
        enc = encrypt("secret")

        # Overwrite the key file with a new key
        from cryptography.fernet import Fernet
        new_key = Fernet.generate_key()
        with open(_key_path(), "wb") as f:
            f.write(new_key)
        crypto._fernet = None  # Force reload

        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(enc)
