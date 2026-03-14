"""Pushover notification service."""

from __future__ import annotations

import time

import httpx

from config import settings
from log_config import get_logger

log = get_logger("notifications")

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
    """Send a push notification via Pushover."""
    if not settings.pushover_app_token or not settings.pushover_user_key:
        log.info(f"Notification (not configured): {title} — {message}")
        return

    # Deduplication
    now = time.time()
    dedup_key = f"{title}:{message}"
    if dedup_key in _last_sent and (now - _last_sent[dedup_key]) < DEDUP_WINDOW_SECONDS:
        log.info(f"Notification deduplicated: {title}")
        return
    _last_sent[dedup_key] = now

    log.info(f"Sending notification: {title} — {message}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
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
            if resp.status_code == 200:
                log.info(f"Notification sent successfully: {title}")
            else:
                log.error(f"Notification failed (HTTP {resp.status_code}): {resp.text[:200]}")
    except Exception as e:
        log.error(f"Notification error: {e}")
