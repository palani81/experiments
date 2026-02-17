"""SQLite database with FTS5 for full-text search."""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from .config import settings

_local = threading.local()

SCHEMA = """
-- Core file index
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    parent_path TEXT,
    is_directory INTEGER DEFAULT 0,
    size INTEGER DEFAULT 0,
    mime_type TEXT,
    file_hash TEXT,
    created_at TEXT,
    modified_at TEXT,
    indexed_at TEXT,
    full_text TEXT
);

CREATE INDEX IF NOT EXISTS idx_files_parent ON files(parent_path);
CREATE INDEX IF NOT EXISTS idx_files_mime ON files(mime_type);
CREATE INDEX IF NOT EXISTS idx_files_size ON files(size DESC);
CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified_at DESC);
CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash);
CREATE INDEX IF NOT EXISTS idx_files_is_dir ON files(is_directory);
CREATE INDEX IF NOT EXISTS idx_files_name ON files(name);

-- Full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
    name,
    full_text,
    path,
    content='files',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
    INSERT INTO files_fts(rowid, name, full_text, path)
    VALUES (new.id, new.name, new.full_text, new.path);
END;

CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, name, full_text, path)
    VALUES ('delete', old.id, old.name, old.full_text, old.path);
END;

CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
    INSERT INTO files_fts(files_fts, rowid, name, full_text, path)
    VALUES ('delete', old.id, old.name, old.full_text, old.path);
    INSERT INTO files_fts(rowid, name, full_text, path)
    VALUES (new.id, new.name, new.full_text, new.path);
END;

-- File metadata (flexible JSON-like storage)
CREATE TABLE IF NOT EXISTS file_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL UNIQUE,
    metadata TEXT,  -- JSON string
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Tags for categorization
CREATE TABLE IF NOT EXISTS file_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    tag TEXT NOT NULL,
    tag_type TEXT DEFAULT 'rule',  -- 'rule' or 'user'
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE(file_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_tags_file ON file_tags(file_id);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON file_tags(tag);

-- Scan log
CREATE TABLE IF NOT EXISTS scan_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT DEFAULT 'running',  -- running, completed, failed
    files_scanned INTEGER DEFAULT 0,
    files_added INTEGER DEFAULT 0,
    files_updated INTEGER DEFAULT 0,
    files_removed INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    error_log TEXT
);
"""


_init_done = set()  # Track which DB files have been initialized


def get_connection() -> sqlite3.Connection:
    """Get a thread-local database connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        db_path = Path(settings.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _local.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA synchronous=NORMAL")
        _local.conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
        _local.conn.execute("PRAGMA foreign_keys=ON")
        # Auto-init schema on first connection to this DB
        db_str = str(db_path)
        if db_str not in _init_done:
            _local.conn.executescript(SCHEMA)
            _init_done.add(db_str)
    return _local.conn


@contextmanager
def get_db():
    """Context manager for database operations."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db():
    """Initialize database schema."""
    with get_db() as conn:
        conn.executescript(SCHEMA)


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a query and return results as list of dicts."""
    conn = get_connection()
    cursor = conn.execute(sql, params)
    columns = [d[0] for d in cursor.description] if cursor.description else []
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def execute(sql: str, params: tuple = ()) -> int:
    """Execute a statement and return lastrowid."""
    conn = get_connection()
    cursor = conn.execute(sql, params)
    conn.commit()
    return cursor.lastrowid


def executemany(sql: str, params_list: list[tuple]):
    """Execute a statement with many parameter sets."""
    conn = get_connection()
    conn.executemany(sql, params_list)
    conn.commit()
