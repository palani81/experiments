"""Monitors ~/.claude/projects/ for Claude Code sessions."""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from log_config import get_logger
from models import CardSource, Session
from services.transcript import parse_transcript

log = get_logger("monitor")


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
            log.warning(f"Projects dir does not exist: {self._projects_dir}")
            return

        found_count = 0
        for project_dir in self._projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            sessions_dir = project_dir / ".sessions"
            if not sessions_dir.exists():
                # Check for session files directly in project dir
                found_count += self._scan_project_dir(project_dir)
                continue
            for session_file in sessions_dir.glob("*.jsonl"):
                session_id = session_file.stem
                if self._process_session_file(session_id, session_file, str(project_dir)):
                    found_count += 1

        if found_count > 0:
            log.info(f"Scan complete: {found_count} new/updated sessions, {len(self._sessions)} total")

    def _scan_project_dir(self, project_dir: Path) -> int:
        """Scan a project directory for session-related files."""
        count = 0
        for jsonl_file in project_dir.glob("**/*.jsonl"):
            session_id = jsonl_file.stem
            if self._process_session_file(session_id, jsonl_file, str(project_dir)):
                count += 1
        return count

    def _process_session_file(self, session_id: str, file_path: Path, project_path: str) -> bool:
        """Process a single session JSONL file. Returns True if new/updated."""
        try:
            stat = file_path.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

            # Only re-parse if file changed
            existing = self._sessions.get(session_id)
            if existing and existing.last_activity >= mtime:
                return False

            conversation = parse_transcript(file_path)
            status = self._infer_status(conversation)

            is_new = session_id not in self._sessions
            self._sessions[session_id] = Session(
                id=session_id,
                project_path=project_path,
                status=status,
                last_activity=mtime,
                conversation=conversation,
                source=CardSource.LOCAL,
            )

            if is_new:
                log.info(f"Discovered session {session_id[:12]} in {project_path} (status={status}, {len(conversation)} messages)")
            else:
                log.info(f"Updated session {session_id[:12]} (status={status}, {len(conversation)} messages)")
            return True
        except Exception as e:
            log.error(f"Failed to process session file {file_path}: {e}")
            return False

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
        log.info(f"Session monitor started — scanning {self._projects_dir} every {settings.monitor_interval_seconds}s")
        while True:
            try:
                self._scan_sessions()
            except Exception as e:
                log.error(f"Session scan failed: {e}")
            await asyncio.sleep(settings.monitor_interval_seconds)
