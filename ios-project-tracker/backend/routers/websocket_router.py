"""WebSocket endpoint for real-time updates."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from config import settings
from log_config import get_logger

log = get_logger("websocket")

router = APIRouter()

# Connected WebSocket clients
_clients: set[WebSocket] = set()


async def broadcast(event_type: str, data: dict[str, Any]):
    """Broadcast a message to all connected WebSocket clients."""
    global _clients
    if not _clients:
        return
    message = json.dumps({"type": event_type, "data": data}, default=str)
    disconnected = set()
    for ws in _clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)
    if disconnected:
        log.info(f"Removed {len(disconnected)} disconnected WebSocket clients")
    _clients -= disconnected
    log.info(f"Broadcast {event_type} to {len(_clients)} clients")


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(default="")):
    """WebSocket connection with token auth via query parameter."""
    if token != settings.auth_token:
        log.warning("WebSocket connection rejected: invalid token")
        await ws.close(code=4001, reason="Unauthorized")
        return

    await ws.accept()
    _clients.add(ws)
    log.info(f"WebSocket client connected ({len(_clients)} total)")
    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        _clients.discard(ws)
        log.info(f"WebSocket client disconnected ({len(_clients)} remaining)")
    except Exception as e:
        _clients.discard(ws)
        log.warning(f"WebSocket error: {e} ({len(_clients)} remaining)")
