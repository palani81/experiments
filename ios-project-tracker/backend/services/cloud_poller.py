"""Polls claude.ai/code cloud-hosted project status."""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from log_config import get_logger
from models import CardSource, Session

log = get_logger("cloud_poller")


class CloudPoller:
    """Polls for cloud-hosted Claude Code session status."""

    def __init__(self):
        self._cloud_sessions: dict[str, dict] = {}
        self._config_path = Path(settings.tracker_data_dir) / "cloud_sessions.json"
        self._load()

    def _load(self):
        if self._config_path.exists():
            try:
                with open(self._config_path) as f:
                    self._cloud_sessions = json.load(f)
                log.info(f"Loaded {len(self._cloud_sessions)} cloud sessions from disk")
            except Exception as e:
                log.error(f"Failed to load cloud sessions: {e}")

    def _save(self):
        try:
            with open(self._config_path, "w") as f:
                json.dump(self._cloud_sessions, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save cloud sessions: {e}")

    def add_cloud_session(self, session_id: str, url: str = "", title: str = ""):
        """Register a cloud session for tracking."""
        self._cloud_sessions[session_id] = {
            "url": url,
            "title": title or f"Cloud: {session_id[:8]}",
            "added_at": datetime.now(timezone.utc).isoformat(),
            "last_status": "unknown",
        }
        self._save()
        log.info(f"Added cloud session: {session_id[:12]} title='{title}'")

    def remove_cloud_session(self, session_id: str):
        """Stop tracking a cloud session."""
        removed = self._cloud_sessions.pop(session_id, None)
        self._save()
        if removed:
            log.info(f"Removed cloud session: {session_id[:12]}")
        else:
            log.warning(f"Cloud session not found for removal: {session_id[:12]}")

    def get_cloud_sessions(self) -> list[Session]:
        """Return all tracked cloud sessions as Session objects."""
        sessions = []
        for sid, info in self._cloud_sessions.items():
            sessions.append(Session(
                id=sid,
                project_path=info.get("url", ""),
                status=info.get("last_status", "unknown"),
                last_activity=datetime.fromisoformat(
                    info.get("added_at", datetime.now(timezone.utc).isoformat())
                ),
                source=CardSource.CLOUD,
            ))
        return sessions

    async def poll(self):
        """Poll cloud sessions for status updates (placeholder)."""
        pass

    async def run(self):
        """Background task: poll cloud sessions periodically."""
        log.info(f"Cloud poller started — {len(self._cloud_sessions)} sessions tracked")
        while True:
            try:
                await self.poll()
            except Exception as e:
                log.error(f"Cloud poll failed: {e}")
            await asyncio.sleep(settings.cloud_poll_interval_seconds)
