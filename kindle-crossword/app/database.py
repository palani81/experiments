import sqlite3
from contextlib import contextmanager
from typing import Generator

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_filename TEXT NOT NULL,
    original_path TEXT NOT NULL,
    processed_path TEXT,
    pdf_path TEXT,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    processing_options TEXT,
    kindle_email TEXT,
    created_at TEXT NOT NULL,
    processed_at TEXT,
    sent_at TEXT
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT
);
"""


def init_db() -> None:
    with get_db() as db:
        db.executescript(SCHEMA)


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
