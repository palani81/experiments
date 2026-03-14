"""Session listing, detail, and reply endpoints."""

import asyncio
import os

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from config import settings
from models import Card, CardStatus, CreateSessionRequest, ReplyRequest
from services.cloud_poller import CloudPoller
from services.session_monitor import SessionMonitor
from services.session_input import send_reply_to_session, start_new_session_background
from storage import storage

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


@router.post("")
async def create_session(body: CreateSessionRequest, authorization: str = Header(default="")):
    """Start a new Claude Code session in the given project directory."""
    verify_token(authorization)

    project_path = os.path.expanduser(body.project_path)
    if not os.path.isdir(project_path):
        raise HTTPException(status_code=400, detail=f"Directory not found: {body.project_path}")

    try:
        await start_new_session_background(project_path, body.prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Auto-create a card for this session if a title was provided
    if body.title:
        card = Card(
            title=body.title,
            status=CardStatus.IN_PROGRESS,
            project_path=body.project_path,
        )
        storage.create_card(card)

    return {"status": "started", "project_path": body.project_path}


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
