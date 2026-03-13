"""WebSocket endpoint for real-time updates."""

import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from config import settings

router = APIRouter()

# Connected WebSocket clients
_clients: set[WebSocket] = set()


async def broadcast(event_type: str, data: dict[str, Any]):
    """Broadcast a message to all connected WebSocket clients."""
    global _clients
    message = json.dumps({"type": event_type, "data": data}, default=str)
    disconnected = set()
    for ws in _clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)
    _clients -= disconnected


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(default="")):
    """WebSocket connection with token auth via query parameter."""
    if token != settings.auth_token:
        await ws.close(code=4001, reason="Unauthorized")
        return

    await ws.accept()
    _clients.add(ws)
    try:
        while True:
            # Keep connection alive, handle client messages if needed
            data = await ws.receive_text()
            # Client can send ping/pong or future commands
            if data == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        _clients.discard(ws)
    except Exception:
        _clients.discard(ws)
