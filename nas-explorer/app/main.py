"""NAS Explorer — FastAPI application entry point."""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("nas_explorer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting NAS Explorer...")
    settings.ensure_dirs()
    init_db()

    # Initialize SMB temp directory
    from .smb_fs import init_temp_dir
    init_temp_dir(settings.cache_path)

    # Register any saved NAS sources
    from .nas_manager import register_all_sources, get_sources
    sources = get_sources()
    if sources:
        registered = register_all_sources()
        logger.info(f"Loaded {len(sources)} NAS sources ({registered} connected)")
    else:
        logger.info("No NAS sources configured yet. Use the setup wizard at /")

    yield

    # Shutdown
    from .smb_fs import cleanup_all_temps
    cleanup_all_temps()
    logger.info("NAS Explorer shutting down.")


app = FastAPI(
    title="NAS Explorer",
    description="Secure, read-only file explorer and intelligence tool for your NAS",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS (allow LAN access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from .routes.files import router as files_router
from .routes.search import router as search_router
from .routes.preview import router as preview_router
from .routes.dashboard import router as dashboard_router
from .routes.admin import router as admin_router
from .routes.setup import router as setup_router

app.include_router(files_router)
app.include_router(search_router)
app.include_router(preview_router)
app.include_router(dashboard_router)
app.include_router(admin_router)
app.include_router(setup_router)

# Serve static frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the single-page React frontend."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "NAS Explorer API is running. Frontend not found at /static/index.html"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
