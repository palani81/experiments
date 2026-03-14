"""Session listing, detail, and reply endpoints."""

from __future__ import annotations

import asyncio
import os
import re

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel

from config import settings
from log_config import get_logger
from models import Card, CardStatus, CreateSessionRequest, ReplyRequest
from services.cloud_poller import cloud_poller
from services.session_monitor import session_monitor
from services.session_input import send_reply_to_session, start_new_session_background
from storage import storage

log = get_logger("sessions_api")

# Default base directory for auto-created session projects
SESSIONS_BASE_DIR = Path.home() / "claude-sessions"

router = APIRouter()


def verify_token(authorization: str = Header()):
    token = authorization.replace("Bearer ", "")
    if token != settings.auth_token:
        raise HTTPException(status_code=401, detail="Invalid auth token")


@router.get("")
async def list_sessions(
    authorization: str = Header(default=""),
    days: int = Query(default=7, description="Only return sessions active within the last N days. Use 0 for all."),
):
    """List all discovered Claude Code sessions (local + cloud)."""
    verify_token(authorization)
    local_sessions = session_monitor.get_sessions()
    cloud_sessions = cloud_poller.get_cloud_sessions()
    all_sessions = local_sessions + cloud_sessions

    if days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        all_sessions = [s for s in all_sessions if s.last_activity >= cutoff]

    log.info(f"List sessions: {len(all_sessions)} (filtered to last {days} days)")
    return {"sessions": [s.model_dump(mode="json") for s in all_sessions]}


@router.get("/{session_id}")
async def get_session(session_id: str, authorization: str = Header(default="")):
    """Get a single session with conversation history."""
    verify_token(authorization)
    all_sessions = session_monitor.get_sessions() + cloud_poller.get_cloud_sessions()
    for s in all_sessions:
        if s.id == session_id:
            return s.model_dump(mode="json")
    raise HTTPException(status_code=404, detail="Session not found")


def _slugify(name: str) -> str:
    """Convert a session name to a filesystem-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", name.lower().strip())
    slug = re.sub(r"[\s]+", "-", slug)
    return slug[:60] or "session"


@router.post("")
async def create_session(body: CreateSessionRequest, authorization: str = Header(default="")):
    """Start a new Claude Code session. Only a name is required — everything else is auto-created."""
    verify_token(authorization)

    # Determine session name (fall back to title for backwards compat)
    name = body.name.strip() or body.title.strip() or "New Session"
    log.info(f"Create session request: name='{name}', path='{body.project_path}', prompt='{body.prompt[:80] if body.prompt else ''}'")


    # Determine project path — auto-create under ~/claude-sessions/ if not provided
    if body.project_path.strip():
        project_path = os.path.expanduser(body.project_path)
    else:
        slug = _slugify(name)
        project_path = str(SESSIONS_BASE_DIR / slug)

    # Create directory if it doesn't exist
    log.info(f"Using project path: {project_path}")
    os.makedirs(project_path, exist_ok=True)
    log.info(f"Directory ensured: {project_path}")

    # Determine prompt — use the name as context if not provided
    prompt = body.prompt.strip() if body.prompt.strip() else f"Work on: {name}"

    try:
        await start_new_session_background(project_path, prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "started", "project_path": project_path, "name": name}


class AddCloudSessionRequest(BaseModel):
    session_id: str
    url: str = ""
    title: str = ""


@router.post("/cloud")
async def add_cloud_session(body: AddCloudSessionRequest, authorization: str = Header(default="")):
    """Register a Claude Code cloud session for tracking."""
    verify_token(authorization)
    log.info(f"Adding cloud session: {body.session_id} title='{body.title}' url='{body.url}'")
    cloud_poller.add_cloud_session(body.session_id, url=body.url, title=body.title)
    return {"status": "added", "session_id": body.session_id}


@router.delete("/cloud/{session_id}")
async def remove_cloud_session(session_id: str, authorization: str = Header(default="")):
    """Stop tracking a cloud session."""
    verify_token(authorization)
    cloud_poller.remove_cloud_session(session_id)
    return {"status": "removed", "session_id": session_id}


@router.post("/{session_id}/reply")
async def reply_to_session(
    session_id: str, body: ReplyRequest, authorization: str = Header(default="")
):
    """Send a reply message to an active Claude Code session."""
    verify_token(authorization)
    try:
        success = await send_reply_to_session(session_id, body.message)
    except Exception as e:
        log.error(f"Reply to {session_id[:12]} raised: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Reply failed: {e}",
        )
    if not success:
        raise HTTPException(
            status_code=422,
            detail="Could not deliver reply — session may no longer be active. "
                   "Both CLI resume and tmux fallback failed.",
        )
    return {"status": "sent", "session_id": session_id}
