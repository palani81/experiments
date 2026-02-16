"""Configuration management for NAS Explorer."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # NAS mount path
    nas_mount_path: str = "/mnt/nas"

    # Auth
    auth_token: str = "change-me-to-a-secure-token"

    # Database
    database_path: str = "./data/nas_explorer.db"

    # Cache
    cache_path: str = "./cache/previews"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Scanning
    scan_batch_size: int = 1000
    max_text_extract_mb: int = 100
    max_text_store_kb: int = 50
    hash_sample_size_kb: int = 64

    # SSL (optional)
    ssl_cert_path: str | None = None
    ssl_key_path: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def ensure_dirs(self):
        """Create required directories."""
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.cache_path).mkdir(parents=True, exist_ok=True)


settings = Settings()
