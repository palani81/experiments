import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings.ensure_dirs()
    init_db()
    yield


app = FastAPI(title="Kindle Crossword", lifespan=lifespan)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

from app.routes.upload import router as upload_router
from app.routes.jobs import router as jobs_router
from app.routes.settings import router as settings_router

app.include_router(upload_router)
app.include_router(jobs_router)
app.include_router(settings_router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/")
async def root():
    index = STATIC_DIR / "index.html"
    if not index.is_file():
        return JSONResponse({"message": "Frontend not built yet"}, status_code=404)
    return FileResponse(index)
