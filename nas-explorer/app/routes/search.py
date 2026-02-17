"""Full-text search endpoint."""
from __future__ import annotations

import time
import json
from fastapi import APIRouter, Depends

from ..database import query
from ..models import SearchRequest, SearchResponse, FileItem
from ..security import require_auth

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(
    req: SearchRequest,
    _auth=Depends(require_auth),
):
    """
    Full-text search across file names and extracted content.
    Uses SQLite FTS5 for fast, ranked results.
    """
    start = time.time()

    # Build FTS query — escape special characters
    fts_query = req.query.replace('"', '""')

    # Support simple AND/OR by splitting words
    words = fts_query.split()
    if len(words) > 1:
        # Default to AND matching
        fts_terms = " AND ".join(f'"{w}"' for w in words)
    else:
        # Single word — use prefix match
        fts_terms = f'"{fts_query}"*'

    # Base FTS query
    sql = """
        SELECT f.*, fts.rank
        FROM files_fts fts
        JOIN files f ON f.id = fts.rowid
        WHERE files_fts MATCH ?
    """
    params = [fts_terms]

    # Apply filters
    if req.mime_type:
        sql += " AND f.mime_type LIKE ?"
        params.append(f"{req.mime_type}%")

    if req.min_size is not None:
        sql += " AND f.size >= ?"
        params.append(req.min_size)

    if req.max_size is not None:
        sql += " AND f.size <= ?"
        params.append(req.max_size)

    if req.tags:
        for tag in req.tags:
            sql += " AND f.id IN (SELECT file_id FROM file_tags WHERE tag = ?)"
            params.append(tag)

    # Sorting
    if req.sort_by == "relevance":
        sql += " ORDER BY fts.rank"
    elif req.sort_by == "size":
        sql += " ORDER BY f.size DESC"
    elif req.sort_by == "modified_at":
        sql += " ORDER BY f.modified_at DESC"
    elif req.sort_by == "name":
        sql += " ORDER BY f.name ASC"
    else:
        sql += " ORDER BY fts.rank"

    # Count total (without pagination)
    count_sql = f"""
        SELECT COUNT(*) as cnt
        FROM files_fts fts
        JOIN files f ON f.id = fts.rowid
        WHERE files_fts MATCH ?
    """
    count_params = [fts_terms]
    if req.mime_type:
        count_sql += " AND f.mime_type LIKE ?"
        count_params.append(f"{req.mime_type}%")
    if req.min_size is not None:
        count_sql += " AND f.size >= ?"
        count_params.append(req.min_size)
    if req.max_size is not None:
        count_sql += " AND f.size <= ?"
        count_params.append(req.max_size)
    if req.tags:
        for tag in req.tags:
            count_sql += " AND f.id IN (SELECT file_id FROM file_tags WHERE tag = ?)"
            count_params.append(tag)

    total_rows = query(count_sql, tuple(count_params))
    total = total_rows[0]["cnt"] if total_rows else 0

    # Apply pagination
    sql += " LIMIT ? OFFSET ?"
    params.extend([req.limit, req.skip])

    rows = query(sql, tuple(params))

    # Build response
    items = []
    for row in rows:
        tags_rows = query("SELECT tag FROM file_tags WHERE file_id = ?", (row["id"],))
        tags = [t["tag"] for t in tags_rows]
        items.append(FileItem.from_row(row, tags))

    elapsed = (time.time() - start) * 1000

    return SearchResponse(
        items=items,
        total=total,
        search_time_ms=round(elapsed, 2),
    )


@router.get("/search/suggest")
async def search_suggest(
    q: str,
    limit: int = 10,
    _auth=Depends(require_auth),
):
    """Quick search suggestions (file names matching prefix)."""
    rows = query(
        "SELECT id, name, path, mime_type FROM files WHERE name LIKE ? AND is_directory = 0 LIMIT ?",
        (f"%{q}%", limit),
    )
    return [
        {"id": r["id"], "name": r["name"], "path": r["path"], "mime_type": r["mime_type"]}
        for r in rows
    ]
