"""Shared test fixtures for NAS Explorer tests."""
from __future__ import annotations

import os
import sys
import json
import tempfile
import pytest

# Ensure app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings


@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """Give every test a fresh database + data dir."""
    db_path = str(tmp_path / "test.db")
    settings.database_path = db_path

    # Reset any module-level caches
    from app import database
    database._init_done.clear()
    if hasattr(database._local, "conn"):
        database._local.conn = None

    # Reset crypto cache so it generates a key in tmp_path
    from app import crypto
    crypto._fernet = None

    # Reset nas_manager config file
    from app import nas_manager
    nas_manager.CONFIG_FILE = None

    from app.database import init_db
    init_db()

    yield db_path


@pytest.fixture
def db_conn(isolated_db):
    """Return a live database connection."""
    from app.database import get_connection
    return get_connection()


@pytest.fixture
def client(isolated_db):
    """FastAPI test client with auth overridden."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.routes.dashboard import router as dash_router
    from app.routes.admin import router as admin_router
    from app.security import require_auth

    app = FastAPI()
    app.dependency_overrides[require_auth] = lambda: "test"
    app.include_router(dash_router)
    app.include_router(admin_router)

    return TestClient(app)


@pytest.fixture
def populated_db(db_conn):
    """Insert realistic test data into the database."""
    conn = db_conn
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)

    files = [
        # Videos
        ("/media/movies/inception.mkv", "inception.mkv", "/media/movies", 0, 4_500_000_000, "video/x-matroska", "hash_v1",
         (now - timedelta(days=30)).isoformat(), (now - timedelta(days=30)).isoformat(), now.isoformat(), None),
        ("/media/movies/matrix.mp4", "matrix.mp4", "/media/movies", 0, 2_100_000_000, "video/mp4", "hash_v2",
         (now - timedelta(days=60)).isoformat(), (now - timedelta(days=60)).isoformat(), now.isoformat(), None),
        # Audio
        ("/media/music/song1.mp3", "song1.mp3", "/media/music", 0, 8_000_000, "audio/mpeg", "hash_a1",
         (now - timedelta(days=10)).isoformat(), (now - timedelta(days=10)).isoformat(), now.isoformat(), None),
        ("/media/music/song2.flac", "song2.flac", "/media/music", 0, 40_000_000, "audio/flac", "hash_a2",
         (now - timedelta(days=5)).isoformat(), (now - timedelta(days=5)).isoformat(), now.isoformat(), None),
        # Images
        ("/photos/vacation/beach.jpg", "beach.jpg", "/photos/vacation", 0, 5_000_000, "image/jpeg", "hash_i1",
         (now - timedelta(days=200)).isoformat(), (now - timedelta(days=200)).isoformat(), now.isoformat(), None),
        ("/photos/vacation/sunset.png", "sunset.png", "/photos/vacation", 0, 12_000_000, "image/png", "hash_i2",
         (now - timedelta(days=200)).isoformat(), (now - timedelta(days=200)).isoformat(), now.isoformat(), None),
        # Documents
        ("/docs/report.pdf", "report.pdf", "/docs", 0, 500_000, "application/pdf", "hash_d1",
         (now - timedelta(days=90)).isoformat(), (now - timedelta(days=90)).isoformat(), now.isoformat(), "quarterly report content"),
        ("/docs/notes.txt", "notes.txt", "/docs", 0, 2_000, "text/plain", "hash_d2",
         (now - timedelta(days=15)).isoformat(), (now - timedelta(days=15)).isoformat(), now.isoformat(), "meeting notes"),
        # Old forgotten files
        ("/archive/legacy/old_backup.tar.gz", "old_backup.tar.gz", "/archive/legacy", 0, 900_000_000, "application/gzip", "hash_old1",
         (now - timedelta(days=1200)).isoformat(), (now - timedelta(days=1200)).isoformat(), now.isoformat(), None),
        ("/archive/legacy/ancient.doc", "ancient.doc", "/archive/legacy", 0, 150_000, "application/msword", "hash_old2",
         (now - timedelta(days=1500)).isoformat(), (now - timedelta(days=1500)).isoformat(), now.isoformat(), None),
        # Duplicates (same hash)
        ("/docs/report_copy.pdf", "report_copy.pdf", "/docs/backup", 0, 500_000, "application/pdf", "hash_d1",
         (now - timedelta(days=80)).isoformat(), (now - timedelta(days=80)).isoformat(), now.isoformat(), "quarterly report content"),
        # Name conflict (same name, different folder, different hash)
        ("/photos/screenshots/beach.jpg", "beach.jpg", "/photos/screenshots", 0, 3_000_000, "image/jpeg", "hash_i3",
         (now - timedelta(days=100)).isoformat(), (now - timedelta(days=100)).isoformat(), now.isoformat(), None),
        # Empty file
        ("/docs/empty.txt", "empty.txt", "/docs", 0, 0, "text/plain", "hash_empty",
         (now - timedelta(days=5)).isoformat(), (now - timedelta(days=5)).isoformat(), now.isoformat(), None),
        # Deep path
        ("/data/projects/2024/q1/reports/final/v2/summary.xlsx", "summary.xlsx",
         "/data/projects/2024/q1/reports/final/v2", 0, 75_000, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
         "hash_deep", (now - timedelta(days=45)).isoformat(), (now - timedelta(days=45)).isoformat(), now.isoformat(), None),
        # Directory entries
        ("/media", "media", None, 1, 0, "inode/directory", None, now.isoformat(), now.isoformat(), now.isoformat(), None),
        ("/media/movies", "movies", "/media", 1, 0, "inode/directory", None, now.isoformat(), now.isoformat(), now.isoformat(), None),
        ("/media/music", "music", "/media", 1, 0, "inode/directory", None, now.isoformat(), now.isoformat(), now.isoformat(), None),
        ("/docs", "docs", None, 1, 0, "inode/directory", None, now.isoformat(), now.isoformat(), now.isoformat(), None),
    ]

    conn.executemany(
        """INSERT INTO files (path, name, parent_path, is_directory, size, mime_type, file_hash,
           created_at, modified_at, indexed_at, full_text) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        files
    )

    # Tags
    tags = [
        (1, "media"), (1, "video"), (2, "media"), (2, "video"),
        (3, "media"), (3, "audio"), (3, "music"), (4, "media"), (4, "audio"), (4, "music"),
        (5, "media"), (5, "image"), (5, "photo"), (6, "media"), (6, "image"),
        (7, "document"), (8, "document"), (8, "text"),
        (9, "archive"), (10, "document"), (10, "old"),
        (11, "document"), (12, "media"), (12, "image"), (12, "photo"),
        (13, "document"), (13, "text"), (13, "empty"),
    ]
    conn.executemany("INSERT INTO file_tags (file_id, tag) VALUES (?, ?)", tags)

    # Metadata for video (with duration)
    conn.execute(
        "INSERT INTO file_metadata (file_id, metadata) VALUES (?, ?)",
        (1, json.dumps({"duration": 8880, "resolution": "1920x1080"}))  # 2.47 hours
    )
    conn.execute(
        "INSERT INTO file_metadata (file_id, metadata) VALUES (?, ?)",
        (2, json.dumps({"duration": 8160, "resolution": "1920x1080"}))  # 2.27 hours
    )
    # Metadata for audio
    conn.execute(
        "INSERT INTO file_metadata (file_id, metadata) VALUES (?, ?)",
        (3, json.dumps({"duration": 240, "bitrate": 320}))  # 4 minutes
    )

    conn.commit()
    return conn
