"""Dashboard and insights endpoints."""

from fastapi import APIRouter, Depends

from ..database import query
from ..models import DashboardData
from ..security import require_auth

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard(_auth=Depends(require_auth)):
    """Get all dashboard data in a single request."""

    # Total stats
    stats = query("""
        SELECT
            COALESCE(SUM(CASE WHEN is_directory = 0 THEN size ELSE 0 END), 0) as total_size,
            COALESCE(SUM(CASE WHEN is_directory = 0 THEN 1 ELSE 0 END), 0) as total_files,
            COALESCE(SUM(CASE WHEN is_directory = 1 THEN 1 ELSE 0 END), 0) as total_directories
        FROM files
    """)
    s = stats[0] if stats else {"total_size": 0, "total_files": 0, "total_directories": 0}

    # Unique hashes and duplicate info
    dup_stats = query("""
        SELECT
            COUNT(DISTINCT file_hash) as unique_hashes,
            (SELECT COUNT(*) FROM (
                SELECT file_hash FROM files
                WHERE file_hash IS NOT NULL AND is_directory = 0
                GROUP BY file_hash HAVING COUNT(*) > 1
            )) as duplicate_groups,
            COALESCE((SELECT SUM(wasted) FROM (
                SELECT (COUNT(*) - 1) * size as wasted
                FROM files
                WHERE file_hash IS NOT NULL AND is_directory = 0
                GROUP BY file_hash HAVING COUNT(*) > 1
            )), 0) as duplicate_wasted_bytes
        FROM files WHERE file_hash IS NOT NULL AND is_directory = 0
    """)
    d = dup_stats[0] if dup_stats else {}

    # By MIME type (top 20)
    by_type = query("""
        SELECT
            CASE
                WHEN mime_type LIKE 'video/%' THEN 'Video'
                WHEN mime_type LIKE 'audio/%' THEN 'Audio'
                WHEN mime_type LIKE 'image/%' THEN 'Image'
                WHEN mime_type LIKE 'text/%' THEN 'Text'
                WHEN mime_type IN ('application/pdf') THEN 'PDF'
                WHEN mime_type LIKE '%document%' OR mime_type LIKE '%word%' THEN 'Document'
                WHEN mime_type LIKE '%spreadsheet%' OR mime_type LIKE '%excel%' THEN 'Spreadsheet'
                WHEN mime_type LIKE '%presentation%' OR mime_type LIKE '%powerpoint%' THEN 'Presentation'
                WHEN mime_type LIKE '%zip%' OR mime_type LIKE '%compressed%' OR mime_type LIKE '%archive%' THEN 'Archive'
                WHEN mime_type = 'inode/directory' THEN 'Directory'
                ELSE 'Other'
            END as category,
            COUNT(*) as count,
            SUM(size) as total_size
        FROM files
        WHERE is_directory = 0
        GROUP BY category
        ORDER BY total_size DESC
        LIMIT 20
    """)

    # Largest files (top 20)
    largest = query("""
        SELECT id, name, path, size, mime_type, modified_at
        FROM files WHERE is_directory = 0
        ORDER BY size DESC LIMIT 20
    """)

    # Recent files (top 20)
    recent = query("""
        SELECT id, name, path, size, mime_type, modified_at
        FROM files WHERE is_directory = 0
        ORDER BY modified_at DESC LIMIT 20
    """)

    # Duplicate groups (top 20 by wasted space)
    duplicates = query("""
        SELECT
            file_hash,
            COUNT(*) as count,
            size,
            (COUNT(*) - 1) * size as wasted_bytes,
            GROUP_CONCAT(name, ' | ') as names,
            GROUP_CONCAT(path, ' | ') as paths
        FROM files
        WHERE file_hash IS NOT NULL AND is_directory = 0
        GROUP BY file_hash
        HAVING COUNT(*) > 1
        ORDER BY wasted_bytes DESC
        LIMIT 20
    """)

    # Tag distribution
    tag_counts = query("""
        SELECT tag, COUNT(*) as count
        FROM file_tags
        GROUP BY tag
        ORDER BY count DESC
        LIMIT 30
    """)

    # Size by extension (top 20)
    size_by_ext = query("""
        SELECT
            LOWER(SUBSTR(name, INSTR(name, '.'))) as extension,
            COUNT(*) as count,
            SUM(size) as total_size
        FROM files
        WHERE is_directory = 0 AND INSTR(name, '.') > 0
        GROUP BY extension
        ORDER BY total_size DESC
        LIMIT 20
    """)

    # Files by month (last 24 months)
    by_month = query("""
        SELECT
            SUBSTR(modified_at, 1, 7) as month,
            COUNT(*) as count,
            SUM(size) as total_size
        FROM files
        WHERE is_directory = 0 AND modified_at IS NOT NULL
        GROUP BY month
        ORDER BY month DESC
        LIMIT 24
    """)

    return DashboardData(
        total_size=s["total_size"],
        total_files=s["total_files"],
        total_directories=s["total_directories"],
        unique_hashes=d.get("unique_hashes", 0),
        duplicate_groups=d.get("duplicate_groups", 0),
        duplicate_wasted_bytes=d.get("duplicate_wasted_bytes", 0),
        by_type=[dict(r) for r in by_type],
        largest_files=[dict(r) for r in largest],
        recent_files=[dict(r) for r in recent],
        duplicates=[dict(r) for r in duplicates],
        tag_counts=[dict(r) for r in tag_counts],
        size_by_extension=[dict(r) for r in size_by_ext],
        files_by_month=[dict(r) for r in by_month],
    )


@router.get("/insights/storage-treemap")
async def storage_treemap(_auth=Depends(require_auth)):
    """Get storage usage as a treemap structure (top-level directories)."""
    rows = query("""
        SELECT
            f.parent_path as path,
            SUM(f.size) as total_size,
            COUNT(*) as file_count
        FROM files f
        WHERE f.is_directory = 0
        GROUP BY f.parent_path
        ORDER BY total_size DESC
        LIMIT 50
    """)
    return [dict(r) for r in rows]
