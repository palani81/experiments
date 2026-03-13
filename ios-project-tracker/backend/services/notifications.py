"""Pushover notification service."""

import time

import httpx

from config import settings

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

# Simple deduplication: track last notification per title
_last_sent: dict[str, float] = {}
DEDUP_WINDOW_SECONDS = 30


async def send_notification(
    title: str,
    message: str,
    priority: int = 0,
    sound: str = "cosmic",
):
    """Send a push notification via Pushover.

    Args:
        title: Notification title
        message: Notification body
        priority: -2 (silent) to 2 (emergency). 1 = high priority.
        sound: Pushover sound name
    """
    if not settings.pushover_app_token or not settings.pushover_user_key:
        return  # Notifications not configured

    # Deduplication
    now = time.time()
    dedup_key = f"{title}:{message}"
    if dedup_key in _last_sent and (now - _last_sent[dedup_key]) < DEDUP_WINDOW_SECONDS:
        return
    _last_sent[dedup_key] = now

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                PUSHOVER_API_URL,
                data={
                    "token": settings.pushover_app_token,
                    "user": settings.pushover_user_key,
                    "title": title,
                    "message": message,
                    "priority": priority,
                    "sound": sound,
                },
                timeout=10,
            )
    except Exception:
        pass  # Don't crash the server if notifications fail
