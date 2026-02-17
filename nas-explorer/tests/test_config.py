"""Tests for application configuration."""

import pytest
from app.config import Settings, settings


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.host == "0.0.0.0"
        assert s.port == 8000
        assert s.scan_batch_size == 1000
        assert s.enrichment_workers == 4
        assert s.max_text_extract_mb == 100
        assert s.max_text_store_kb == 50
        assert s.hash_sample_size_kb == 64
        assert s.auth_token == "change-me-to-a-secure-token"

    def test_ensure_dirs(self, tmp_path):
        s = Settings()
        s.database_path = str(tmp_path / "data" / "test.db")
        s.cache_path = str(tmp_path / "cache" / "previews")
        s.ensure_dirs()
        assert (tmp_path / "data").exists()
        assert (tmp_path / "cache" / "previews").exists()

    def test_ssl_defaults_none(self):
        s = Settings()
        assert s.ssl_cert_path is None
        assert s.ssl_key_path is None

    def test_global_settings_instance(self):
        """The global `settings` should be a Settings instance."""
        assert isinstance(settings, Settings)
        assert hasattr(settings, "enrichment_workers")
