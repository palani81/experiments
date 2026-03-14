"""Core data models for the Claude Code Tracker."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from ksuid import Ksuid
from pydantic import BaseModel, Field


def generate_id() -> str:
    """Generate a time-sortable KSUID."""
    return str(Ksuid())


class CardStatus(str, Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    IN_REVIEW = "in_review"
    DONE = "done"


class CardSource(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"


class Card(BaseModel):
    id: str = Field(default_factory=generate_id)
    title: str
    status: CardStatus = CardStatus.BACKLOG
    session_id: Optional[str] = None
    branch: Optional[str] = None
    pr_url: Optional[str] = None
    project_path: Optional[str] = None
    source: CardSource = CardSource.LOCAL
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    conversation_summary: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CardCreate(BaseModel):
    title: str
    status: CardStatus = CardStatus.BACKLOG
    session_id: Optional[str] = None
    branch: Optional[str] = None
    pr_url: Optional[str] = None
    project_path: Optional[str] = None
    source: CardSource = CardSource.LOCAL


class CardUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[CardStatus] = None
    session_id: Optional[str] = None
    branch: Optional[str] = None
    pr_url: Optional[str] = None
    project_path: Optional[str] = None
    conversation_summary: Optional[str] = None


class HookEventType(str, Enum):
    STOP = "stop"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    NOTIFICATION = "notification"
    PROMPT_SUBMIT = "prompt_submit"


class HookEvent(BaseModel):
    event_type: HookEventType
    session_id: str
    project_path: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Session(BaseModel):
    id: str
    project_path: str
    status: str = "unknown"
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    conversation: list[dict[str, Any]] = Field(default_factory=list)
    source: CardSource = CardSource.LOCAL


class ReplyRequest(BaseModel):
    message: str


class CreateSessionRequest(BaseModel):
    project_path: str
    prompt: str
    title: str = ""


class WebSocketMessage(BaseModel):
    type: str  # card_updated, card_created, card_deleted, session_updated, hook_event
    data: dict[str, Any] = Field(default_factory=dict)
