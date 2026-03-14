"""Claude Code Tracker — FastAPI backend server."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import cards, hooks, sessions, websocket_router
from services.cloud_poller import CloudPoller
from services.session_monitor import SessionMonitor


monitor = SessionMonitor()
cloud_poller = CloudPoller()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks on startup, clean up on shutdown."""
    monitor_task = asyncio.create_task(monitor.run())
    cloud_task = asyncio.create_task(cloud_poller.run())
    yield
    monitor_task.cancel()
    cloud_task.cancel()
    for task in (monitor_task, cloud_task):
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Claude Code Tracker",
    description="Backend service for tracking Claude Code projects",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cards.router, prefix="/api/cards", tags=["cards"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(hooks.router, prefix="/hooks", tags=["hooks"])
app.include_router(websocket_router.router, tags=["websocket"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
