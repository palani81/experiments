"""Claude Code Tracker — FastAPI backend server."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, Query
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from log_config import setup_logging, get_logger, ring_handler
from routers import cards, hooks, sessions, websocket_router
from services.cloud_poller import CloudPoller
from services.session_monitor import SessionMonitor

# Initialize logging BEFORE anything else
setup_logging()
log = get_logger("main")

monitor = SessionMonitor()
cloud_poller = CloudPoller()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks on startup, clean up on shutdown."""
    log.info("Starting Claude Code Tracker backend v1.0.0")
    log.info(f"Projects dir: {settings.claude_projects_dir}")
    log.info(f"Data dir: {settings.tracker_data_dir}")
    log.info(f"Monitor interval: {settings.monitor_interval_seconds}s")
    log.info(f"Pushover configured: {bool(settings.pushover_app_token)}")

    monitor_task = asyncio.create_task(monitor.run())
    cloud_task = asyncio.create_task(cloud_poller.run())
    log.info("Background tasks started (session monitor + cloud poller)")
    yield
    log.info("Shutting down background tasks")
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
    session_count = len(monitor.get_sessions()) + len(cloud_poller.get_cloud_sessions())
    return {
        "status": "ok",
        "version": "1.0.0",
        "sessions": session_count,
        "projects_dir": settings.claude_projects_dir,
    }


@app.get("/api/logs")
async def get_logs(
    authorization: str = Header(default=""),
    limit: int = Query(default=100, le=500),
    level: str = Query(default=""),
):
    """Return recent server logs. Visible from the mobile app."""
    token = authorization.replace("Bearer ", "")
    if token != settings.auth_token:
        return {"logs": [], "error": "unauthorized"}
    logs = ring_handler.get_logs(limit=limit, level=level or None)
    return {"logs": logs}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
