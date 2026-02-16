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

    # ─── Extended Insights ─────────────────────────────────

    # Oldest files (top 15)
    oldest = query("""
        SELECT id, name, path, size, mime_type, modified_at
        FROM files WHERE is_directory = 0 AND modified_at IS NOT NULL
        ORDER BY modified_at ASC LIMIT 15
    """)

    # Average file size
    avg_row = query("""
        SELECT COALESCE(AVG(size), 0) as avg_size FROM files WHERE is_directory = 0
    """)
    avg_size = int(avg_row[0]["avg_size"]) if avg_row else 0

    # Median file size
    median_row = query("""
        SELECT size FROM files WHERE is_directory = 0
        ORDER BY size LIMIT 1
        OFFSET (SELECT COUNT(*) / 2 FROM files WHERE is_directory = 0)
    """)
    median_size = median_row[0]["size"] if median_row else 0

    # Size by source (top-level folder = source label)
    size_by_source = query("""
        SELECT
            CASE
                WHEN INSTR(SUBSTR(path, 2), '/') > 0
                THEN SUBSTR(path, 2, INSTR(SUBSTR(path, 2), '/') - 1)
                ELSE SUBSTR(path, 2)
            END as source,
            COUNT(*) as count,
            SUM(size) as total_size
        FROM files
        WHERE is_directory = 0 AND path LIKE '/%'
        GROUP BY source
        ORDER BY total_size DESC
    """)

    # File age buckets
    file_age = query("""
        SELECT
            CASE
                WHEN modified_at >= date('now', '-30 days') THEN 'Last 30 days'
                WHEN modified_at >= date('now', '-90 days') THEN '1-3 months'
                WHEN modified_at >= date('now', '-1 year') THEN '3-12 months'
                WHEN modified_at >= date('now', '-3 years') THEN '1-3 years'
                WHEN modified_at >= date('now', '-5 years') THEN '3-5 years'
                ELSE '5+ years'
            END as age_bucket,
            COUNT(*) as count,
            SUM(size) as total_size
        FROM files
        WHERE is_directory = 0 AND modified_at IS NOT NULL
        GROUP BY age_bucket
        ORDER BY MIN(modified_at) DESC
    """)

    # Top extensions by count
    ext_counts = query("""
        SELECT
            LOWER(SUBSTR(name, INSTR(name, '.'))) as extension,
            COUNT(*) as count
        FROM files
        WHERE is_directory = 0 AND INSTR(name, '.') > 0
        GROUP BY extension
        ORDER BY count DESC
        LIMIT 15
    """)

    # Empty files
    empty = query("SELECT COUNT(*) as cnt FROM files WHERE is_directory = 0 AND size = 0")
    empty_count = empty[0]["cnt"] if empty else 0

    # Deepest nested paths
    deep_paths = query("""
        SELECT path, LENGTH(path) - LENGTH(REPLACE(path, '/', '')) as depth, name, size
        FROM files WHERE is_directory = 0
        ORDER BY depth DESC
        LIMIT 10
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
        oldest_files=[dict(r) for r in oldest],
        avg_file_size=avg_size,
        median_file_size=median_size,
        size_by_source=[dict(r) for r in size_by_source],
        file_age_buckets=[dict(r) for r in file_age],
        extension_counts=[dict(r) for r in ext_counts],
        empty_files=empty_count,
        deep_paths=[dict(r) for r in deep_paths],
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
