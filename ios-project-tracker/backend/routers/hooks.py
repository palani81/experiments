"""Webhook receiver endpoints for Claude Code hooks.

Supports two input formats:
1. Native Claude Code hook format (HTTP hooks POST directly from Claude Code)
   - Fields: session_id, cwd, hook_event_name, transcript_path, etc.
2. Legacy format (shell scripts that curl our backend)
   - Fields: event_type, session_id, project_path, payload
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Request

from log_config import get_logger
from models import Card, CardSource, CardStatus, HookEvent, HookEventType
from storage import storage
from services.notifications import send_notification
from routers.websocket_router import broadcast

log = get_logger("hooks")

router = APIRouter()


def _parse_hook_input(data: dict[str, Any], event_type: str) -> HookEvent:
    """Parse native Claude Code hook input into our HookEvent model.

    Native format has: session_id, cwd, hook_event_name, transcript_path,
    permission_mode, plus event-specific fields.
    Legacy format has: event_type, session_id, project_path, payload.
    """
    # Detect format: native has 'hook_event_name' or 'cwd', legacy has 'event_type'
    if "hook_event_name" in data or ("cwd" in data and "event_type" not in data):
        # Native Claude Code format
        session_id = data.get("session_id", "")
        project_path = data.get("cwd", "")

        # Build payload from event-specific fields
        payload: dict[str, Any] = {}
        for key in ("last_assistant_message", "message", "title",
                     "notification_type", "reason", "source", "model",
                     "stop_hook_active", "prompt", "transcript_path"):
            if key in data:
                payload[key] = data[key]

        return HookEvent(
            event_type=event_type,
            session_id=session_id,
            project_path=project_path,
            payload=payload,
        )
    else:
        # Legacy format — pass through
        return HookEvent(
            event_type=data.get("event_type", event_type),
            session_id=data.get("session_id", ""),
            project_path=data.get("project_path", ""),
            payload=data.get("payload", {}),
        )


async def _handle_hook(event: HookEvent):
    """Process a hook event: update session state, broadcast, notify."""
    log.info(
        f"Hook received: {event.event_type.value} "
        f"session={event.session_id[:12] if event.session_id else '?'} "
        f"project={event.project_path}"
    )

    # Broadcast session update to connected WebSocket clients
    await broadcast("session_updated", {
        "session_id": event.session_id,
        "event_type": event.event_type.value,
        "project_path": event.project_path,
    })

    card = storage.get_card_by_session(event.session_id)

    if event.event_type == HookEventType.SESSION_START:
        if not card:
            title = event.payload.get("title", f"Session {event.session_id[:8]}")
            project = event.payload.get("project_path", event.project_path)
            card = Card(
                title=title,
                status=CardStatus.IN_PROGRESS,
                session_id=event.session_id,
                project_path=project,
                source=CardSource.LOCAL,
            )
            storage.create_card(card)
            log.info(f"Auto-created card '{title}' for session {event.session_id[:12]}")
            await broadcast("card_created", card.model_dump(mode="json"))
        else:
            storage.update_card(card.id, status=CardStatus.IN_PROGRESS)
            card = storage.get_card(card.id)
            log.info(f"Resumed card '{card.title}' -> in_progress")
            await broadcast("card_updated", card.model_dump(mode="json"))

    elif event.event_type == HookEventType.STOP:
        if card:
            storage.update_card(card.id, status=CardStatus.WAITING)
            card = storage.get_card(card.id)
            stop_reason = event.payload.get("reason", "stopped")
            log.info(f"Session stopped: '{card.title}' -> waiting (reason={stop_reason})")
            await broadcast("card_updated", card.model_dump(mode="json"))
            await send_notification(
                title=f"Claude needs input: {card.title}",
                message=f"Session stopped ({stop_reason}). Open the app to respond.",
                priority=1,
            )
        else:
            log.warning(f"Stop hook for unknown session {event.session_id[:12]} — no card found")
            # Still notify — session may not have a card yet
            await send_notification(
                title="Claude needs input",
                message=f"Session {event.session_id[:8]} stopped in {event.project_path}",
                priority=1,
            )

    elif event.event_type == HookEventType.PROMPT_SUBMIT:
        if card:
            storage.update_card(card.id, status=CardStatus.IN_PROGRESS)
            card = storage.get_card(card.id)
            log.info(f"Prompt submitted: '{card.title}' -> in_progress")
            await broadcast("card_updated", card.model_dump(mode="json"))

    elif event.event_type == HookEventType.SESSION_END:
        if card:
            pr_url = event.payload.get("pr_url")
            if pr_url:
                storage.update_card(
                    card.id, status=CardStatus.IN_REVIEW, pr_url=pr_url
                )
                log.info(f"Session ended with PR: '{card.title}' -> in_review ({pr_url})")
                await send_notification(
                    title=f"PR ready: {card.title}",
                    message=f"Pull request opened: {pr_url}",
                )
            else:
                storage.update_card(card.id, status=CardStatus.DONE)
                log.info(f"Session ended: '{card.title}' -> done")
                await send_notification(
                    title=f"Completed: {card.title}",
                    message="Task finished.",
                    priority=-1,
                )
            card = storage.get_card(card.id)
            await broadcast("card_updated", card.model_dump(mode="json"))

    elif event.event_type == HookEventType.NOTIFICATION:
        message = event.payload.get("message", "Notification from Claude")
        notification_type = event.payload.get("notification_type", "")
        log.info(f"Notification hook: session={event.session_id[:12]} type={notification_type} — {message}")
        await send_notification(
            title=f"Claude: {notification_type or 'alert'}",
            message=message,
            priority=1 if notification_type == "permission_prompt" else 0,
        )

    return {"status": "ok", "card_id": card.id if card else None}


@router.post("/stop")
async def hook_stop(request: Request):
    data = await request.json()
    log.info(f"POST /hooks/stop — raw keys: {list(data.keys())}")
    event = _parse_hook_input(data, "stop")
    return await _handle_hook(event)


@router.post("/session-start")
async def hook_session_start(request: Request):
    data = await request.json()
    log.info(f"POST /hooks/session-start — raw keys: {list(data.keys())}")
    event = _parse_hook_input(data, "session_start")
    return await _handle_hook(event)


@router.post("/session-end")
async def hook_session_end(request: Request):
    data = await request.json()
    log.info(f"POST /hooks/session-end — raw keys: {list(data.keys())}")
    event = _parse_hook_input(data, "session_end")
    return await _handle_hook(event)


@router.post("/notification")
async def hook_notification(request: Request):
    data = await request.json()
    log.info(f"POST /hooks/notification — raw keys: {list(data.keys())}")
    event = _parse_hook_input(data, "notification")
    return await _handle_hook(event)


@router.post("/prompt-submit")
async def hook_prompt_submit(request: Request):
    data = await request.json()
    log.info(f"POST /hooks/prompt-submit — raw keys: {list(data.keys())}")
    event = _parse_hook_input(data, "prompt_submit")
    return await _handle_hook(event)
