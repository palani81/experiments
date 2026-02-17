"""Tests for NAS connection manager (config persistence, encryption, source management)."""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from app.nas_manager import (
    save_config, load_config, add_source, remove_source,
    get_sources, _config_path,
)
from app.crypto import is_encrypted, _ENCRYPTED_PREFIX


class TestConfigPersistence:
    def test_save_and_load(self):
        config = {
            "sources": [{
                "host": "192.168.1.100",
                "share": "media",
                "username": "admin",
                "password": "secret123",
                "subfolder": "/",
                "label": "media",
            }]
        }
        save_config(config)
        loaded = load_config()
        assert loaded is not None
        assert len(loaded["sources"]) == 1
        assert loaded["sources"][0]["host"] == "192.168.1.100"
        # Credentials should be decrypted on load
        assert loaded["sources"][0]["username"] == "admin"
        assert loaded["sources"][0]["password"] == "secret123"

    def test_credentials_encrypted_on_disk(self):
        config = {
            "sources": [{
                "host": "10.0.0.1",
                "share": "data",
                "username": "user",
                "password": "pass",
                "subfolder": "/",
                "label": "data",
            }]
        }
        save_config(config)

        # Read raw JSON from disk
        with open(_config_path(), "r") as f:
            raw = json.load(f)

        src = raw["sources"][0]
        assert is_encrypted(src["username"]), "Username should be encrypted on disk"
        assert is_encrypted(src["password"]), "Password should be encrypted on disk"
        assert src["host"] == "10.0.0.1"  # Host should NOT be encrypted

    def test_auto_migration_plaintext(self):
        """If config has plaintext credentials, loading should auto-encrypt them."""
        config_path = _config_path()
        raw = {
            "sources": [{
                "host": "nas.local",
                "share": "files",
                "username": "plainuser",
                "password": "plainpass",
                "subfolder": "/",
                "label": "files",
            }]
        }
        # Write plaintext directly
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(raw, f)

        # Loading should detect plaintext and re-save encrypted
        loaded = load_config()
        assert loaded["sources"][0]["username"] == "plainuser"
        assert loaded["sources"][0]["password"] == "plainpass"

        # Verify re-saved file is now encrypted
        with open(config_path, "r") as f:
            raw2 = json.load(f)
        assert is_encrypted(raw2["sources"][0]["username"])
        assert is_encrypted(raw2["sources"][0]["password"])

    def test_load_missing_config(self):
        assert load_config() is None

    def test_save_multiple_sources(self):
        config = {
            "sources": [
                {"host": "nas", "share": "s1", "username": "u1", "password": "p1", "subfolder": "/", "label": "s1"},
                {"host": "nas", "share": "s2", "username": "u2", "password": "p2", "subfolder": "/", "label": "s2"},
            ]
        }
        save_config(config)
        loaded = load_config()
        assert len(loaded["sources"]) == 2

    def test_already_encrypted_not_double_encrypted(self):
        """Saving already-encrypted values should not double-encrypt."""
        config = {
            "sources": [{
                "host": "nas", "share": "s",
                "username": _ENCRYPTED_PREFIX + "already_encrypted_token",
                "password": "plaintext",
                "subfolder": "/", "label": "s",
            }]
        }
        save_config(config)
        with open(_config_path(), "r") as f:
            raw = json.load(f)
        # Username was already "encrypted" (has prefix), password was plain -> should be encrypted
        assert raw["sources"][0]["username"] == _ENCRYPTED_PREFIX + "already_encrypted_token"
        assert is_encrypted(raw["sources"][0]["password"])


class TestSourceManagement:
    @patch("app.nas_manager.register_source")
    @patch("app.nas_manager.test_connection", return_value={"success": True})
    def test_add_source(self, mock_test, mock_register):
        result = add_source("nas", "photos", "user", "pass")
        assert result["success"] is True
        assert "source_id" in result

        sources = get_sources()
        assert len(sources) == 1
        assert sources[0].share == "photos"

    @patch("app.nas_manager.register_source")
    def test_add_duplicate_source(self, mock_register):
        # Add first
        add_source("nas", "media", "user", "pass")
        # Try duplicate
        result = add_source("nas", "media", "user", "pass")
        assert result["success"] is False
        assert "already exists" in result["message"]

    @patch("app.nas_manager.register_source")
    def test_remove_source(self, mock_register):
        add_source("nas", "media", "user", "pass", label="media")
        add_source("nas", "photos", "user", "pass", label="photos")

        result = remove_source("nas/media")
        assert result["success"] is True
        sources = get_sources()
        assert len(sources) == 1
        assert sources[0].share == "photos"

    def test_remove_nonexistent_source(self):
        # Save an empty config first
        save_config({"sources": []})
        result = remove_source("nonexistent/source")
        assert result["success"] is False

    @patch("app.nas_manager.register_source")
    def test_remove_source_purges_db(self, mock_register, db_conn):
        """Removing a source should delete its files, tags, and metadata from DB."""
        from app.database import execute, query

        # Add source and fake some indexed files
        add_source("nas", "media", "user", "pass", label="media")
        fid = execute(
            "INSERT INTO files (path, name, is_directory, size) VALUES (?, ?, ?, ?)",
            ("/media/movie.mp4", "movie.mp4", 0, 5000)
        )
        execute("INSERT INTO file_tags (file_id, tag) VALUES (?, ?)", (fid, "video"))
        execute("INSERT INTO file_metadata (file_id, metadata) VALUES (?, ?)", (fid, '{"duration":120}'))

        # Verify data exists
        assert len(query("SELECT * FROM files WHERE path LIKE '/media/%'")) == 1
        assert len(query("SELECT * FROM file_tags WHERE file_id = ?", (fid,))) == 1

        # Remove source
        result = remove_source("nas/media")
        assert result["success"] is True
        assert result["purged_files"] >= 1

        # Verify all data purged
        assert len(query("SELECT * FROM files WHERE path LIKE '/media/%'")) == 0
        assert len(query("SELECT * FROM file_tags WHERE file_id = ?", (fid,))) == 0
        assert len(query("SELECT * FROM file_metadata WHERE file_id = ?", (fid,))) == 0

    def test_get_sources_empty(self):
        sources = get_sources()
        assert sources == []

    @patch("app.nas_manager.register_source")
    def test_get_sources_returns_smb_sources(self, mock_register):
        add_source("nas", "data", "u", "p", label="data")
        sources = get_sources()
        assert len(sources) == 1
        from app.smb_fs import SMBSource
        assert isinstance(sources[0], SMBSource)
        assert sources[0].host == "nas"
        assert sources[0].share == "data"


class TestConnectionStatus:
    @patch("app.nas_manager.test_connection", return_value={"success": False, "message": "unreachable"})
    @patch("app.nas_manager.register_source")
    def test_status_disconnected(self, mock_register, mock_test):
        from app.nas_manager import get_connection_status
        add_source("nas", "media", "u", "p", label="media")
        status = get_connection_status()
        assert status["configured"] is True
        assert status["connected"] is False

    def test_status_not_configured(self):
        from app.nas_manager import get_connection_status
        status = get_connection_status()
        assert status["configured"] is False
        assert status["connected"] is False
        assert status["sources"] == []
