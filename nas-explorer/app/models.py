"""Pydantic models for request/response schemas."""

from pydantic import BaseModel
from typing import Optional


class FileItem(BaseModel):
    id: int
    path: str
    name: str
    parent_path: Optional[str] = None
    is_directory: bool = False
    size: int = 0
    mime_type: Optional[str] = None
    file_hash: Optional[str] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    indexed_at: Optional[str] = None
    tags: list[str] = []
    metadata: Optional[dict] = None
    preview_url: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict, tags: list[str] | None = None) -> "FileItem":
        preview_url = None
        mime = row.get("mime_type") or ""
        if mime.startswith(("image/", "video/")) or mime == "application/pdf":
            preview_url = f"/api/preview/{row['id']}?size=medium"
        return cls(
            id=row["id"],
            path=row["path"],
            name=row["name"],
            parent_path=row.get("parent_path"),
            is_directory=bool(row.get("is_directory", 0)),
            size=row.get("size", 0),
            mime_type=row.get("mime_type"),
            file_hash=row.get("file_hash"),
            created_at=row.get("created_at"),
            modified_at=row.get("modified_at"),
            indexed_at=row.get("indexed_at"),
            tags=tags or [],
            preview_url=preview_url,
        )


class FileListResponse(BaseModel):
    items: list[FileItem]
    total: int
    has_more: bool


class SearchRequest(BaseModel):
    query: str
    mime_type: Optional[str] = None
    tags: Optional[list[str]] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    sort_by: str = "relevance"
    skip: int = 0
    limit: int = 50


class SearchResponse(BaseModel):
    items: list[FileItem]
    total: int
    search_time_ms: float


class FolderNode(BaseModel):
    id: int
    name: str
    path: str
    children: list["FolderNode"] = []
    file_count: int = 0


class DashboardData(BaseModel):
    total_size: int = 0
    total_files: int = 0
    total_directories: int = 0
    unique_hashes: int = 0
    duplicate_groups: int = 0
    duplicate_wasted_bytes: int = 0
    by_type: list[dict] = []
    largest_files: list[dict] = []
    recent_files: list[dict] = []
    duplicates: list[dict] = []
    tag_counts: list[dict] = []
    size_by_extension: list[dict] = []
    files_by_month: list[dict] = []


class ScanStatus(BaseModel):
    scan_id: Optional[int] = None
    status: str = "idle"
    files_scanned: int = 0
    files_added: int = 0
    files_updated: int = 0
    files_removed: int = 0
    errors: int = 0
    current_source: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress_pct: float = 0.0
