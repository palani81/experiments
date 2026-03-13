"""Webhook receiver endpoints for Claude Code hooks."""

from datetime import datetime, timezone

from fastapi import APIRouter

from models import Card, CardSource, CardStatus, HookEvent, HookEventType
from storage import storage
from services.notifications import send_notification
from routers.websocket_router import broadcast

router = APIRouter()


async def _handle_hook(event: HookEvent):
    """Process a hook event and update card state accordingly."""
    card = storage.get_card_by_session(event.session_id)

    if event.event_type == HookEventType.SESSION_START:
        if not card:
            # Auto-create a card for new sessions
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
            await broadcast("card_created", card.model_dump(mode="json"))
        else:
            storage.update_card(card.id, status=CardStatus.IN_PROGRESS)
            card = storage.get_card(card.id)
            await broadcast("card_updated", card.model_dump(mode="json"))

    elif event.event_type == HookEventType.STOP:
        if card:
            storage.update_card(card.id, status=CardStatus.WAITING)
            card = storage.get_card(card.id)
            await broadcast("card_updated", card.model_dump(mode="json"))
            stop_reason = event.payload.get("reason", "stopped")
            await send_notification(
                title=f"Claude needs input: {card.title}",
                message=f"Session stopped ({stop_reason}). Open the app to respond.",
                priority=1,
            )

    elif event.event_type == HookEventType.PROMPT_SUBMIT:
        if card:
            storage.update_card(card.id, status=CardStatus.IN_PROGRESS)
            card = storage.get_card(card.id)
            await broadcast("card_updated", card.model_dump(mode="json"))

    elif event.event_type == HookEventType.SESSION_END:
        if card:
            # Check if there's a PR associated
            pr_url = event.payload.get("pr_url")
            if pr_url:
                storage.update_card(
                    card.id, status=CardStatus.IN_REVIEW, pr_url=pr_url
                )
                await send_notification(
                    title=f"PR ready: {card.title}",
                    message=f"Pull request opened: {pr_url}",
                )
            else:
                storage.update_card(card.id, status=CardStatus.DONE)
                await send_notification(
                    title=f"Completed: {card.title}",
                    message="Task finished.",
                    priority=-1,
                )
            card = storage.get_card(card.id)
            await broadcast("card_updated", card.model_dump(mode="json"))

    elif event.event_type == HookEventType.NOTIFICATION:
        if card:
            message = event.payload.get("message", "Notification from Claude")
            await send_notification(
                title=f"Alert: {card.title}",
                message=message,
                priority=1,
            )

    return {"status": "ok", "card_id": card.id if card else None}


@router.post("/stop")
async def hook_stop(event: HookEvent):
    event.event_type = HookEventType.STOP
    return await _handle_hook(event)


@router.post("/session-start")
async def hook_session_start(event: HookEvent):
    event.event_type = HookEventType.SESSION_START
    return await _handle_hook(event)


@router.post("/session-end")
async def hook_session_end(event: HookEvent):
    event.event_type = HookEventType.SESSION_END
    return await _handle_hook(event)


@router.post("/notification")
async def hook_notification(event: HookEvent):
    event.event_type = HookEventType.NOTIFICATION
    return await _handle_hook(event)


@router.post("/prompt-submit")
async def hook_prompt_submit(event: HookEvent):
    event.event_type = HookEventType.PROMPT_SUBMIT
    return await _handle_hook(event)
