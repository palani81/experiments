"""Polls claude.ai/code cloud-hosted project status."""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from models import CardSource, Session


class CloudPoller:
    """Polls for cloud-hosted Claude Code session status.

    Cloud sessions are manually registered by the user via the mobile app.
    This service periodically checks their status.
    """

    def __init__(self):
        self._cloud_sessions: dict[str, dict] = {}
        self._config_path = Path(settings.tracker_data_dir) / "cloud_sessions.json"
        self._load()

    def _load(self):
        if self._config_path.exists():
            with open(self._config_path) as f:
                self._cloud_sessions = json.load(f)

    def _save(self):
        with open(self._config_path, "w") as f:
            json.dump(self._cloud_sessions, f, indent=2)

    def add_cloud_session(self, session_id: str, url: str = "", title: str = ""):
        """Register a cloud session for tracking."""
        self._cloud_sessions[session_id] = {
            "url": url,
            "title": title or f"Cloud: {session_id[:8]}",
            "added_at": datetime.now(timezone.utc).isoformat(),
            "last_status": "unknown",
        }
        self._save()

    def remove_cloud_session(self, session_id: str):
        """Stop tracking a cloud session."""
        self._cloud_sessions.pop(session_id, None)
        self._save()

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
        """Poll cloud sessions for status updates.

        Note: This is a placeholder for when Claude Code provides a proper API
        for querying cloud session status. Currently, cloud sessions are
        manually managed by the user.
        """
        # Future: Use Claude Code API to poll session status
        # For now, cloud sessions are manually updated
        pass

    async def run(self):
        """Background task: poll cloud sessions periodically."""
        while True:
            try:
                await self.poll()
            except Exception:
                pass
            await asyncio.sleep(settings.cloud_poll_interval_seconds)
