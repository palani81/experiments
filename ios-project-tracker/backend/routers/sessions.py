"""Session listing, detail, and reply endpoints."""

import asyncio
import os
import re

from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from config import settings
from models import Card, CardStatus, CreateSessionRequest, ReplyRequest
from services.cloud_poller import CloudPoller
from services.session_monitor import SessionMonitor
from services.session_input import send_reply_to_session, start_new_session_background
from storage import storage

# Default base directory for auto-created session projects
SESSIONS_BASE_DIR = Path.home() / "claude-sessions"

router = APIRouter()
monitor = SessionMonitor()
cloud_poller = CloudPoller()


def verify_token(authorization: str = Header()):
    token = authorization.replace("Bearer ", "")
    if token != settings.auth_token:
        raise HTTPException(status_code=401, detail="Invalid auth token")


@router.get("")
async def list_sessions(authorization: str = Header(default="")):
    """List all discovered Claude Code sessions (local + cloud)."""
    verify_token(authorization)
    local_sessions = monitor.get_sessions()
    cloud_sessions = cloud_poller.get_cloud_sessions()
    all_sessions = local_sessions + cloud_sessions
    return {"sessions": [s.model_dump(mode="json") for s in all_sessions]}


@router.get("/{session_id}")
async def get_session(session_id: str, authorization: str = Header(default="")):
    """Get a single session with conversation history."""
    verify_token(authorization)
    all_sessions = monitor.get_sessions() + cloud_poller.get_cloud_sessions()
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

    # Determine project path — auto-create under ~/claude-sessions/ if not provided
    if body.project_path.strip():
        project_path = os.path.expanduser(body.project_path)
    else:
        slug = _slugify(name)
        project_path = str(SESSIONS_BASE_DIR / slug)

    # Create directory if it doesn't exist
    os.makedirs(project_path, exist_ok=True)

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
    success = await send_reply_to_session(session_id, body.message)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send reply")
    return {"status": "sent", "session_id": session_id}
