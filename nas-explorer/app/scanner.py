"""Background file scanner/indexer with two-phase scanning.

Phase 1 (Fast Index): Walk directories, stat files, insert into DB immediately.
  Files become browsable/searchable by name within seconds.

Phase 2 (Enrichment): Thread pool computes hashes, extracts text content,
  extracts media metadata — all in parallel for much faster throughput.

Scans NAS shares over SMB (no OS mount needed).
Supports multiple sources/shares.
"""
from __future__ import annotations

import os
import hashlib
import threading
import logging
import json
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import settings
from .database import get_connection, query, execute
from .smb_fs import (
    SMBSource, walk, stat, open_file, download_to_temp, cleanup_temp,
    smb_to_relative, relative_to_smb, get_mime_type, register_source,
)
from .nas_manager import get_sources
from .extractor import extract_text, extract_metadata
from .categorizer import categorize_file

logger = logging.getLogger("nas_explorer.scanner")

# Global scan state
_scan_state = {
    "running": False,
    "scan_id": None,
    "phase": "",          # "indexing" | "enriching"
    "files_scanned": 0,
    "files_added": 0,
    "files_updated": 0,
    "files_removed": 0,
    "files_enriched": 0,
    "files_to_enrich": 0,
    "errors": 0,
    "total_estimate": 0,
    "current_source": "",
    "started_at": None,
    "error_log": [],
}
_scan_lock = threading.Lock()
_cancel_event = threading.Event()


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
    return _cancel_event.is_set()


# ─── Phase 1: Fast Index ─────────────────────────────────────────────────

def _phase1_index(source: SMBSource, conn, full_scan: bool) -> set:
    """
    Phase 1: Walk the SMB share and insert file entries into DB.
    Only collects path, name, size, mtime, mime (by extension).
    No hashing, no text extraction, no metadata download.
    Returns set of seen paths for stale-file cleanup.
    """
    label = source.label or source.share

    with _scan_lock:
        _scan_state["current_source"] = label
        _scan_state["phase"] = "indexing"

    # Load existing for incremental skip
    existing = {}
    if not full_scan:
        rows = conn.execute(
            "SELECT path, modified_at FROM files WHERE path LIKE ?",
            (f"/{label}/%",)
        ).fetchall()
        existing = {row[0]: row[1] for row in rows}

    seen_paths = set()
    batch = []

    try:
        register_source(source)
    except Exception as e:
        logger.error(f"Failed to register source {source.source_id}: {e}")
        with _scan_lock:
            _scan_state["errors"] += 1
            _scan_state["error_log"].append(f"Source {source.source_id}: {e}")
        return seen_paths

    for dirpath, dirnames, filenames in walk(source):
        if _is_cancelled():
            logger.info(f"Phase 1 cancelled during source: {source.source_id}")
            break

        rel_dir = smb_to_relative(dirpath, source)
        parent_dir = "/".join(rel_dir.rsplit("/", 1)[:-1]) or f"/{label}"
        if rel_dir == f"/{label}":
            parent_dir = None

        seen_paths.add(rel_dir)

        # Directory entry
        dir_stat = stat(dirpath)
        dir_mtime = None
        if dir_stat:
            dir_mtime = datetime.fromtimestamp(dir_stat.mtime, tz=timezone.utc).isoformat()

        batch.append((
            rel_dir,
            dirpath.replace("\\", "/").split("/")[-1] or label,
            parent_dir,
            1,  # is_directory
            0,
            "inode/directory",
            None,  # hash
            dir_mtime,
            dir_mtime,
            datetime.now(timezone.utc).isoformat(),
            None,  # full_text
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

                # Skip unchanged files in incremental mode
                if not full_scan and rel_path in existing:
                    if existing[rel_path] == mtime:
                        continue

                # MIME by extension (fast, no download)
                mime = get_mime_type(smb_filepath)

                batch.append((
                    rel_path,
                    filename,
                    rel_dir,
                    0,  # is_directory
                    size,
                    mime,
                    None,  # hash — filled in phase 2
                    ctime,
                    mtime,
                    datetime.now(timezone.utc).isoformat(),
                    None,  # full_text — filled in phase 2
                ))

                # Auto-categorize (fast, extension-based)
                try:
                    tags = categorize_file(filename, mime, size, mtime)
                    # We'll insert tags after flushing the file batch
                except Exception:
                    tags = []

                with _scan_lock:
                    if rel_path in existing:
                        _scan_state["files_updated"] += 1
                    else:
                        _scan_state["files_added"] += 1

            except Exception as e:
                with _scan_lock:
                    _scan_state["errors"] += 1
                    _scan_state["error_log"].append(f"{rel_path}: {str(e)}")
                continue

            # Flush batch
            if len(batch) >= settings.scan_batch_size:
                _flush_batch_phase1(conn, batch)
                batch.clear()

    # Final flush
    if batch:
        _flush_batch_phase1(conn, batch)

    # Tag all newly indexed files
    _apply_tags_bulk(conn, label)

    # Remove stale files (full scan only)
    if full_scan and not _is_cancelled():
        _remove_stale(conn, label, seen_paths)

    return seen_paths


def _flush_batch_phase1(conn, batch):
    """Insert file entries (phase 1 — no hash, no full_text yet)."""
    conn.executemany(
        """INSERT OR REPLACE INTO files
           (path, name, parent_path, is_directory, size, mime_type, file_hash,
            created_at, modified_at, indexed_at, full_text)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        batch
    )
    conn.commit()


def _apply_tags_bulk(conn, label):
    """Apply categorization tags to all files for a source."""
    rows = conn.execute(
        "SELECT id, name, mime_type, size, modified_at FROM files WHERE path LIKE ? AND is_directory = 0",
        (f"/{label}/%",)
    ).fetchall()

    for row in rows:
        try:
            tags = categorize_file(row[1], row[2], row[3], row[4])
            for tag in tags:
                conn.execute(
                    "INSERT OR IGNORE INTO file_tags (file_id, tag) VALUES (?, ?)",
                    (row[0], tag)
                )
        except Exception:
            pass
    conn.commit()


def _remove_stale(conn, label, seen_paths):
    """Remove files from DB that are no longer on the NAS."""
    all_indexed = conn.execute(
        "SELECT path FROM files WHERE path LIKE ?",
        (f"/{label}/%",)
    ).fetchall()
    removed = 0
    for row in all_indexed:
        if row[0] not in seen_paths:
            conn.execute("DELETE FROM files WHERE path = ?", (row[0],))
            removed += 1
    root_entry = f"/{label}"
    if root_entry not in seen_paths:
        conn.execute("DELETE FROM files WHERE path = ?", (root_entry,))

    if removed:
        conn.commit()
        with _scan_lock:
            _scan_state["files_removed"] += removed


# ─── Phase 2: Parallel Enrichment ────────────────────────────────────────

def _enrich_file(file_row: dict) -> dict | None:
    """
    Enrich a single file: compute hash, extract text, extract metadata.
    Runs in a thread pool worker. Returns enrichment data or None.
    """
    if _is_cancelled():
        return None

    path = file_row["path"]
    mime = file_row["mime_type"] or ""
    size = file_row["size"]
    file_id = file_row["id"]

    # We need to reconstruct the SMB path from the relative path
    sources = get_sources()
    smb_path = None
    matched_source = None
    for source in sources:
        try:
            sp = relative_to_smb(path, source)
            if sp:
                smb_path = sp
                matched_source = source
                break
        except Exception:
            continue

    if not smb_path:
        return None

    result = {"file_id": file_id, "path": path}

    # 1. Compute hash
    try:
        file_hash = _compute_hash(smb_path, size)
        if file_hash:
            result["file_hash"] = file_hash
    except Exception as e:
        logger.debug(f"Hash failed for {path}: {e}")

    # 2. Extract text content
    if size <= settings.max_text_extract_mb * 1024 * 1024:
        try:
            full_text = _extract_text_smb(smb_path, mime)
            if full_text:
                result["full_text"] = full_text[:settings.max_text_store_kb * 1024]
        except Exception as e:
            logger.debug(f"Text extraction failed for {path}: {e}")

    # 3. Extract metadata (media files only, with size limit)
    if mime and (mime.startswith("image/") or mime.startswith("video/") or mime.startswith("audio/")):
        if size <= 200 * 1024 * 1024:  # 200MB limit for metadata download
            try:
                meta = _extract_metadata_smb(smb_path, mime, size)
                if meta:
                    result["metadata"] = json.dumps(meta)
            except Exception as e:
                logger.debug(f"Metadata extraction failed for {path}: {e}")

    return result


def _compute_hash(smb_path: str, file_size: int) -> str | None:
    """Compute fast hash using first + last N KB over SMB."""
    try:
        sample_size = settings.hash_sample_size_kb * 1024
        hasher = hashlib.sha256()
        hasher.update(str(file_size).encode())

        with open_file(smb_path) as f:
            hasher.update(f.read(sample_size))
            if file_size > sample_size * 2:
                f.seek(-sample_size, 2)
                hasher.update(f.read(sample_size))

        return hasher.hexdigest()[:16]
    except Exception as e:
        logger.warning(f"Hash failed for {smb_path}: {e}")
        return None


def _extract_text_smb(smb_path: str, mime: str) -> str | None:
    """Extract text from a file accessed over SMB."""
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
        except Exception:
            return None
        finally:
            if temp_path:
                cleanup_temp(temp_path)

    return None


def _extract_metadata_smb(smb_path: str, mime: str, size: int) -> dict | None:
    """Extract metadata from a media file accessed over SMB."""
    temp_path = None
    try:
        temp_path = download_to_temp(smb_path)
        return extract_metadata(temp_path, mime)
    except Exception:
        return None
    finally:
        if temp_path:
            cleanup_temp(temp_path)


def _phase2_enrich(conn):
    """
    Phase 2: Enrich files that don't have hashes yet.
    Uses a thread pool for parallel SMB I/O.
    """
    with _scan_lock:
        _scan_state["phase"] = "enriching"

    # Find files needing enrichment (no hash = not yet enriched)
    rows = conn.execute(
        "SELECT id, path, mime_type, size FROM files "
        "WHERE is_directory = 0 AND file_hash IS NULL"
    ).fetchall()

    to_enrich = [{"id": r[0], "path": r[1], "mime_type": r[2], "size": r[3]} for r in rows]

    with _scan_lock:
        _scan_state["files_to_enrich"] = len(to_enrich)

    if not to_enrich:
        return

    logger.info(f"Phase 2: Enriching {len(to_enrich)} files with {settings.enrichment_workers} workers")

    with ThreadPoolExecutor(max_workers=settings.enrichment_workers) as pool:
        futures = {pool.submit(_enrich_file, f): f for f in to_enrich}

        for future in as_completed(futures):
            if _is_cancelled():
                pool.shutdown(wait=False, cancel_futures=True)
                break

            try:
                result = future.result(timeout=120)
                if result and result.get("file_id"):
                    fid = result["file_id"]

                    # Update hash and text
                    if "file_hash" in result or "full_text" in result:
                        conn.execute(
                            "UPDATE files SET file_hash = COALESCE(?, file_hash), "
                            "full_text = COALESCE(?, full_text) WHERE id = ?",
                            (result.get("file_hash"), result.get("full_text"), fid)
                        )

                    # Update metadata
                    if "metadata" in result:
                        conn.execute(
                            "INSERT OR REPLACE INTO file_metadata (file_id, metadata) VALUES (?, ?)",
                            (fid, result["metadata"])
                        )

                    with _scan_lock:
                        _scan_state["files_enriched"] += 1

            except Exception as e:
                with _scan_lock:
                    _scan_state["errors"] += 1
                file_info = futures[future]
                logger.debug(f"Enrichment failed for {file_info.get('path')}: {e}")

            # Commit periodically
            with _scan_lock:
                if _scan_state["files_enriched"] % 50 == 0:
                    conn.commit()

    conn.commit()


# ─── Main Scan Orchestrator ──────────────────────────────────────────────

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

        # Phase 1: Fast index all sources
        for source in sources:
            if _is_cancelled():
                break
            logger.info(f"Phase 1 — Indexing source: {source.source_id}")
            _phase1_index(source, conn, full_scan)

        # Phase 2: Enrich files in parallel
        if not _is_cancelled():
            logger.info("Phase 2 — Enriching files")
            _phase2_enrich(conn)

        # Mark scan complete
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
            _scan_state["phase"] = ""


def start_scan(full_scan: bool = False) -> dict:
    """Start a background scan. Returns scan state."""
    global _scan_state

    with _scan_lock:
        if _scan_state["running"]:
            return {"error": "Scan already in progress", **_scan_state}

        _cancel_event.clear()
        _scan_state = {
            "running": True,
            "scan_id": None,
            "phase": "indexing",
            "files_scanned": 0,
            "files_added": 0,
            "files_updated": 0,
            "files_removed": 0,
            "files_enriched": 0,
            "files_to_enrich": 0,
            "errors": 0,
            "total_estimate": 0,
            "current_source": "",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "error_log": [],
        }

    sources = get_sources()
    if not sources:
        with _scan_lock:
            _scan_state["running"] = False
            _scan_state["phase"] = ""
        return {"error": "No NAS sources configured. Use the setup wizard to add a source."}

    scan_id = execute(
        "INSERT INTO scan_log (started_at, status) VALUES (?, 'running')",
        (datetime.now(timezone.utc).isoformat(),)
    )
    with _scan_lock:
        _scan_state["scan_id"] = scan_id

    thread = threading.Thread(
        target=_scan_all_sources,
        args=(scan_id, full_scan),
        daemon=True,
        name="nas-scanner"
    )
    thread.start()

    return get_scan_state()
