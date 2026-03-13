"""Monitors ~/.claude/projects/ for Claude Code sessions."""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from models import CardSource, Session
from services.transcript import parse_transcript


class SessionMonitor:
    """Scans the Claude projects directory for active sessions."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._projects_dir = Path(settings.claude_projects_dir)

    def get_sessions(self) -> list[Session]:
        """Return all discovered sessions."""
        return list(self._sessions.values())

    def _scan_sessions(self):
        """Walk the projects directory to discover sessions."""
        if not self._projects_dir.exists():
            return

        for project_dir in self._projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            sessions_dir = project_dir / ".sessions"
            if not sessions_dir.exists():
                # Check for session files directly in project dir
                self._scan_project_dir(project_dir)
                continue
            for session_file in sessions_dir.glob("*.jsonl"):
                session_id = session_file.stem
                self._process_session_file(session_id, session_file, str(project_dir))

    def _scan_project_dir(self, project_dir: Path):
        """Scan a project directory for session-related files."""
        for jsonl_file in project_dir.glob("**/*.jsonl"):
            session_id = jsonl_file.stem
            self._process_session_file(session_id, jsonl_file, str(project_dir))

    def _process_session_file(self, session_id: str, file_path: Path, project_path: str):
        """Process a single session JSONL file."""
        try:
            stat = file_path.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

            # Only re-parse if file changed
            existing = self._sessions.get(session_id)
            if existing and existing.last_activity >= mtime:
                return

            conversation = parse_transcript(file_path)
            status = self._infer_status(conversation)

            self._sessions[session_id] = Session(
                id=session_id,
                project_path=project_path,
                status=status,
                last_activity=mtime,
                conversation=conversation,
                source=CardSource.LOCAL,
            )
        except Exception:
            pass  # Skip unparseable files

    def _infer_status(self, conversation: list[dict]) -> str:
        """Infer session status from the last conversation entry."""
        if not conversation:
            return "unknown"
        last = conversation[-1]
        role = last.get("role", "")
        if role == "assistant":
            return "waiting"  # Claude spoke last, may be waiting for input
        elif role == "user":
            return "active"
        return "unknown"

    async def run(self):
        """Background task: scan sessions periodically."""
        while True:
            try:
                self._scan_sessions()
            except Exception:
                pass
            await asyncio.sleep(settings.monitor_interval_seconds)
