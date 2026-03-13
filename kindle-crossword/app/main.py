import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.auth import (
    LOGIN_PAGE,
    TOKEN_COOKIE,
    TOKEN_MAX_AGE,
    AuthMiddleware,
    _make_token,
    verify_password,
)
from app.config import settings
from app.database import init_db

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings.ensure_dirs()
    init_db()
    if settings.app_password:
        logger.info("Authentication enabled")
    else:
        logger.warning("No APP_PASSWORD set — running without authentication")
    yield


app = FastAPI(title="Kindle Crossword", lifespan=lifespan)
app.add_middleware(AuthMiddleware)

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


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    if not settings.app_password:
        return RedirectResponse("/", status_code=303)
    return HTMLResponse(LOGIN_PAGE.replace("{error}", ""))


@app.post("/login")
async def login(password: str = Form(...)):
    if not verify_password(password):
        html = LOGIN_PAGE.replace("{error}", '<p class="error">Incorrect password</p>')
        return HTMLResponse(html, status_code=401)
    token = _make_token(int(time.time()))
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        TOKEN_COOKIE, token, max_age=TOKEN_MAX_AGE,
        httponly=True, samesite="lax", secure=False,
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(TOKEN_COOKIE)
    return response


@app.get("/")
async def root():
    index = STATIC_DIR / "index.html"
    if not index.is_file():
        return JSONResponse({"message": "Frontend not built yet"}, status_code=404)
    return FileResponse(index)
