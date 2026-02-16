"""Background file scanner/indexer with incremental support.

Scans NAS shares over SMB (no OS mount needed).
Supports multiple sources/shares.
"""

import os
import hashlib
import threading
import logging
import json
import mimetypes
from datetime import datetime, timezone

from .config import settings
from .database import get_connection, query, execute
from .smb_fs import (
    SMBSource, walk, stat, open_file, download_to_temp, cleanup_temp,
    smb_to_relative, get_mime_type, register_source,
)
from .nas_manager import get_sources
from .extractor import extract_text, extract_metadata
from .categorizer import categorize_file

logger = logging.getLogger("nas_explorer.scanner")

# Global scan state
_scan_state = {
    "running": False,
    "scan_id": None,
    "files_scanned": 0,
    "files_added": 0,
    "files_updated": 0,
    "files_removed": 0,
    "errors": 0,
    "total_estimate": 0,
    "current_source": "",
    "started_at": None,
    "error_log": [],
}
_scan_lock = threading.Lock()
_cancel_event = threading.Event()  # Set this to signal scan cancellation


def get_scan_state() -> dict:
    """Get current scan state (thread-safe read)."""
    with _scan_lock:
        return dict(_scan_state)


def stop_scan() -> dict:
    """Signal the running scan to stop. Returns immediately; scan stops at next check."""
    with _scan_lock:
        if not _scan_state["running"]:
            return {"success": True, "message": "No scan running"}
    _cancel_event.set()
    return {"success": True, "message": "Scan cancel signal sent"}


def _is_cancelled() -> bool:
    """Check if cancellation has been requested."""
    return _cancel_event.is_set()


def compute_file_hash_smb(smb_path: str, file_size: int) -> str | None:
    """
    Compute a fast hash using first + last N KB of the file over SMB.
    """
    try:
        sample_size = settings.hash_sample_size_kb * 1024
        hasher = hashlib.sha256()
        hasher.update(str(file_size).encode())

        with open_file(smb_path) as f:
            # Read first chunk
            hasher.update(f.read(sample_size))

            # Read last chunk if file is big enough
            if file_size > sample_size * 2:
                f.seek(-sample_size, 2)
                hasher.update(f.read(sample_size))

        return hasher.hexdigest()[:16]
    except Exception as e:
        logger.warning(f"Hash failed for {smb_path}: {e}")
        return None


def _scan_source(source: SMBSource, conn, scan_id: int, full_scan: bool):
    """Scan a single SMB source."""
    global _scan_state

    with _scan_lock:
        _scan_state["current_source"] = source.label or source.share

    # Get existing indexed files for incremental scanning
    label = source.label or source.share
    existing = {}
    if not full_scan:
        rows = conn.execute(
            "SELECT path, modified_at FROM files WHERE path LIKE ?",
            (f"/{label}/%",)
        ).fetchall()
        existing = {row[0]: row[1] for row in rows}

    seen_paths = set()
    batch = []
    batch_tags = []
    batch_meta = []

    try:
        register_source(source)
    except Exception as e:
        logger.error(f"Failed to register source {source.source_id}: {e}")
        with _scan_lock:
            _scan_state["errors"] += 1
            _scan_state["error_log"].append(f"Source {source.source_id}: {e}")
        return

    for dirpath, dirnames, filenames in walk(source):
        # Check for cancellation between directories
        if _is_cancelled():
            logger.info(f"Scan cancelled during source: {source.source_id}")
            break

        # Convert SMB path to relative path for DB
        rel_dir = smb_to_relative(dirpath, source)
        parent_dir = "/".join(rel_dir.rsplit("/", 1)[:-1]) or f"/{label}"
        if rel_dir == f"/{label}":
            parent_dir = None

        seen_paths.add(rel_dir)

        # Get directory mtime
        dir_stat = stat(dirpath)
        dir_mtime = None
        if dir_stat:
            dir_mtime = datetime.fromtimestamp(dir_stat.mtime, tz=timezone.utc).isoformat()

        batch.append((
            rel_dir,
            dirpath.replace("\\", "/").split("/")[-1] or label,
            parent_dir,
            1,  # is_directory
            0,  # size
            "inode/directory",
            None,  # hash
            dir_mtime,
            dir_mtime,
            datetime.now(timezone.utc).isoformat(),
            None,  # full_text
            source.source_id,  # source_id for tracking
        ))

        for filename in filenames:
            smb_filepath = dirpath.rstrip("\\") + "\\" + filename
            rel_path = smb_to_relative(smb_filepath, source)
            seen_paths.add(rel_path)

            with _scan_lock:
                _scan_state["files_scanned"] += 1

            try:
                file_stat = stat(smb_filepath)
                if not file_stat:
                    continue

                mtime = datetime.fromtimestamp(file_stat.mtime, tz=timezone.utc).isoformat()
                ctime = datetime.fromtimestamp(file_stat.ctime, tz=timezone.utc).isoformat()
                size = file_stat.size

                # Skip if not modified (incremental scan)
                if not full_scan and rel_path in existing:
                    if existing[rel_path] == mtime:
                        continue

                # Detect MIME type (by extension — fast, no download)
                mime = get_mime_type(smb_filepath)

                # Compute hash for dedup
                file_hash = compute_file_hash_smb(smb_filepath, size)

                # Extract text content (for searchable files)
                full_text = None
                if size <= settings.max_text_extract_mb * 1024 * 1024:
                    try:
                        full_text = _extract_text_smb(smb_filepath, mime)
                        if full_text:
                            max_store = settings.max_text_store_kb * 1024
                            full_text = full_text[:max_store]
                    except Exception as e:
                        logger.debug(f"Text extraction failed for {rel_path}: {e}")

                batch.append((
                    rel_path,
                    filename,
                    rel_dir,
                    0,  # is_directory
                    size,
                    mime,
                    file_hash,
                    ctime,
                    mtime,
                    datetime.now(timezone.utc).isoformat(),
                    full_text,
                    source.source_id,
                ))

                # Extract metadata (needs temp download for media files)
                try:
                    meta = _extract_metadata_smb(smb_filepath, mime, size)
                    if meta:
                        batch_meta.append((rel_path, json.dumps(meta)))
                except Exception as e:
                    logger.debug(f"Metadata extraction failed for {rel_path}: {e}")

                # Auto-categorize
                try:
                    tags = categorize_file(filename, mime, size, mtime)
                    for tag in tags:
                        batch_tags.append((rel_path, tag))
                except Exception as e:
                    logger.debug(f"Categorization failed for {rel_path}: {e}")

                with _scan_lock:
                    if rel_path in existing:
                        _scan_state["files_updated"] += 1
                    else:
                        _scan_state["files_added"] += 1

            except Exception as e:
                with _scan_lock:
                    _scan_state["errors"] += 1
                    _scan_state["error_log"].append(f"{rel_path}: {str(e)}")
                logger.warning(f"Error scanning {smb_filepath}: {e}")
                continue

            # Flush batch
            if len(batch) >= settings.scan_batch_size:
                _flush_batch(conn, batch, batch_tags, batch_meta)
                batch.clear()
                batch_tags.clear()
                batch_meta.clear()

    # Final flush
    if batch:
        _flush_batch(conn, batch, batch_tags, batch_meta)

    # Remove files no longer on NAS (for this source only)
    if full_scan:
        all_indexed = conn.execute(
            "SELECT path FROM files WHERE path LIKE ?",
            (f"/{label}/%",)
        ).fetchall()
        removed = 0
        for row in all_indexed:
            if row[0] not in seen_paths:
                conn.execute("DELETE FROM files WHERE path = ?", (row[0],))
                removed += 1
        # Also check the root entry
        root_entry = f"/{label}"
        if root_entry not in seen_paths:
            conn.execute("DELETE FROM files WHERE path = ?", (root_entry,))

        if removed:
            conn.commit()
            with _scan_lock:
                _scan_state["files_removed"] += removed


def _extract_text_smb(smb_path: str, mime: str) -> str | None:
    """Extract text from a file accessed over SMB."""
    # For text files, read directly
    if mime and (mime.startswith("text/") or mime in (
        "application/json", "application/xml", "application/javascript",
        "application/x-yaml", "application/x-python",
    )):
        try:
            from .smb_fs import read_bytes
            data = read_bytes(smb_path, max_bytes=512 * 1024)
            return data.decode("utf-8", errors="replace")
        except Exception:
            return None

    # For binary formats (PDF, DOCX, XLSX), download to temp
    ext = smb_path.replace("\\", "/").split("/")[-1].rsplit(".", 1)[-1].lower() if "." in smb_path else ""
    needs_download = mime in (
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ) or ext in ("srt", "vtt", "ass", "ssa", "sub")

    if needs_download:
        temp_path = None
        try:
            temp_path = download_to_temp(smb_path)
            return extract_text(temp_path, mime)
        except Exception as e:
            logger.debug(f"Text extraction via temp failed for {smb_path}: {e}")
            return None
        finally:
            if temp_path:
                cleanup_temp(temp_path)

    return None


def _extract_metadata_smb(smb_path: str, mime: str, size: int) -> dict | None:
    """Extract metadata from a file accessed over SMB."""
    # Only extract for media files (worth the download cost)
    if not mime:
        return None

    is_media = (
        mime.startswith("image/") or
        mime.startswith("video/") or
        mime.startswith("audio/")
    )

    if not is_media:
        return None

    # Skip very large files for metadata extraction
    if size > 500 * 1024 * 1024:  # 500MB
        return None

    temp_path = None
    try:
        # For images, download fully. For video, ffprobe can work with SMB?
        # No — ffprobe needs local path. Download to temp.
        temp_path = download_to_temp(smb_path)
        return extract_metadata(temp_path, mime)
    except Exception as e:
        logger.debug(f"Metadata extraction via temp failed for {smb_path}: {e}")
        return None
    finally:
        if temp_path:
            cleanup_temp(temp_path)


def _scan_all_sources(scan_id: int, full_scan: bool):
    """Walk all configured SMB sources and index files. Runs in background thread."""
    global _scan_state
    conn = get_connection()

    try:
        sources = get_sources()
        if not sources:
            logger.warning("No SMB sources configured")
            with _scan_lock:
                _scan_state["running"] = False
            return

        for source in sources:
            if _is_cancelled():
                logger.info("Scan cancelled before starting next source")
                break
            logger.info(f"Scanning source: {source.source_id}")
            _scan_source(source, conn, scan_id, full_scan)

        # Mark scan complete (or cancelled)
        final_status = "cancelled" if _is_cancelled() else "completed"
        conn.execute(
            "UPDATE scan_log SET completed_at=?, status=?, "
            "files_scanned=?, files_added=?, files_updated=?, files_removed=?, errors=?, error_log=? "
            "WHERE id=?",
            (
                datetime.now(timezone.utc).isoformat(),
                final_status,
                _scan_state["files_scanned"],
                _scan_state["files_added"],
                _scan_state["files_updated"],
                _scan_state["files_removed"],
                _scan_state["errors"],
                json.dumps(_scan_state["error_log"][-100:]),
                scan_id,
            )
        )
        conn.commit()

    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        conn.execute(
            "UPDATE scan_log SET completed_at=?, status='failed', error_log=? WHERE id=?",
            (datetime.now(timezone.utc).isoformat(), str(e), scan_id)
        )
        conn.commit()

    finally:
        with _scan_lock:
            _scan_state["running"] = False


def _flush_batch(conn, batch, batch_tags, batch_meta):
    """Insert a batch of files, tags, and metadata."""
    # Note: source_id is extra column — we ignore it in the INSERT (not in schema)
    conn.executemany(
        """INSERT OR REPLACE INTO files
           (path, name, parent_path, is_directory, size, mime_type, file_hash,
            created_at, modified_at, indexed_at, full_text)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(row[0], row[1], row[2], row[3], row[4], row[5], row[6],
          row[7], row[8], row[9], row[10]) for row in batch]
    )
    conn.commit()

    # Insert tags
    for rel_path, tag in batch_tags:
        try:
            row = conn.execute("SELECT id FROM files WHERE path = ?", (rel_path,)).fetchone()
            if row:
                conn.execute(
                    "INSERT OR IGNORE INTO file_tags (file_id, tag) VALUES (?, ?)",
                    (row[0], tag)
                )
        except Exception:
            pass

    # Insert metadata
    for rel_path, meta_json in batch_meta:
        try:
            row = conn.execute("SELECT id FROM files WHERE path = ?", (rel_path,)).fetchone()
            if row:
                conn.execute(
                    "INSERT OR REPLACE INTO file_metadata (file_id, metadata) VALUES (?, ?)",
                    (row[0], meta_json)
                )
        except Exception:
            pass

    conn.commit()


def start_scan(full_scan: bool = False) -> dict:
    """Start a background scan. Returns scan state."""
    global _scan_state

    with _scan_lock:
        if _scan_state["running"]:
            return {"error": "Scan already in progress", **_scan_state}

        _cancel_event.clear()  # Reset cancellation flag for new scan
        _scan_state = {
            "running": True,
            "scan_id": None,
            "files_scanned": 0,
            "files_added": 0,
            "files_updated": 0,
            "files_removed": 0,
            "errors": 0,
            "total_estimate": 0,
            "current_source": "",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "error_log": [],
        }

    # Check we have sources configured
    sources = get_sources()
    if not sources:
        with _scan_lock:
            _scan_state["running"] = False
        return {"error": "No NAS sources configured. Use the setup wizard to add a source."}

    # Create scan log entry
    scan_id = execute(
        "INSERT INTO scan_log (started_at, status) VALUES (?, 'running')",
        (datetime.now(timezone.utc).isoformat(),)
    )
    with _scan_lock:
        _scan_state["scan_id"] = scan_id

    # Launch background thread
    thread = threading.Thread(
        target=_scan_all_sources,
        args=(scan_id, full_scan),
        daemon=True,
        name="nas-scanner"
    )
    thread.start()

    return get_scan_state()
