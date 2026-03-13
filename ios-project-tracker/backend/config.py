"""Application configuration loaded from environment or config file."""

import json
import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8420
    auth_token: str = "changeme"

    # Paths
    claude_projects_dir: str = str(Path.home() / ".claude" / "projects")
    tracker_data_dir: str = str(Path.home() / ".claude-tracker")

    # Pushover notifications
    pushover_app_token: str = ""
    pushover_user_key: str = ""

    # Session monitoring
    monitor_interval_seconds: int = 30

    # Cloud polling
    cloud_poll_interval_seconds: int = 60

    model_config = {"env_prefix": "TRACKER_", "env_file": ".env"}


def get_settings() -> Settings:
    """Load settings, merging config file with environment overrides."""
    config_path = Path(Settings().tracker_data_dir) / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            file_config = json.load(f)
        return Settings(**file_config)
    return Settings()


settings = get_settings()

# Ensure data directory exists
os.makedirs(settings.tracker_data_dir, exist_ok=True)
