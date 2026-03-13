"""Session listing, detail, and reply endpoints."""

import asyncio

from fastapi import APIRouter, Header, HTTPException

from config import settings
from models import ReplyRequest
from services.session_monitor import SessionMonitor
from services.session_input import send_reply_to_session

router = APIRouter()
monitor = SessionMonitor()


def verify_token(authorization: str = Header()):
    token = authorization.replace("Bearer ", "")
    if token != settings.auth_token:
        raise HTTPException(status_code=401, detail="Invalid auth token")


@router.get("")
async def list_sessions(authorization: str = Header(default="")):
    """List all discovered Claude Code sessions."""
    verify_token(authorization)
    sessions = monitor.get_sessions()
    return {"sessions": [s.model_dump(mode="json") for s in sessions]}


@router.get("/{session_id}")
async def get_session(session_id: str, authorization: str = Header(default="")):
    """Get a single session with conversation history."""
    verify_token(authorization)
    sessions = monitor.get_sessions()
    for s in sessions:
        if s.id == session_id:
            return s.model_dump(mode="json")
    raise HTTPException(status_code=404, detail="Session not found")


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
