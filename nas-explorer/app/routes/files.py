"""File browsing and listing endpoints."""

import json
from fastapi import APIRouter, Depends, Query
from typing import Optional

from ..database import query
from ..models import FileItem, FileListResponse, FolderNode
from ..security import require_auth

router = APIRouter(prefix="/api", tags=["files"])


@router.get("/files", response_model=FileListResponse)
async def list_files(
    parent_path: Optional[str] = Query(None, description="Parent directory path (/ for root)"),
    sort_by: str = Query("name", description="Sort field: name, size, modified_at, mime_type"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    mime_filter: Optional[str] = Query(None, description="Filter by MIME prefix, e.g. 'video/'"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    _auth=Depends(require_auth),
):
    """List files in a directory with pagination and sorting."""
    # Default to root
    if parent_path is None:
        parent_path = "/"

    # Validate sort field
    valid_sorts = {"name", "size", "modified_at", "mime_type", "created_at"}
    if sort_by not in valid_sorts:
        sort_by = "name"
    order_sql = "DESC" if order.lower() == "desc" else "ASC"

    # Build query
    conditions = ["f.parent_path = ?"]
    params = [parent_path]

    if mime_filter:
        conditions.append("f.mime_type LIKE ?")
        params.append(f"{mime_filter}%")

    if tag:
        conditions.append("f.id IN (SELECT file_id FROM file_tags WHERE tag = ?)")
        params.append(tag)

    where = " AND ".join(conditions)

    # Directories first, then sort
    sql = f"""
        SELECT f.* FROM files f
        WHERE {where}
        ORDER BY f.is_directory DESC, f.{sort_by} {order_sql}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, skip])

    rows = query(sql, tuple(params))

    # Get total count
    count_sql = f"SELECT COUNT(*) as cnt FROM files f WHERE {where}"
    total = query(count_sql, tuple(params[:-2]))[0]["cnt"]

    # Get tags for each file
    items = []
    for row in rows:
        tags = _get_tags(row["id"])
        items.append(FileItem.from_row(row, tags))

    return FileListResponse(
        items=items,
        total=total,
        has_more=(skip + limit) < total,
    )


@router.get("/files/{file_id}", response_model=FileItem)
async def get_file(
    file_id: int,
    _auth=Depends(require_auth),
):
    """Get detailed info about a single file."""
    rows = query("SELECT * FROM files WHERE id = ?", (file_id,))
    if not rows:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")

    row = rows[0]
    tags = _get_tags(file_id)

    # Get metadata
    meta_rows = query("SELECT metadata FROM file_metadata WHERE file_id = ?", (file_id,))
    metadata = None
    if meta_rows and meta_rows[0]["metadata"]:
        try:
            metadata = json.loads(meta_rows[0]["metadata"])
        except (json.JSONDecodeError, TypeError):
            pass

    item = FileItem.from_row(row, tags)
    item.metadata = metadata
    return item


@router.get("/tree", response_model=list[FolderNode])
async def get_folder_tree(
    depth: int = Query(3, ge=1, le=10),
    _auth=Depends(require_auth),
):
    """Get hierarchical folder tree for sidebar navigation."""
    # Get all directories
    dirs = query(
        "SELECT id, name, path, parent_path FROM files WHERE is_directory = 1 ORDER BY path"
    )

    # Build tree
    nodes_by_path = {}
    root_children = []

    for d in dirs:
        node = FolderNode(
            id=d["id"],
            name=d["name"],
            path=d["path"],
            children=[],
        )
        nodes_by_path[d["path"]] = node

    # Get file counts per directory
    counts = query(
        "SELECT parent_path, COUNT(*) as cnt FROM files WHERE is_directory = 0 GROUP BY parent_path"
    )
    count_map = {c["parent_path"]: c["cnt"] for c in counts}

    for d in dirs:
        node = nodes_by_path[d["path"]]
        node.file_count = count_map.get(d["path"], 0)

        parent = d["parent_path"]
        if parent and parent in nodes_by_path:
            # Check depth
            node_depth = d["path"].count("/")
            if node_depth <= depth:
                nodes_by_path[parent].children.append(node)
        elif d["path"] == "/":
            root_children.insert(0, node)
        elif parent is None or parent not in nodes_by_path:
            # Top-level directory
            root_children.append(node)

    return root_children


@router.get("/browse/{path:path}")
async def browse_path(
    path: str,
    sort_by: str = Query("name"),
    order: str = Query("asc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _auth=Depends(require_auth),
):
    """Browse files by path with breadcrumb navigation."""
    # Normalize path
    browse_path = "/" + path.strip("/") if path else "/"

    # Build breadcrumb
    parts = browse_path.strip("/").split("/") if browse_path != "/" else []
    breadcrumb = [{"name": "root", "path": "/"}]
    for i, part in enumerate(parts):
        crumb_path = "/" + "/".join(parts[:i+1])
        breadcrumb.append({"name": part, "path": crumb_path})

    # Get files using the list endpoint logic
    result = await list_files(
        parent_path=browse_path,
        sort_by=sort_by,
        order=order,
        skip=skip,
        limit=limit,
    )

    return {
        "breadcrumb": breadcrumb,
        "current_path": browse_path,
        **result.model_dump(),
    }


def _get_tags(file_id: int) -> list[str]:
    """Get tags for a file."""
    rows = query("SELECT tag FROM file_tags WHERE file_id = ?", (file_id,))
    return [r["tag"] for r in rows]
